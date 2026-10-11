"""Monta o relatório agregado do workflow de análise de arquivo."""

SIMBOLOS = {
    "ok": "[✓]",
    "parcial": "[!]",
    "falhou": "[✗]",
    "pulada": "[-]",
    "ausente": "[-]",
}

LEGENDA = {
    "ok": "a etapa rodou e produziu resultado",
    "parcial": "a etapa rodou mas não encontrou o esperado",
    "falhou": "a etapa rodou e retornou erro",
    "pulada": "a etapa foi pulada pelo usuário",
    "ausente": "a ferramenta não está instalada",
}


def _cabecalho_meta(versao, inicio):
    return [
        "=== Análise de arquivo ===",
        f"Versão do módulo: {versao}",
        f"Iniciado em:      {inicio}",
        "",
    ]


def _cabecalho(caminho, tamanho, etapas):
    linhas = [
        f"Arquivo:  {caminho}",
        f"Tamanho:  {tamanho}",
        "",
    ]
    for e in etapas:
        simbolo = SIMBOLOS.get(e["estado"], "[?]")
        duracao = f"{e['duracao']:>5.1f}s" if e["duracao"] else "     "
        linhas.append(f"{simbolo} {e['nome']:<10} {duracao}  {e['resumo']}")
    linhas.append("")
    return linhas


def _detalhes(etapas):
    blocos = ["=== Detalhes por etapa ===", ""]
    for e in etapas:
        blocos.append(f"--- {e['nome']} ---")
        blocos.append(e["detalhe"] or "(sem saída)")
        blocos.append("")
    return blocos


def _legenda(etapas):
    estados_usados = {e["estado"] for e in etapas}
    linhas = ["Legenda:"]
    for estado in ("ok", "parcial", "falhou", "pulada", "ausente"):
        if estado in estados_usados:
            linhas.append(f"  {SIMBOLOS[estado]} {estado:<8} {LEGENDA[estado]}")
    return linhas


def montar(caminho, tamanho, etapas, versao, inicio, detalhado=False):
    """Devolve (saida_para_painel, relatorio_completo).

    `versao` é a versão do módulo (do META), `inicio` é a data/hora do
    começo da execução, já formatada como string.
    """
    meta = _cabecalho_meta(versao, inicio)
    resumo = _cabecalho(caminho, tamanho, etapas)
    detalhes = _detalhes(etapas)
    legenda = _legenda(etapas)

    completo = "\n".join(meta + resumo + detalhes + [""] + legenda)
    if detalhado:
        painel = completo
    else:
        painel = "\n".join(
            meta + resumo
            + ["(use o parâmetro 'detalhado' para incluir os detalhes ou consulte o arquivo de relatório)"]
            + [""] + legenda
        )
    return painel, completo