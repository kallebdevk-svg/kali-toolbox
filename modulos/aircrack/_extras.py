"""Versão e ajuda."""
from ._core import erro, rodar, verificar_binario


def h_versao(params, status, timeout):
    status("consultando versões instaladas")
    if not verificar_binario("aircrack-ng"):
        return erro("aircrack-ng não está instalado")
    codigo, saida, e, _ = rodar(["aircrack-ng", "--help"], 10)
    return {"status": "ok" if codigo == 0 else "erro", "saida": saida, "erro": e, "codigo": codigo}


def h_ajuda(params, status, timeout):
    status("consultando ajuda do aircrack-ng")
    if not verificar_binario("aircrack-ng"):
        return erro("aircrack-ng não está instalado")
    codigo, saida, e, _ = rodar(["aircrack-ng", "--help"], 10)
    return {"status": "ok" if codigo == 0 else "erro", "saida": saida, "erro": e, "codigo": codigo}