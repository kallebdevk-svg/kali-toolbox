"""Etapas do workflow de análise de firmware."""
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

_raiz = Path(__file__).resolve().parents[2]
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

from _lib._core import binario_existe, limitar_linhas, rodar, tentar_com_retry


TIMEOUTS = {
    "identificacao": 60,
    "estrutura": 300,
    "extracao": 900,
    "pos_processamento": 600,
}

PADROES_SENSIVEIS = [
    r"/etc/passwd", r"/etc/shadow", r"id_rsa", r"id_dsa",
    r"\.pem$", r"\.crt$", r"\.key$", r"\.p12$",
    r"authorized_keys", r"\.htpasswd",
]

PADROES_STRINGS_INTERESSANTES = [
    r"https?://[^\s]+",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    r"(?i)(password|passwd|senha|secret|api[_-]?key)\s*[=:]\s*\S+",
    r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
]

# Tipos de estrutura que o binwalk consegue desempacotar. Se nenhuma
# dessas aparece, não vale a pena chamar binwalk -e.
TIPOS_EXTRAIVEIS = [
    "squashfs", "jffs2", "cramfs", "ubifs", "yaffs", "romfs",
    "gzip compressed data", "bzip2 compressed data", "lzma compressed data",
    "lz4 compressed data", "lzop compressed data", "xz compressed data",
    "zlib compressed data", "compress'd data", "zip archive",
    "7-zip archive", "rar archive", "cab archive", "tar archive",
    "linux kernel x86 boot executable", "linux kernel arm boot executable",
    "uimage", "trx firmware", "chk header", "motorola s-record",
    "device tree blob", "android bootimg", "openssl encryption",
    "filesystem", "ext2 filesystem", "ext4 filesystem",
    "iso 9660", "cpio archive", "arc archive", "arj archive",
]


def _estado(nome, estado, resumo, detalhe, duracao, extra=None):
    r = {"nome": nome, "estado": estado, "resumo": resumo,
         "detalhe": detalhe, "duracao": duracao}
    if extra:
        r["extra"] = extra
    return r


def _compilar_padroes_extras(texto):
    if not texto:
        return [], []
    compilados, invalidos = [], []
    for bruto in texto.split(","):
        bruto = bruto.strip()
        if not bruto:
            continue
        try:
            compilados.append((bruto, re.compile(bruto)))
        except re.error as e:
            invalidos.append((bruto, str(e)))
    return compilados, invalidos


def _linha_parece_estrutura(linha):
    """Verifica se uma linha do binwalk descreve algo extraível."""
    minuscula = linha.lower()
    return any(tipo in minuscula for tipo in TIPOS_EXTRAIVEIS)


# --------------------------------------------------------------------------
# Etapa 1 — identificação
# --------------------------------------------------------------------------
def etapa_identificacao(caminho, status, ctx):
    if not binario_existe("file"):
        return _estado("identificacao", "ausente", "file não instalado", "", 0.0)

    inicio = time.monotonic()
    codigo, tipo, _, _ = rodar(["file", "-b", caminho], 20)
    tipo = tipo.strip() if codigo == 0 else "desconhecido"

    hashes = {}
    for algo in ("md5sum", "sha256sum"):
        if not binario_existe(algo):
            continue
        c, s, _, _ = rodar([algo, caminho], 60)
        if c == 0 and s.strip():
            hashes[algo] = s.split()[0]

    try:
        tamanho = os.path.getsize(caminho)
    except OSError:
        tamanho = 0

    duracao = time.monotonic() - inicio
    ctx["tipo"] = tipo
    ctx["tamanho_bytes"] = tamanho
    ctx["hashes"] = hashes

    linhas = [f"Tipo:   {tipo}", f"Tamanho: {tamanho} bytes"]
    for k, v in hashes.items():
        linhas.append(f"{k}: {v}")
    return _estado("identificacao", "ok", tipo, "\n".join(linhas), duracao)


