"""Evasão de firewall e IDS."""
import re
import shutil

from ._core import erro, resolver_alvo, resultado, validar_alvo, validar_portas


def h_evasao(params, status, timeout):
    alvo = str(params.get("alvo", "")).strip()
    tecnica = str(params.get("tecnica", "sT")).strip()
    portas = str(params.get("portas", "")).strip()
    decoys = str(params.get("decoys", "")).strip()
    mac = str(params.get("mac_falso", "")).strip()
    porta_origem = int(params.get("porta_origem", 0) or 0)
    mtu = int(params.get("mtu", 0) or 0)
    ttl = int(params.get("ttl", 0) or 0)
    data_len = int(params.get("tamanho_dados", 0) or 0)

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

    if mtu > 0 and mtu % 8 != 0:
        return erro(f"MTU deve ser múltiplo de 8 (recebido: {mtu})")
    if porta_origem > 0 and not (1 <= porta_origem <= 65535):
        return erro(f"porta_origem fora de 1-65535: {porta_origem}")
    if ttl > 0 and not (1 <= ttl <= 255):
        return erro(f"TTL fora de 1-255: {ttl}")
    if decoys and not re.fullmatch(r"[A-Za-z0-9_,.:\-]+", decoys):
        return erro(f"decoys inválidos: {decoys!r}")
    if mac and not re.fullmatch(r"[A-Za-z0-9:]+", mac):
        return erro(f"MAC inválido: {mac!r}")

    cmd = ["nmap", "-" + tecnica]
    if params.get("fragmentar"):
        cmd.append("-f")
    if mtu > 0:
        cmd.extend(["--mtu", str(mtu)])
    if decoys:
        cmd.extend(["-D", decoys])
    if porta_origem > 0:
        cmd.extend(["--source-port", str(porta_origem)])
    if ttl > 0:
        cmd.extend(["--ttl", str(ttl)])
    if mac:
        cmd.extend(["--spoof-mac", mac])
    if data_len > 0:
        cmd.extend(["--data-length", str(data_len)])
    t = params.get("timing")
    if t:
        cmd.append("-" + t)
    if portas:
        cmd.extend(["-p", portas])
    cmd.append(alvo)
    return resultado(cmd, timeout, status, f"evasão ({tecnica})", alvo)