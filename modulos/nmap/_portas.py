"""Scan de portas."""
import shutil

from ._core import erro, resolver_alvo, resultado, validar_alvo, validar_portas


def h_scan_portas(params, status, timeout):
    alvo = str(params.get("alvo", "")).strip()
    tecnica = str(params.get("tecnica", "sT")).strip()
    portas = str(params.get("portas", "")).strip()
    top_portas = int(params.get("top_portas", 0) or 0)

    alvo, e = resolver_alvo(alvo)
    if e:
        return erro(e)
    status("validando parâmetros")
    ok, msg = validar_alvo(alvo)
    if not ok:
        return erro(msg)
    ok, msg = validar_portas(portas)
    if not ok:
        return erro(msg)
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")

    cmd = ["nmap", "-" + tecnica]
    if params.get("rapido"):
        cmd.append("-F")
    elif top_portas > 0:
        cmd.extend(["--top-ports", str(top_portas)])
    elif portas:
        cmd.extend(["-p", portas])
    if params.get("sequencial"):
        cmd.append("-r")
    if params.get("pular_ping"):
        cmd.append("-Pn")
    if params.get("sem_dns"):
        cmd.append("-n")
    t = params.get("timing")
    if t:
        cmd.append("-" + t)
    if params.get("mostrar_abertas"):
        cmd.append("--open")
    if params.get("motivo"):
        cmd.append("--reason")
    if params.get("verbose"):
        cmd.append("-v")
    cmd.append(alvo)
    return resultado(cmd, timeout, status, f"scan de portas ({tecnica})", alvo)