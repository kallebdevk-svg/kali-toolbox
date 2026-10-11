"""airodump-ng: captura de pacotes."""
from ._core import erro, resultado, validar_iface, validar_mac, verificar_binario


def h_airodump_scan(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    canal = str(params.get("canal", "")).strip()
    bssid = str(params.get("bssid", "")).strip()
    essid = str(params.get("essid", "")).strip()
    write = str(params.get("write", "")).strip()
    banda = str(params.get("banda", "")).strip()

    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    if bssid:
        ok, msg = validar_mac(bssid)
        if not ok:
            return erro(msg)
    if not verificar_binario("airodump-ng"):
        return erro("airodump-ng não está instalado")

    cmd = ["airodump-ng"]
    if canal:
        cmd.extend(["-c", canal])
    if bssid:
        cmd.extend(["--bssid", bssid])
    if essid:
        cmd.extend(["--essid", essid])
    if write:
        cmd.extend(["-w", write])
    if banda:
        cmd.extend(["--band", banda])
    if params.get("mostrar_wps"):
        cmd.append("--wps")
    if params.get("mostrar_ack"):
        cmd.append("--showack")
    cmd.append(iface)
    return resultado(cmd, timeout, status, "airodump-ng scan", iface)