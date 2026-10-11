"""Trace e DNSSEC."""
from ._core import (erro, montar_formato, resultado, validar_nome,
                    validar_servidor, verificar_binario)


def h_trace(params, status, timeout):
    nome = str(params.get("nome", "")).strip()
    tipo = str(params.get("tipo", "A")).strip()
    formato = str(params.get("formato", "bruto")).strip()

    ok, msg = validar_nome(nome)
    if not ok:
        return erro(msg)
    if not verificar_binario("dig"):
        return erro("dig não está instalado")

    cmd = ["dig"] + montar_formato(formato) + [nome, tipo, "+trace"]
    return resultado(cmd, timeout, status, f"trace {tipo}", nome, formato)


def h_dnssec(params, status, timeout):
    nome = str(params.get("nome", "")).strip()
    tipo = str(params.get("tipo", "A")).strip()
    servidor = str(params.get("servidor", "")).strip()
    formato = str(params.get("formato", "bruto")).strip()

    ok, msg = validar_nome(nome)
    if not ok:
        return erro(msg)
    ok, msg = validar_servidor(servidor)
    if not ok:
        return erro(msg)
    if not verificar_binario("dig"):
        return erro("dig não está instalado")

    cmd = ["dig"] + montar_formato(formato) + [nome, tipo, "+dnssec"]
    if servidor:
        cmd.append("@" + servidor)
    return resultado(cmd, timeout, status, f"dnssec {tipo}", nome, formato)