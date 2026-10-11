"""airmon-ng: gerenciamento de modo monitor."""
from ._core import erro, resultado, rodar, validar_iface, verificar_binario


def h_airmon_start(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    canal = str(params.get("canal", "")).strip()
    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    if not verificar_binario("airmon-ng"):
        return erro("airmon-ng não está instalado")
    cmd = ["airmon-ng", "start", iface]
    if canal:
        cmd.append(canal)
    return resultado(cmd, timeout, status, "airmon-ng start", iface)


def h_airmon_stop(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    if not verificar_binario("airmon-ng"):
        return erro("airmon-ng não está instalado")
    cmd = ["airmon-ng", "stop", iface]
    return resultado(cmd, timeout, status, "airmon-ng stop", iface)


def h_airmon_check(params, status, timeout):
    if not verificar_binario("airmon-ng"):
        return erro("airmon-ng não está instalado")
    cmd = ["airmon-ng", "check"]
    if params.get("matar"):
        cmd.append("kill")
    return resultado(cmd, timeout, status, "airmon-ng check", "sistema")