# --------------------------------------------------------------------------
# Etapa 2 — estrutura
# --------------------------------------------------------------------------
def etapa_estrutura(caminho, status, ctx):
    if not binario_existe("binwalk"):
        return _estado("estrutura", "ausente", "binwalk não instalado", "", 0.0)

    def acao():
        c, s, e, estourou = rodar(["binwalk", caminho], TIMEOUTS["estrutura"])
        return (c == 0 and not estourou), s, c, e, estourou

    inicio = time.monotonic()
    sucesso, saida, tentativas = tentar_com_retry("estrutura", acao, status)
    duracao = time.monotonic() - inicio

    if not sucesso:
        return _estado("estrutura", "falhou",
                       "falha ao analisar estrutura", str(saida)[:500], duracao)

    linhas = [l for l in (saida or "").splitlines()
              if l.strip() and not l.startswith(("DECIMAL", "----", "Scan Time",
                                                 "Target File", "MD5 Checksum",
                                                 "Signatures", "WARNING", "NOTE:"))]

    # Separa "estruturas extraíveis" de "achados informativos"
    extraiveis = [l for l in linhas if _linha_parece_estrutura(l)]
    informativos = [l for l in linhas if l not in extraiveis]

    ctx["estrutura_linhas"] = linhas
    ctx["estruturas_extraiveis"] = extraiveis
    ctx["tem_estrutura"] = len(extraiveis) > 0

    if not linhas:
        return _estado("estrutura", "parcial",
                       "nenhuma estrutura identificada",
                       "(o binwalk não reconheceu nada neste arquivo)", duracao)

    if not extraiveis:
        detalhe = (f"Achados informativos (não extraíveis):\n"
                   + "\n".join(f"  {l}" for l in informativos[:30])
                   + "\n\nNenhuma estrutura desempacotável foi encontrada.")
        return _estado("estrutura", "parcial",
                       f"{len(informativos)} achados informativos, "
                       f"nenhuma estrutura extraível",
                       detalhe, duracao)

    detalhe = limitar_linhas(saida, 60, "... (mais entradas no relatório completo)")
    resumo = (f"{len(extraiveis)} extraíveis, "
              f"{len(informativos)} informativos")
    return _estado("estrutura", "ok", resumo, detalhe, duracao)


# --------------------------------------------------------------------------
# Etapa 3 — extração
# --------------------------------------------------------------------------
def etapa_extracao(caminho, status, ctx):
    if not ctx.get("tem_estrutura"):
        motivo = "nenhuma estrutura extraível encontrada"
        return _estado("extracao", "pulada", motivo, "", 0.0)
    if not binario_existe("binwalk"):
        return _estado("extracao", "ausente", "binwalk não instalado", "", 0.0)

    try:
        livre = shutil.disk_usage("/tmp").free
    except OSError:
        livre = 0
    if livre < 200 * 1024 * 1024:
        return _estado("extracao", "pulada",
                       f"espaço em /tmp insuficiente ({livre // (1024*1024)} MB)",
                       "mínimo recomendado: 200 MB livres", 0.0)

    selo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = Path("/tmp") / f"workflow_firmware_{selo}"
    try:
        destino.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return _estado("extracao", "falhou",
                       f"não foi possível criar {destino}", str(e), 0.0)

    ctx["dir_extracao"] = str(destino)

    status("iniciando extracao")
    inicio = time.monotonic()
    c, saida, stderr, estourou = rodar(
        ["binwalk", "-e", "-C", str(destino), caminho], TIMEOUTS["extracao"])
    duracao = time.monotonic() - inicio

    if estourou:
        status("extracao excedeu o tempo limite")
        return _estado("extracao", "falhou",
                       f"tempo limite de {TIMEOUTS['extracao']}s excedido",
                       str(saida)[:500] or "(sem saída)", duracao)

    total_arquivos = sum(1 for _ in destino.rglob("*") if _.is_file())

    if total_arquivos == 0:
        status("extracao concluida sem arquivos gerados")
        ctx["extracao_ok"] = False
        detalhe = (
            f"Diretório: {destino}\n"
            f"O binwalk rodou mas não gerou nenhum arquivo.\n"
            f"Isso pode acontecer quando as estruturas identificadas não "
            f"possuem extrator disponível ou o arquivo de origem não contém "
            f"o payload completo."
        )
        if stderr.strip():
            detalhe += f"\n\nMensagens do binwalk:\n{limitar_linhas(stderr, 20)}"
        return _estado("extracao", "parcial",
                       "nada foi extraído", detalhe, duracao)

    ctx["extracao_ok"] = True
    ctx["total_extraidos"] = total_arquivos
    status(f"extracao concluida: {total_arquivos} arquivos")
    resumo = f"{total_arquivos} arquivos extraídos"
    detalhe = f"Diretório: {destino}\nArquivos: {total_arquivos}"
    return _estado("extracao", "ok", resumo, detalhe, duracao)


