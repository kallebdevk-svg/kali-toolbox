"""
Workflow do Kali Toolbox: análise de firmware (v1.0).

Orquestra file, hashes, binwalk e análise dos arquivos extraídos
em um relatório único com sumário executivo.
"""
import os
import shutil

from ._docs import DOCS
from ._funcoes import FUNCOES
from ._etapas import TODAS_AS_ETAPAS, ORDEM_PADRAO
from ._relatorio import montar as montar_relatorio

META = {
    "modulo": True,
    "ferramenta": "analise_firmware",
    "versao": "1.0",
    "descricao": "Análise de firmware com binwalk, extração e inspeção dos arquivos extraídos",
    "categoria": "workflows",
    "ordem": ["completa", "estrutura_simples"],
}


def verificar():
    obrig = ["file", "binwalk"]
    opc = ["strings", "sha256sum"]
    faltando_obrig = [b for b in obrig if not shutil.which(b)]
    if faltando_obrig:
        return False, f"binários obrigatórios ausentes: {', '.join(faltando_obrig)}"
    faltando_opc = [b for b in opc if not shutil.which(b)]
    if faltando_opc:
        return True, f"pronto, mas etapas limitadas — ausentes: {', '.join(faltando_opc)}"
    return True, "todas as ferramentas disponíveis"


def _executar_etapas(caminho, ordem, detalhado, status):
    ctx = {}
    resultados = []
    for nome in ordem:
        funcao = TODAS_AS_ETAPAS.get(nome)
        if not funcao:
            continue
        resultados.append(funcao(caminho, status, ctx))

    painel, completo = montar_relatorio(ctx, resultados, detalhado=detalhado)
    return painel, completo, resultados


def _executar_completa(params, status, timeout):
    caminho = str(params.get("arquivo", "")).strip()
    detalhado = bool(params.get("detalhado", False))
    if not caminho or not os.path.isfile(caminho):
        return {"status": "erro", "saida": "", "codigo": None,
                "erro": f"arquivo não encontrado: {caminho!r}"}

    painel, completo, resultados = _executar_etapas(caminho, ORDEM_PADRAO,
                                                    detalhado, status)
    algum_ok = any(r["estado"] in ("ok", "parcial") for r in resultados)
    return {
        "status": "ok" if algum_ok else "erro",
        "saida": painel,
        "erro": "" if algum_ok else "nenhuma etapa produziu resultado",
        "codigo": 0 if algum_ok else None,
        "relatorio": completo,
    }


def _executar_estrutura_simples(params, status, timeout):
    caminho = str(params.get("arquivo", "")).strip()
    detalhado = bool(params.get("detalhado", True))
    if not caminho or not os.path.isfile(caminho):
        return {"status": "erro", "saida": "", "codigo": None,
                "erro": f"arquivo não encontrado: {caminho!r}"}

    ordem = ["identificacao", "estrutura"]
    painel, completo, resultados = _executar_etapas(caminho, ordem, detalhado, status)
    algum_ok = any(r["estado"] in ("ok", "parcial") for r in resultados)
    return {
        "status": "ok" if algum_ok else "erro",
        "saida": painel,
        "erro": "" if algum_ok else "nenhuma etapa produziu resultado",
        "codigo": 0 if algum_ok else None,
        "relatorio": completo,
    }


def executar(funcao, parametros, status, timeout):
    if funcao == "completa":
        return _executar_completa(parametros, status, timeout)
    if funcao == "estrutura_simples":
        return _executar_estrutura_simples(parametros, status, timeout)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}",
            "codigo": None}
