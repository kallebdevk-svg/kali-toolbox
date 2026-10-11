"""Monta o relatório do workflow de firmware com sumário executivo no topo."""

SIMBOLOS = {
    "ok": "[✓]", "parcial": "[!]", "falhou": "[✗]",
    "pulada": "[-]", "ausente": "[-]",
}

LEGENDA = {
    "ok": "a etapa rodou e produziu resultado",
    "parcial": "a etapa rodou mas não encontrou o esperado",
    "falhou": "a etapa rodou e retornou erro",
    "pulada": "a etapa foi pulada (condição não satisfeita)",
    "ausente": "a ferramenta não está instalada",
}


def _sumario_executivo(ctx, etapas):
    linhas = ["=== Sumário executivo ===", ""]

    linhas.append(f"Tipo:     {ctx.get('tipo', 'desconhecido')}")
    tamanho = ctx.get("tamanho_bytes", 0)
    linhas.append(f"Tamanho:  {tamanho} bytes ({tamanho // 1024} KB)")
    for k, v in ctx.get("hashes", {}).items():
        linhas.append(f"{k}: {v}")
    linhas.append("")

    achados = ctx.get("achados", {})
    binarios = ctx.get("binarios_elf", 0)
    estruturas = len(ctx.get("estrutura_linhas", []))

    linhas.append("Achados principais:")
    linhas.append(f"  Estruturas embutidas: {estruturas}")
    if binarios:
        linhas.append(f"  Binários ELF:         {binarios}")
    if achados.get("sensiveis"):
        linhas.append(f"  Arquivos sensíveis:   {len(achados['sensiveis'])}")
    if achados.get("credenciais"):
        linhas.append(f"  Credenciais:          {len(achados['credenciais'])}")
    if achados.get("urls"):
        linhas.append(f"  URLs:                 {len(achados['urls'])}")
    if achados.get("emails"):
        linhas.append(f"  E-mails:              {len(achados['emails'])}")

    if achados.get("sensiveis"):
        linhas.append("")
        linhas.append("Arquivos sensíveis encontrados:")
        for p in achados["sensiveis"][:15]:
            linhas.append(f"  • {p}")

    if ctx.get("dir_extracao"):
        linhas.append("")
        linhas.append(f"Diretório de extração: {ctx['dir_extracao']}")

    linhas.append("")
    return linhas


def _resumo_etapas(etapas):
    linhas = ["=== Etapas ===", ""]
    for e in etapas:
        simbolo = SIMBOLOS.get(e["estado"], "[?]")
        duracao = f"{e['duracao']:>6.1f}s" if e["duracao"] else "       "
        linhas.append(f"{simbolo} {e['nome']:<18} {duracao}  {e['resumo']}")
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
    usados = {e["estado"] for e in etapas}
    linhas = ["Legenda:"]
    for estado in ("ok", "parcial", "falhou", "pulada", "ausente"):
        if estado in usados:
            linhas.append(f"  {SIMBOLOS[estado]} {estado:<8} {LEGENDA[estado]}")
    return linhas


def montar(ctx, etapas, detalhado=False):
    """Devolve (saida_para_painel, relatorio_completo)."""
    sumario = _sumario_executivo(ctx, etapas)
    resumo = _resumo_etapas(etapas)
    detalhes = _detalhes(etapas)
    legenda = _legenda(etapas)

    completo = "\n".join(sumario + resumo + detalhes + [""] + legenda)
    if detalhado:
        painel = completo
    else:
        painel = "\n".join(
            sumario + resumo
            + ["(use 'detalhado' para incluir a saída completa de cada etapa)"]
            + [""] + legenda
        )
    return painel, completo
