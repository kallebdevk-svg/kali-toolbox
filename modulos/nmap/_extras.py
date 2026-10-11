"""Versão, ajuda, agressivo, traceroute e construtor."""
import re
import shutil

from ._core import erro, resolver_alvo, resultado, rodar, validar_alvo, validar_portas


def h_versao(params, status, timeout):
    status("consultando a versão do nmap")
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")
    codigo, saida, e, _ = rodar(["nmap", "--version"], 10)
    return {"status": "ok" if codigo == 0 else "erro", "saida": saida, "erro": e, "codigo": codigo}


def h_ajuda(params, status, timeout):
    status("consultando a ajuda do nmap")
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")
    codigo, saida, e, _ = rodar(["nmap", "--help"], 10)
    return {"status": "ok" if codigo == 0 else "erro", "saida": saida, "erro": e, "codigo": codigo}


def h_agressivo(params, status, timeout):
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

    cmd = ["nmap", "-A"]
    if params.get("pular_ping"):
        cmd.append("-Pn")
    if portas:
        cmd.extend(["-p", portas])
    cmd.append(alvo)
    return resultado(cmd, timeout, status, "scan agressivo (-A)", alvo)


def h_traceroute(params, status, timeout):
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

    cmd = ["nmap", "--traceroute"]
    if params.get("sem_dns"):
        cmd.append("-n")
    if portas:
        cmd.extend(["-p", portas])
    cmd.append(alvo)
    return resultado(cmd, timeout, status, "traceroute", alvo)


def h_construtor(params, status, timeout):
    tecnica = str(params.get("parte1_tecnica", "sT")).strip()
    deteccao = str(params.get("parte2_deteccao", "nenhuma")).strip()
    portas = str(params.get("parte3_portas", "")).strip()
    timing = str(params.get("parte4_timing", "T4")).strip()
    extra_str = str(params.get("parte5_extra", "")).strip()
    alvo = str(params.get("alvo", "")).strip()

    alvo, e = resolver_alvo(alvo)
    if e:
        return erro(e)
    status("validando as partes do comando")
    ok, msg = validar_alvo(alvo)
    if not ok:
        return erro(msg)
    ok, msg = validar_portas(portas)
    if not ok:
        return erro(msg)
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")

    cmd = ["nmap"]
    if tecnica and tecnica != "nenhuma":
        cmd.append("-" + tecnica)
    if deteccao and deteccao != "nenhuma":
        if deteccao == "sV+sC":
            cmd.extend(["-sV", "-sC"])
        else:
            cmd.append("-" + deteccao)
    if portas and tecnica != "sn":
        cmd.extend(["-p", portas])
    if timing and timing != "nenhuma":
        cmd.append("-" + timing)
    if extra_str:
        for f in extra_str.split():
            if not re.fullmatch(r"[A-Za-z0-9._:=,/\-]+", f):
                return erro(f"flag extra inválida: {f!r}")
            cmd.append(f)
    cmd.append(alvo)
    return resultado(cmd, timeout, status, "construtor", alvo)