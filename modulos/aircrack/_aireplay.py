"""aireplay-ng: injeção de pacotes."""
from ._core import erro, resultado, validar_iface, validar_mac, verificar_binario


def h_aireplay_deauth(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    bssid = str(params.get("bssid", "")).strip()
    cliente = str(params.get("cliente", "")).strip()
    count = int(params.get("count", 5) or 5)
    motivo = int(params.get("motivo", 7) or 7)

    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    ok, msg = validar_mac(bssid)
    if not ok:
        return erro(msg)
    if cliente:
        ok, msg = validar_mac(cliente)
        if not ok:
            return erro(msg)
    if not verificar_binario("aireplay-ng"):
        return erro("aireplay-ng não está instalado")

    cmd = ["aireplay-ng", "-0", str(count), "-a", bssid]
    if cliente:
        cmd.extend(["-c", cliente])
    if motivo != 7:
        cmd.extend(["--deauth-rc", str(motivo)])
    cmd.append(iface)
    return resultado(cmd, timeout, status, "aireplay deauth", bssid)


def h_aireplay_fakeauth(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    bssid = str(params.get("bssid", "")).strip()
    essid = str(params.get("essid", "")).strip()
    delay = int(params.get("delay", 0) or 0)

    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    ok, msg = validar_mac(bssid)
    if not ok:
        return erro(msg)
    if not essid:
        return erro("ESSID é obrigatório para autenticação falsa")
    if not verificar_binario("aireplay-ng"):
        return erro("aireplay-ng não está instalado")

    cmd = ["aireplay-ng", "-1", str(delay), "-a", bssid, "-e", essid, iface]
    return resultado(cmd, timeout, status, "aireplay fakeauth", bssid)


def h_aireplay_arpreplay(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    bssid = str(params.get("bssid", "")).strip()
    pps = int(params.get("pps", 0) or 0)

    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    ok, msg = validar_mac(bssid)
    if not ok:
        return erro(msg)
    if not verificar_binario("aireplay-ng"):
        return erro("aireplay-ng não está instalado")

    cmd = ["aireplay-ng", "-3", "-b", bssid]
    if pps > 0:
        cmd.extend(["-x", str(pps)])
    cmd.append(iface)
    return resultado(cmd, timeout, status, "aireplay arpreplay", bssid)


def h_aireplay_test(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    if not verificar_binario("aireplay-ng"):
        return erro("aireplay-ng não está instalado")
    cmd = ["aireplay-ng", "-9", iface]
    return resultado(cmd, timeout, status, "aireplay test", iface)