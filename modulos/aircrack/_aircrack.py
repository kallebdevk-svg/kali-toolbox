"""aircrack-ng e airdecap-ng: quebra de chaves e decriptação."""
from ._core import erro, resultado, validar_arquivo, validar_mac, verificar_binario


def h_aircrack_wep(params, status, timeout):
    captura = str(params.get("captura", "")).strip()
    bssid = str(params.get("bssid", "")).strip()
    bits = int(params.get("bits", 128) or 128)
    saida = str(params.get("saida", "")).strip()

    ok, msg = validar_arquivo(captura)
    if not ok:
        return erro(msg)
    if bssid:
        ok, msg = validar_mac(bssid)
        if not ok:
            return erro(msg)
    if not verificar_binario("aircrack-ng"):
        return erro("aircrack-ng não está instalado")

    cmd = ["aircrack-ng", "-a", "1", "-n", str(bits)]
    if bssid:
        cmd.extend(["-b", bssid])
    if params.get("forcar_ptw"):
        cmd.append("-z")
    if params.get("korek"):
        cmd.append("-K")
    if saida:
        cmd.extend(["-l", saida])
    cmd.append(captura)
    return resultado(cmd, timeout, status, "aircrack WEP", captura)


def h_aircrack_wpa(params, status, timeout):
    captura = str(params.get("captura", "")).strip()
    wordlist = str(params.get("wordlist", "")).strip()
    bssid = str(params.get("bssid", "")).strip()
    essid = str(params.get("essid", "")).strip()
    threads = int(params.get("threads", 0) or 0)
    hccapx = str(params.get("exportar_hccapx", "")).strip()
    saida = str(params.get("saida", "")).strip()

    ok, msg = validar_arquivo(captura)
    if not ok:
        return erro(msg)
    ok, msg = validar_arquivo(wordlist)
    if not ok:
        return erro(msg)
    if bssid:
        ok, msg = validar_mac(bssid)
        if not ok:
            return erro(msg)
    if not verificar_binario("aircrack-ng"):
        return erro("aircrack-ng não está instalado")

    cmd = ["aircrack-ng", "-a", "2", "-w", wordlist]
    if bssid:
        cmd.extend(["-b", bssid])
    if essid:
        cmd.extend(["-e", essid])
    if threads > 0:
        cmd.extend(["-p", str(threads)])
    if hccapx:
        cmd.extend(["-j", hccapx])
    if saida:
        cmd.extend(["-l", saida])
    cmd.append(captura)
    return resultado(cmd, timeout, status, "aircrack WPA", captura)


def h_airdecap(params, status, timeout):
    captura = str(params.get("captura", "")).strip()
    chave_wep = str(params.get("chave_wep", "")).strip()
    essid = str(params.get("essid", "")).strip()
    passphrase = str(params.get("passphrase", "")).strip()
    pmk = str(params.get("pmk", "")).strip()
    bssid = str(params.get("bssid", "")).strip()

    ok, msg = validar_arquivo(captura)
    if not ok:
        return erro(msg)
    if bssid:
        ok, msg = validar_mac(bssid)
        if not ok:
            return erro(msg)
    if not verificar_binario("airdecap-ng"):
        return erro("airdecap-ng não está instalado")

    cmd = ["airdecap-ng"]
    if chave_wep:
        cmd.extend(["-w", chave_wep])
    if essid:
        cmd.extend(["-e", essid])
    if passphrase:
        cmd.extend(["-p", passphrase])
    if pmk:
        cmd.extend(["-k", pmk])
    if bssid:
        cmd.extend(["-b", bssid])
    cmd.append(captura)
    return resultado(cmd, timeout, status, "airdecap-ng", captura)