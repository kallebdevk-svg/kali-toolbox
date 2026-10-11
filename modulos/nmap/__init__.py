"""
Módulo do Kali Toolbox: nmap (v1.4).

Contrato em __init__.py; handlers em arquivos _*.py ao lado.
"""
import shutil

from ._docs import DOCS
from ._funcoes import FUNCOES
from ._rede import h_rede_local
from ._host import h_descoberta
from ._portas import h_scan_portas
from ._servico import h_servico_versao, h_servico_so, h_servico_nse
from ._evasao import h_evasao
from ._extras import h_versao, h_ajuda, h_agressivo, h_traceroute, h_construtor

META = {
    "modulo": True,
    "ferramenta": "nmap",
    "versao": "1.4",
    "descricao": "Scanner de rede com cobertura das funções do nmap",
    "categoria": "network",
    "ordem": [
        "rede_local",
        "versao",
        "ajuda",
        "descoberta.hosts",
        "portas.scan",
        "servico.version",
        "servico.os",
        "servico.nse",
        "agressivo",
        "evasao.firewall",
        "traceroute",
        "construtor",
    ],
}


def verificar():
    caminho = shutil.which("nmap")
    if caminho:
        return True, f"nmap encontrado em {caminho}"
    return False, "o binário 'nmap' não está instalado (pacote nmap)"


def executar(funcao, parametros, status, timeout):
    if funcao == "rede_local":       return h_rede_local(parametros, status, timeout)
    if funcao == "versao":           return h_versao(parametros, status, timeout)
    if funcao == "ajuda":            return h_ajuda(parametros, status, timeout)
    if funcao == "descoberta.hosts": return h_descoberta(parametros, status, timeout)
    if funcao == "portas.scan":      return h_scan_portas(parametros, status, timeout)
    if funcao == "servico.version":  return h_servico_versao(parametros, status, timeout)
    if funcao == "servico.os":       return h_servico_so(parametros, status, timeout)
    if funcao == "servico.nse":      return h_servico_nse(parametros, status, timeout)
    if funcao == "agressivo":        return h_agressivo(parametros, status, timeout)
    if funcao == "evasao.firewall":  return h_evasao(parametros, status, timeout)
    if funcao == "traceroute":       return h_traceroute(parametros, status, timeout)
    if funcao == "construtor":       return h_construtor(parametros, status, timeout)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}", "codigo": None}