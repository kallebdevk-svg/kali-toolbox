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
    "pos_processamento": 300,
}

# Padrões para achar coisas interessantes nos arquivos extraídos.
PADROES_SENSIVEIS = [
    r"/etc/passwd",
    r"/etc/shadow",
    r"id_rsa",
    r"id_dsa",
    r"\.pem$",
    r"\.crt$",
    r"\.key$",
    r"\.p12$",
    r"authorized_keys",
    r"\.htpasswd",
]

PADROES_STRINGS_INTERESSANTES = [
    r"https?://[^\s]+",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    r"(?i)(password|passwd|senha|secret|api[_-]?key)\s*[=:]\s*\S+",
    r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
]


def _estado(nome, estado, resumo, detalhe, duracao, extra=None):
    r = {"nome": nome, "estado": estado, "resumo": resumo,
         "detalhe": detalhe, "duracao": duracao}
    if extra:
        r["extra"] = extra
    return r


# --------------------------------------------------------------------------
# Etapa 1 — identificação
# --------------------------------------------------------------------------
def etapa_identificacao(caminho, status, ctx):
    if not binario_existe("file"):
        return _estado("identificacao", "ausente", "file não instalado", "", 0.0)

    inicio = time.monotonic()
    codigo, tipo, erro, _ = rodar(["file", "-b", caminho], 20)
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
# Etapa 2 — estrutura (binwalk sem extrair)
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
    ctx["estrutura_linhas"] = linhas
    ctx["tem_estrutura"] = len(linhas) > 0

    if not linhas:
        return _estado("estrutura", "parcial",
                       "nada extraível", "(sem estruturas identificadas)", duracao)

    detalhe = limitar_linhas(saida, 60, "... (mais entradas no relatório completo)")
    return _estado("estrutura", "ok", f"{len(linhas)} estruturas identificadas",
                   detalhe, duracao)


# --------------------------------------------------------------------------
# Etapa 3 — extração (condicional: só roda se estrutura achou algo)
# --------------------------------------------------------------------------
def etapa_extracao(caminho, status, ctx):
    if not ctx.get("tem_estrutura"):
        return _estado("extracao", "pulada",
                       "estrutura vazia, nada a extrair", "", 0.0)
    if not binario_existe("binwalk"):
        return _estado("extracao", "ausente", "binwalk não instalado", "", 0.0)

    # Verifica espaço livre em /tmp
    try:
        livre = shutil.disk_usage("/tmp").free
    except OSError:
        livre = 0
    if livre < 200 * 1024 * 1024:
        return _estado("extracao", "pulada",
                       f"espaço em /tmp insuficiente ({livre // (1024*1024)} MB)",
                       "mínimo recomendado: 200 MB livres", 0.0)

    # Diretório isolado por execução
    selo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = Path("/tmp") / f"workflow_firmware_{selo}"
    try:
        destino.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return _estado("extracao", "falhou",
                       f"não foi possível criar {destino}", str(e), 0.0)

    ctx["dir_extracao"] = str(destino)

    def acao():
        c, s, e, estourou = rodar(["binwalk", "-e", "-C", str(destino), caminho],
                                  TIMEOUTS["extracao"])
        # binwalk retorna 0 ou 1 dependendo do que achou; tratamos 0/1 como sucesso
        sucesso = (c in (0, 1)) and not estourou
        return sucesso, s, c, e, estourou

    inicio = time.monotonic()
    sucesso, saida, tentativas = tentar_com_retry("extracao", acao, status)
    duracao = time.monotonic() - inicio

    if not sucesso:
        return _estado("extracao", "falhou",
                       "falha na extração", str(saida)[:500], duracao)

    # Conta arquivos gerados
    total_arquivos = sum(1 for _ in destino.rglob("*") if _.is_file())
    ctx["total_extraidos"] = total_arquivos

    resumo = f"{total_arquivos} arquivos extraídos em {destino}"
    return _estado("extracao", "ok", resumo,
                   f"Diretório: {destino}\nArquivos: {total_arquivos}", duracao)


# --------------------------------------------------------------------------
# Etapa 4 — pós-processamento (condicional: só roda se extraiu algo)
# --------------------------------------------------------------------------
def etapa_pos_processamento(caminho, status, ctx):
    if not ctx.get("dir_extracao"):
        return _estado("pos_processamento", "pulada",
                       "extração não gerou arquivos", "", 0.0)

    destino = Path(ctx["dir_extracao"])
    if not destino.exists():
        return _estado("pos_processamento", "pulada",
                       "diretório de extração sumiu", "", 0.0)

    inicio = time.monotonic()
    achados = {"sensiveis": [], "urls": set(), "emails": set(),
               "credenciais": set(), "ips": set()}
    binarios_elf = 0

    # Varre tudo que foi extraído
    for arquivo in destino.rglob("*"):
        if not arquivo.is_file():
            continue

        # Detecta ELFs
        c, tipo, _, _ = rodar(["file", "-b", str(arquivo)], 10)
        eh_elf = c == 0 and "ELF" in tipo
        if eh_elf:
            binarios_elf += 1

        # Nomes sensíveis
        for padrao in PADROES_SENSIVEIS:
            if re.search(padrao, str(arquivo)):
                achados["sensiveis"].append(str(arquivo.relative_to(destino)))
                break

        # Strings interessantes só em ELFs (evita varrer tudo)
        if not eh_elf or not binario_existe("strings"):
            continue
        c, saida, _, _ = rodar(["strings", "-n", "6", str(arquivo)], 60)
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

    ctx["achados"] = achados
    ctx["binarios_elf"] = binarios_elf

    duracao = time.monotonic() - inicio
    resumo = (f"{binarios_elf} binários ELF, "
              f"{len(achados['sensiveis'])} arquivos sensíveis, "
              f"{len(achados['urls'])} URLs")

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

    return _estado("pos_processamento", "ok", resumo,
                   "\n".join(detalhe_linhas), duracao)


TODAS_AS_ETAPAS = {
    "identificacao": etapa_identificacao,
    "estrutura": etapa_estrutura,
    "extracao": etapa_extracao,
    "pos_processamento": etapa_pos_processamento,
}

ORDEM_PADRAO = ["identificacao", "estrutura", "extracao", "pos_processamento"]
