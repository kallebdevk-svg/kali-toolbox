"""
Módulo do Kali Toolbox: aircrack-ng (v1.0).

Suíte de auditoria Wi-Fi: airmon-ng, airodump-ng, aireplay-ng,
aircrack-ng e airdecap-ng.
Contrato em __init__.py; handlers em arquivos _*.py ao lado.
"""
import shutil

from ._docs import DOCS
from ._funcoes import FUNCOES
from ._airmon import h_airmon_start, h_airmon_stop, h_airmon_check
from ._airodump import h_airodump_scan
from ._aireplay import h_aireplay_deauth, h_aireplay_fakeauth, h_aireplay_arpreplay, h_aireplay_test
from ._aircrack import h_aircrack_wep, h_aircrack_wpa, h_airdecap
from ._extras import h_versao, h_ajuda

META = {
    "modulo": True,
    "ferramenta": "aircrack-ng",
    "versao": "1.0",
    "descricao": "Suíte de auditoria de redes Wi-Fi (WEP/WPA/WPA2)",
    "categoria": "wireless",
    "ordem": [
        "versao",
        "ajuda",
        "airmon.start",
        "airmon.stop",
        "airmon.check",
        "airodump.scan",
        "aireplay.deauth",
        "aireplay.fakeauth",
        "aireplay.arpreplay",
        "aireplay.test",
        "aircrack.wep",
        "aircrack.wpa",
        "airdecap.decrypt",
    ],
}


def verificar():
    faltando = [b for b in ("aircrack-ng", "airmon-ng", "airodump-ng",
                            "aireplay-ng", "airdecap-ng")
                if not shutil.which(b)]
    if faltando:
        return False, f"binários ausentes no PATH: {', '.join(faltando)}"
    return True, "suíte aircrack-ng encontrada"


def executar(funcao, parametros, status, timeout):
    if funcao == "versao":             return h_versao(parametros, status, timeout)
    if funcao == "ajuda":              return h_ajuda(parametros, status, timeout)
    if funcao == "airmon.start":       return h_airmon_start(parametros, status, timeout)
    if funcao == "airmon.stop":        return h_airmon_stop(parametros, status, timeout)
    if funcao == "airmon.check":       return h_airmon_check(parametros, status, timeout)
    if funcao == "airodump.scan":      return h_airodump_scan(parametros, status, timeout)
    if funcao == "aireplay.deauth":    return h_aireplay_deauth(parametros, status, timeout)
    if funcao == "aireplay.fakeauth":  return h_aireplay_fakeauth(parametros, status, timeout)
    if funcao == "aireplay.arpreplay": return h_aireplay_arpreplay(parametros, status, timeout)
    if funcao == "aireplay.test":      return h_aireplay_test(parametros, status, timeout)
    if funcao == "aircrack.wep":       return h_aircrack_wep(parametros, status, timeout)
    if funcao == "aircrack.wpa":       return h_aircrack_wpa(parametros, status, timeout)
    if funcao == "airdecap.decrypt":   return h_airdecap(parametros, status, timeout)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}", "codigo": None}