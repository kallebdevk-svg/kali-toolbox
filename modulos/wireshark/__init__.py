"""
Módulo do Kali Toolbox: wireshark (v1.0).

Suíte de captura e análise de pacotes: tshark, dumpcap, editcap,
capinfos e mergecap.
Contrato em __init__.py; handlers em arquivos _*.py ao lado.
"""
import shutil

from ._docs import DOCS
from ._funcoes import FUNCOES
from ._captura import h_interfaces, h_captura_iniciar, h_captura_ringbuffer
from ._arquivo import (h_arquivo_ler, h_arquivo_filtrar, h_arquivo_extrair,
                       h_arquivo_estatisticas, h_arquivo_converter, h_arquivo_dividir)
from ._extras import h_versao, h_ajuda

META = {
    "modulo": True,
    "ferramenta": "wireshark",
    "versao": "1.0",
    "descricao": "Suíte de captura e análise de pacotes de rede",
    "categoria": "network",
    "ordem": [
        "versao",
        "ajuda",
        "captura.interfaces",
        "captura.iniciar",
        "captura.ringbuffer",
        "arquivo.ler",
        "arquivo.filtrar",
        "arquivo.extrair",
        "arquivo.estatisticas",
        "arquivo.converter",
        "arquivo.dividir",
    ],
}


def verificar():
    faltando = [b for b in ("tshark", "dumpcap", "editcap", "capinfos", "mergecap")
                if not shutil.which(b)]
    if faltando:
        return False, f"binários ausentes no PATH: {', '.join(faltando)}"
    return True, "suíte Wireshark encontrada"


def executar(funcao, parametros, status, timeout):
    if funcao == "versao":              return h_versao(parametros, status, timeout)
    if funcao == "ajuda":               return h_ajuda(parametros, status, timeout)
    if funcao == "captura.interfaces":  return h_interfaces(parametros, status, timeout)
    if funcao == "captura.iniciar":     return h_captura_iniciar(parametros, status, timeout)
    if funcao == "captura.ringbuffer":  return h_captura_ringbuffer(parametros, status, timeout)
    if funcao == "arquivo.ler":         return h_arquivo_ler(parametros, status, timeout)
    if funcao == "arquivo.filtrar":     return h_arquivo_filtrar(parametros, status, timeout)
    if funcao == "arquivo.extrair":     return h_arquivo_extrair(parametros, status, timeout)
    if funcao == "arquivo.estatisticas": return h_arquivo_estatisticas(parametros, status, timeout)
    if funcao == "arquivo.converter":   return h_arquivo_converter(parametros, status, timeout)
    if funcao == "arquivo.dividir":     return h_arquivo_dividir(parametros, status, timeout)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}", "codigo": None}