"""Versão e ajuda."""
from datetime import datetime

from ._core import erro, rodar, verificar_binario

FERRAMENTAS = ["tshark", "dumpcap", "editcap", "capinfos", "mergecap"]


def h_versao(params, status, timeout):
    status("consultando versões instaladas")
    linhas = []
    for nome in FERRAMENTAS:
        if not verificar_binario(nome):
            linhas.append(f"{nome:<12} NÃO ENCONTRADO no PATH")
            continue
        codigo, saida, e, _ = rodar([nome, "--version"], 10)
        cabecalho = ""
        for l in saida.splitlines():
            if l.strip():
                cabecalho = l.strip()
                break
        linhas.append(f"{nome:<12} {cabecalho or '(sem saída)'}")

    texto = "Versões instaladas:\n\n" + "\n".join(linhas)
    relatorio = (
        f"Versões da suíte Wireshark\n"
        f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
        f"{texto}\n"
    )
    status("concluído")
    return {"status": "ok", "saida": texto, "erro": "", "codigo": 0, "relatorio": relatorio}


def h_ajuda(params, status, timeout):
    status("consultando ajuda do tshark")
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")
    codigo, saida, e, _ = rodar(["tshark", "--help"], 10)
    return {"status": "ok" if codigo == 0 else "erro", "saida": saida, "erro": e, "codigo": codigo}