# --------------------------------------------------------------------------
# Etapa 4 — pós-processamento
# --------------------------------------------------------------------------
def etapa_pos_processamento(caminho, status, ctx):
    if not ctx.get("extracao_ok"):
        return _estado("pos_processamento", "pulada",
                       "extração não gerou arquivos", "", 0.0)

    destino = Path(ctx["dir_extracao"])
    if not destino.exists():
        return _estado("pos_processamento", "pulada",
                       "diretório de extração sumiu", "", 0.0)

    extras, invalidos = _compilar_padroes_extras(ctx.get("procurar", ""))
    ctx["procurar_invalidos"] = invalidos

    inicio = time.monotonic()
    achados = {
        "sensiveis": [], "urls": set(), "emails": set(),
        "credenciais": set(), "ips": set(), "extras": {},
    }
    for regex_str, _ in extras:
        achados["extras"][regex_str] = []
    binarios_elf = 0

    for arquivo in destino.rglob("*"):
        if not arquivo.is_file():
            continue

        c, tipo, _, _ = rodar(["file", "-b", str(arquivo)], 10)
        eh_elf = c == 0 and "ELF" in tipo
        if eh_elf:
            binarios_elf += 1

        caminho_rel = str(arquivo.relative_to(destino))

        for padrao in PADROES_SENSIVEIS:
            if re.search(padrao, caminho_rel):
                achados["sensiveis"].append(caminho_rel)
                break

        for regex_str, compilado in extras:
            if compilado.search(caminho_rel):
                achados["extras"][regex_str].append(f"[nome] {caminho_rel}")

        if not eh_elf or not binario_existe("strings"):
            continue
        c, saida, _, _ = rodar(["strings", "-n", "6", str(arquivo)], 120)
        if c != 0:
            continue

        for linha in saida.splitlines():
            for padrao in PADROES_STRINGS_INTERESSANTES:
                m = re.search(padrao, linha)
                if not m:
                    continue
                achado = m.group(0)[:200]
                if padrao.startswith("https?"):
                    achados["urls"].add(achado)
                elif "@" in padrao:
                    achados["emails"].add(achado)
                elif "password" in padrao.lower() or "senha" in padrao.lower():
                    achados["credenciais"].add(achado)
                elif padrao.startswith(r"\b(?:"):
                    achados["ips"].add(achado)

            for regex_str, compilado in extras:
                m = compilado.search(linha)
                if m:
                    trecho = m.group(0)[:200]
                    entrada = f"[{caminho_rel}] {trecho}"
                    if entrada not in achados["extras"][regex_str]:
                        achados["extras"][regex_str].append(entrada)

    ctx["achados"] = achados
    ctx["binarios_elf"] = binarios_elf

    duracao = time.monotonic() - inicio
    total_extras = sum(len(v) for v in achados["extras"].values())
    resumo = (f"{binarios_elf} binários ELF, "
              f"{len(achados['sensiveis'])} sensíveis, "
              f"{len(achados['urls'])} URLs"
              + (f", {total_extras} extras" if total_extras else ""))

    detalhe_linhas = [f"Binários ELF encontrados: {binarios_elf}"]
    if achados["sensiveis"]:
        detalhe_linhas.append("\nArquivos sensíveis:")
        detalhe_linhas.extend(f"  {p}" for p in achados["sensiveis"][:20])
    if achados["credenciais"]:
        detalhe_linhas.append("\nCredenciais aparentes:")
        detalhe_linhas.extend(f"  {c}" for c in list(achados["credenciais"])[:10])
    if achados["urls"]:
        detalhe_linhas.append(f"\nURLs encontradas: {len(achados['urls'])}")
        detalhe_linhas.extend(f"  {u}" for u in list(achados["urls"])[:10])
    if achados["emails"]:
        detalhe_linhas.append(f"\nE-mails: {len(achados['emails'])}")
        detalhe_linhas.extend(f"  {e}" for e in list(achados["emails"])[:10])
    for regex_str, ocorrencias in achados["extras"].items():
        if not ocorrencias:
            continue
        detalhe_linhas.append(f"\nPadrão '{regex_str}': {len(ocorrencias)} ocorrências")
        detalhe_linhas.extend(f"  {o}" for o in ocorrencias[:15])
    if invalidos:
        detalhe_linhas.append("\nPadrões inválidos (ignorados):")
        detalhe_linhas.extend(f"  '{p}' — {erro}" for p, erro in invalidos)

    return _estado("pos_processamento", "ok", resumo,
                   "\n".join(detalhe_linhas), duracao)


TODAS_AS_ETAPAS = {
    "identificacao": etapa_identificacao,
    "estrutura": etapa_estrutura,
    "extracao": etapa_extracao,
    "pos_processamento": etapa_pos_processamento,
}

ORDEM_PADRAO = ["identificacao", "estrutura", "extracao", "pos_processamento"]