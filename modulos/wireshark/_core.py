"""Helpers compartilhados do módulo wireshark."""
import re
import shutil
import subprocess
from datetime import datetime


def rodar(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        saida = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        erro = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return None, saida, erro, True


def validar_iface(iface):
    """Valida nome de interface de rede (ex: eth0, wlan0, any)."""
    if not iface:
        return False, "interface vazia"
    if iface.startswith("-"):
        return False, f"interface inválida: {iface!r} (não pode começar com '-')"
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", iface):
        return False, f"interface inválida: {iface!r}"
    return True, ""


def validar_arquivo(caminho):
    """Valida caminho de arquivo (não pode começar com '-')."""
    if not caminho:
        return False, "caminho vazio"
    if caminho.startswith("-"):
        return False, f"caminho inválido: {caminho!r} (não pode começar com '-')"
    return True, ""


def erro(msg, saida="", codigo=None):
    return {"status": "erro", "saida": saida, "erro": msg, "codigo": codigo}


def resultado(cmd, timeout, status, rotulo, alvo):
    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)
    if estourou:
        status("tempo limite atingido")
        return erro(f"o comando excedeu o tempo limite de {timeout}s e foi encerrado", saida=saida)
    ok = codigo == 0
    relatorio = (
        f"Relatório wireshark\n"
        f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"Operação: {rotulo}\n"
        f"Alvo: {alvo}\n"
        f"Comando: {' '.join(cmd)}\n"
        f"Resultado: {'ok' if ok else 'erro'}\n\n"
        f"{saida}"
    )
    status("concluído" if ok else "o comando retornou erro")
    return {
        "status": "ok" if ok else "erro",
        "saida": saida,
        "erro": e if e.strip() else ("" if ok else "comando retornou código diferente de zero"),
        "codigo": codigo,
        "relatorio": relatorio,
    }


def verificar_binario(nome):
    return shutil.which(nome) is not None


def formatar_pacotes(texto, largura_total=100):
    """Formata a saída de 'tshark -T fields' como uma tabela alinhada."""
    linhas = [l for l in texto.strip().splitlines() if l.strip()]
    if not linhas:
        return "(nenhum pacote capturado)"

    cabecalho = ["#", "Tempo", "Origem", "Destino", "Proto", "Tam", "Info"]
    registros = []
    for linha in linhas:
        p = linha.split("\t")
        while len(p) < 7:
            p.append("")
        num, tempo, src, dst, proto, tam, info = p[:7]
        try:
            tempo = f"{float(tempo):.3f}"
        except ValueError:
            pass
        registros.append([num, tempo, src, dst, proto, tam, info])

    def maior(col, cap):
        m = max((len(r[col]) for r in registros), default=0)
        return min(max(m, len(cabecalho[col])), cap)

    larg = [maior(0, 6), 8, maior(2, 20), maior(3, 20), maior(4, 8), maior(5, 5)]
    fixo = sum(larg) + 6 * 2
    larg.append(max(20, largura_total - fixo))

    def fmt(reg):
        celulas = []
        for i, v in enumerate(reg):
            if len(v) > larg[i]:
                v = v[: larg[i] - 1] + "~"
            celulas.append(v.ljust(larg[i]))
        return "  ".join(celulas).rstrip()

    saida = [fmt(cabecalho), "  ".join("-" * w for w in larg)]
    for reg in registros:
        saida.append(fmt(reg))
    return "\n".join(saida)