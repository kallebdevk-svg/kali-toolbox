"""Consultas ao DNS."""
from ._core import (erro, montar_formato, resultado, validar_arquivo,
                    validar_ip, validar_nome, validar_servidor,
                    verificar_binario)


def _montar_cmd(nome_ou_x, tipo, servidor, formato, extras):
    cmd = ["dig"]
    cmd.extend(montar_formato(formato))
    if tipo:
        cmd.append(tipo)
    if nome_ou_x:
        cmd.append(nome_ou_x)
    if servidor:
        cmd.append("@" + servidor)
    cmd.extend(extras)
    return cmd


def h_consulta_simples(params, status, timeout):
    nome = str(params.get("nome", "")).strip()
    tipo = str(params.get("tipo", "A")).strip()
    servidor = str(params.get("servidor", "")).strip()
    formato = str(params.get("formato", "resposta")).strip()

    ok, msg = validar_nome(nome)
    if not ok:
        return erro(msg)
    ok, msg = validar_servidor(servidor)
    if not ok:
        return erro(msg)
    if not verificar_binario("dig"):
        return erro("dig não está instalado (pacote dnsutils)")

    extras = []
    if params.get("dnssec"):
        extras.append("+dnssec")
    if params.get("tcp"):
        extras.append("+tcp")
    if params.get("sem_recurse"):
        extras.append("+norecurse")

    cmd = ["dig"] + montar_formato(formato) + [nome, tipo]
    if servidor:
        cmd.append("@" + servidor)
    cmd.extend(extras)
    return resultado(cmd, timeout, status, f"consulta {tipo}", nome, formato)


def h_consulta_reversa(params, status, timeout):
    ip = str(params.get("ip", "")).strip()
    servidor = str(params.get("servidor", "")).strip()
    formato = str(params.get("formato", "resposta")).strip()

    ok, msg = validar_ip(ip)
    if not ok:
        return erro(msg)
    ok, msg = validar_servidor(servidor)
    if not ok:
        return erro(msg)
    if not verificar_binario("dig"):
        return erro("dig não está instalado")

    cmd = ["dig"] + montar_formato(formato) + ["-x", ip]
    if servidor:
        cmd.append("@" + servidor)
    return resultado(cmd, timeout, status, "consulta reversa", ip, formato)


def h_consulta_lote(params, status, timeout):
    arquivo = str(params.get("arquivo", "")).strip()
    servidor = str(params.get("servidor", "")).strip()
    formato = str(params.get("formato", "resposta")).strip()

    ok, msg = validar_arquivo(arquivo)
    if not ok:
        return erro(msg)
    ok, msg = validar_servidor(servidor)
    if not ok:
        return erro(msg)
    if not verificar_binario("dig"):
        return erro("dig não está instalado")

    cmd = ["dig"] + montar_formato(formato) + ["-f", arquivo]
    if servidor:
        cmd.append("@" + servidor)
    return resultado(cmd, timeout, status, "consulta em lote", arquivo, formato)