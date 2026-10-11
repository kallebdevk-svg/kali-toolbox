"""
Módulo do Kali Toolbox: dig (v1.0).

Ferramenta de consulta ao DNS: consulta simples, reversa, em lote,
trace e DNSSEC.
Contrato em __init__.py; handlers em arquivos _*.py ao lado.
"""
import shutil

from ._docs import DOCS
from ._funcoes import FUNCOES
from ._consulta import h_consulta_simples, h_consulta_reversa, h_consulta_lote
from ._avancado import h_trace, h_dnssec
from ._extras import h_versao, h_ajuda

META = {
    "modulo": True,
    "ferramenta": "dig",
    "versao": "1.0",
    "descricao": "Consultas DNS: simples, reversa, lote, trace e DNSSEC",
    "categoria": "dns",
    "ordem": [
        "versao",
        "ajuda",
        "consulta.simples",
        "consulta.reversa",
        "consulta.lote",
        "avancado.trace",
        "avancado.dnssec",
    ],
}


def verificar():
    caminho = shutil.which("dig")
    if caminho:
        return True, f"dig encontrado em {caminho}"
    return False, "o binário 'dig' não está instalado (pacote dnsutils)"


def executar(funcao, parametros, status, timeout):
    if funcao == "versao":            return h_versao(parametros, status, timeout)
    if funcao == "ajuda":             return h_ajuda(parametros, status, timeout)
    if funcao == "consulta.simples":  return h_consulta_simples(parametros, status, timeout)
    if funcao == "consulta.reversa":  return h_consulta_reversa(parametros, status, timeout)
    if funcao == "consulta.lote":     return h_consulta_lote(parametros, status, timeout)
    if funcao == "avancado.trace":    return h_trace(parametros, status, timeout)
    if funcao == "avancado.dnssec":   return h_dnssec(parametros, status, timeout)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}", "codigo": None}