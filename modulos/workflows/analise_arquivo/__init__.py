"""
Workflow do Kali Toolbox: análise de arquivo (v1.1).

Orquestra file, hashes, exiftool, strings e binwalk num relatório único.
Aceita ~ e caminhos relativos, dá mensagens específicas quando o caminho
de entrada não é válido, e grava a versão do módulo e o horário de início
no topo do relatório.
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
from ._etapas import TODAS_AS_ETAPAS
from ._relatorio import montar as montar_relatorio

META = {
    "modulo": True,
    "ferramenta": "analise_arquivo",
    "versao": "1.1",
    "descricao": "Analisa um arquivo com file, hashes, exiftool, strings e binwalk",
    "categoria": "workflows",
    "ordem": ["completa", "rapida", "etapa_unica"],
}


def verificar():
    obrigatorios = ["file", "sha256sum"]
    opcionais = ["exiftool", "strings", "binwalk"]
    faltando_obrig = [b for b in obrigatorios if not shutil.which(b)]
    if faltando_obrig:
        return False, f"binários obrigatórios ausentes: {', '.join(faltando_obrig)}"
    faltando_opc = [b for b in opcionais if not shutil.which(b)]
    if faltando_opc:
        return True, (f"pronto, mas com etapas limitadas — ausentes: "
                      f"{', '.join(faltando_opc)}")
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


def _tamanho_legivel(caminho):
    try:
        b = os.path.getsize(caminho)
    except OSError:
        return "desconhecido"
    for unidade in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unidade}" if unidade != "B" else f"{b} B"
        b /= 1024
    return f"{b:.1f} TB"


def _interpretar_pular(pular_str, disponiveis):
    if not pular_str:
        return set()
    nomes = {n.strip() for n in pular_str.split(",") if n.strip()}
    return {n for n in nomes if n in disponiveis}


def _executar_lista(caminho, etapas_escolhidas, pular, status, detalhado):
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tamanho = _tamanho_legivel(caminho)
    resultados = []
    for nome in etapas_escolhidas:
        if nome in pular:
            resultados.append({
                "nome": nome, "estado": "pulada",
                "resumo": "pulada pelo usuário", "detalhe": "",
                "duracao": 0.0,
            })
            continue
        funcao = TODAS_AS_ETAPAS.get(nome)
        if not funcao:
            continue
        resultados.append(funcao(caminho, status))

    painel, completo = montar_relatorio(
        caminho, tamanho, resultados,
        versao=META["versao"],
        inicio=inicio,
        detalhado=detalhado,
    )
    return painel, completo, resultados


def _executar_completa(params, status, timeout):
    caminho, erro_caminho = _resolver_e_validar(params.get("arquivo", ""))
    if erro_caminho:
        return {"status": "erro", "saida": "", "codigo": None, "erro": erro_caminho}

    detalhado = bool(params.get("detalhado", False))
    pular = _interpretar_pular(str(params.get("pular", "")),
                               TODAS_AS_ETAPAS.keys())

    ordem = ["file", "hashes", "exiftool", "strings", "binwalk"]
    painel, completo, resultados = _executar_lista(
        caminho, ordem, pular, status, detalhado)

    algum_ok = any(r["estado"] in ("ok", "parcial") for r in resultados)
    return {
        "status": "ok" if algum_ok else "erro",
        "saida": painel,
        "erro": "" if algum_ok else "nenhuma etapa produziu resultado",
        "codigo": 0 if algum_ok else None,
        "relatorio": completo,
    }


def _executar_rapida(params, status, timeout):
    caminho, erro_caminho = _resolver_e_validar(params.get("arquivo", ""))
    if erro_caminho:
        return {"status": "erro", "saida": "", "codigo": None, "erro": erro_caminho}

    detalhado = bool(params.get("detalhado", False))

    ordem = ["file", "hashes", "exiftool"]
    painel, completo, resultados = _executar_lista(
        caminho, ordem, set(), status, detalhado)

    algum_ok = any(r["estado"] in ("ok", "parcial") for r in resultados)
    return {
        "status": "ok" if algum_ok else "erro",
        "saida": painel,
        "erro": "" if algum_ok else "nenhuma etapa produziu resultado",
        "codigo": 0 if algum_ok else None,
        "relatorio": completo,
    }


def _executar_etapa_unica(params, status, timeout):
    caminho, erro_caminho = _resolver_e_validar(params.get("arquivo", ""))
    if erro_caminho:
        return {"status": "erro", "saida": "", "codigo": None, "erro": erro_caminho}

    etapa = str(params.get("etapa", "file")).strip()
    detalhado = bool(params.get("detalhado", True))

    painel, completo, resultados = _executar_lista(
        caminho, [etapa], set(), status, detalhado)

    algum_ok = any(r["estado"] in ("ok", "parcial") for r in resultados)
    return {
        "status": "ok" if algum_ok else "erro",
        "saida": painel,
        "erro": "" if algum_ok else f"etapa {etapa} não produziu resultado",
        "codigo": 0 if algum_ok else None,
        "relatorio": completo,
    }


def executar(funcao, parametros, status, timeout):
    if funcao == "completa":
        return _executar_completa(parametros, status, timeout)
    if funcao == "rapida":
        return _executar_rapida(parametros, status, timeout)
    if funcao == "etapa_unica":
        return _executar_etapa_unica(parametros, status, timeout)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}",
            "codigo": None}