"""Detecção de serviço, SO e scripts NSE."""
import re
import shutil

from ._core import erro, resolver_alvo, resultado, validar_alvo, validar_portas


def h_servico_versao(params, status, timeout):
    alvo = str(params.get("alvo", "")).strip()
    portas = str(params.get("portas", "")).strip()
    intensidade = int(params.get("intensidade", 7) or 7)
    modo = str(params.get("modo", "normal")).strip()

    alvo, e = resolver_alvo(alvo)
    if e:
        return erro(e)
    ok, msg = validar_alvo(alvo)
    if not ok:
        return erro(msg)
    ok, msg = validar_portas(portas)
    if not ok:
        return erro(msg)
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")

    cmd = ["nmap", "-sV"]
    if modo == "light":
        cmd.append("--version-light")
    elif modo == "all":
        cmd.append("--version-all")
    else:
        intensidade = max(0, min(9, intensidade))
        cmd.extend(["--version-intensity", str(intensidade)])
    if params.get("trace"):
        cmd.append("--version-trace")
    if params.get("pular_ping"):
        cmd.append("-Pn")
    t = params.get("timing")
    if t:
        cmd.append("-" + t)
    if portas:
        cmd.extend(["-p", portas])
    cmd.append(alvo)
    return resultado(cmd, timeout, status, "detecção de serviço", alvo)


def h_servico_so(params, status, timeout):
    alvo = str(params.get("alvo", "")).strip()
    portas = str(params.get("portas", "")).strip()

    alvo, e = resolver_alvo(alvo)
    if e:
        return erro(e)
    ok, msg = validar_alvo(alvo)
    if not ok:
        return erro(msg)
    ok, msg = validar_portas(portas)
    if not ok:
        return erro(msg)
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")

    cmd = ["nmap", "-O"]
    if params.get("limitar"):
        cmd.append("--osscan-limit")
    if params.get("adivinhar"):
        cmd.append("--osscan-guess")
    if params.get("pular_ping"):
        cmd.append("-Pn")
    if portas:
        cmd.extend(["-p", portas])
    cmd.append(alvo)
    return resultado(cmd, timeout, status, "detecção de SO", alvo)


def h_servico_nse(params, status, timeout):
    alvo = str(params.get("alvo", "")).strip()
    categoria = str(params.get("categoria", "default")).strip()
    extra = str(params.get("scripts_extra", "")).strip()
    args = str(params.get("args", "")).strip()
    portas = str(params.get("portas", "")).strip()

    alvo, e = resolver_alvo(alvo)
    if e:
        return erro(e)
    ok, msg = validar_alvo(alvo)
    if not ok:
        return erro(msg)
    ok, msg = validar_portas(portas)
    if not ok:
        return erro(msg)
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")

    if categoria == "customizado":
        if not extra:
            return erro("categoria 'customizado' exige scripts_extra preenchido")
        if not re.fullmatch(r"[A-Za-z0-9_,.*\-]+", extra):
            return erro(f"scripts_extra inválido: {extra!r}")
        cmd = ["nmap", "--script", extra]
    else:
        cmd = ["nmap", "--script", categoria]

    if args:
        cmd.extend(["--script-args", args])
    if params.get("trace"):
        cmd.append("--script-trace")
    if params.get("pular_ping"):
        cmd.append("-Pn")
    if portas:
        cmd.extend(["-p", portas])
    cmd.append(alvo)
    return resultado(cmd, timeout, status, f"NSE ({categoria})", alvo)