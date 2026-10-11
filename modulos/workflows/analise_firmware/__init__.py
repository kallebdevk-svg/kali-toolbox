"""
Workflow do Kali Toolbox: análise de firmware (v1.4).

Orquestra file, hashes, binwalk e análise dos arquivos extraídos
em um relatório único com sumário executivo. Aceita padrões regex
extras, expande ~ e caminhos relativos, dá mensagens específicas
quando o caminho de entrada não é válido, e grava a versão do módulo
e o horário de início no topo do relatório.
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

_raiz = Path(__file__).resolve().parents[2]
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

from _lib._core import resolver_caminho, validar_arquivo_existe

from ._docs import DOCS
from ._funcoes import FUNCOES
from ._etapas import TODAS_AS_ETAPAS, ORDEM_PADRAO
from ._relatorio import montar as montar_relatorio

META = {
    "modulo": True,
    "ferramenta": "analise_firmware",
    "versao": "1.4",
    "descricao": "Análise de firmware com binwalk, extração, inspeção dos arquivos e busca por padrões",
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


def _resolver_e_validar(caminho_bruto):
    """Resolve o caminho e valida como arquivo regular.

    Devolve (caminho_absoluto, mensagem_de_erro).
    Se a mensagem for vazia, o caminho é válido.
    """
    caminho = resolver_caminho(str(caminho_bruto).strip())
    if not caminho:
        return "", "caminho vazio"
    ok, msg = validar_arquivo_existe(caminho)
    if not ok:
        return caminho, msg
    return caminho, ""


def _executar_etapas(caminho, ordem, detalhado, procurar, status):
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx = {"procurar": procurar or ""}
    resultados = []
    for nome in ordem:
        funcao = TODAS_AS_ETAPAS.get(nome)
        if not funcao:
            continue
        resultados.append(funcao(caminho, status, ctx))

    painel, completo = montar_relatorio(
        ctx, resultados,
        versao=META["versao"],
        inicio=inicio,
        detalhado=detalhado,
    )
    return painel, completo, resultados


def _executar_completa(params, status, timeout):
    caminho, erro_caminho = _resolver_e_validar(params.get("arquivo", ""))
    if erro_caminho:
        return {"status": "erro", "saida": "", "codigo": None, "erro": erro_caminho}

    procurar = str(params.get("procurar", "")).strip()
    detalhado = bool(params.get("detalhado", False))

    painel, completo, resultados = _executar_etapas(
        caminho, ORDEM_PADRAO, detalhado, procurar, status)
    algum_ok = any(r["estado"] in ("ok", "parcial") for r in resultados)
    return {
        "status": "ok" if algum_ok else "erro",
        "saida": painel,
        "erro": "" if algum_ok else "nenhuma etapa produziu resultado",
        "codigo": 0 if algum_ok else None,
        "relatorio": completo,
    }


def _executar_estrutura_simples(params, status, timeout):
    caminho, erro_caminho = _resolver_e_validar(params.get("arquivo", ""))
    if erro_caminho:
        return {"status": "erro", "saida": "", "codigo": None, "erro": erro_caminho}

    detalhado = bool(params.get("detalhado", True))

    ordem = ["identificacao", "estrutura"]
    painel, completo, resultados = _executar_etapas(
        caminho, ordem, detalhado, "", status)
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