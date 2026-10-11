"""Versão e ajuda."""
from ._core import erro, rodar, verificar_binario


def h_versao(params, status, timeout):
    status("consultando a versão do dig")
    if not verificar_binario("dig"):
        return erro("dig não está instalado (pacote dnsutils)")
    codigo, saida, e, _ = rodar(["dig", "-v"], 10)
    return {"status": "ok" if codigo == 0 else "erro",
            "saida": saida.strip() or "dig não informou a versão",
            "erro": e, "codigo": codigo}


def h_ajuda(params, status, timeout):
    status("consultando a ajuda do dig")
    if not verificar_binario("dig"):
        return erro("dig não está instalado")
    codigo, saida, e, _ = rodar(["dig", "-h"], 10)
    return {"status": "ok" if codigo == 0 else "erro",
            "saida": saida, "erro": e, "codigo": codigo}