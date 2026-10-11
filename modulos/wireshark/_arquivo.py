"""Leitura e análise de arquivos de captura."""
from ._core import erro, resultado, validar_arquivo, verificar_binario


def h_arquivo_ler(params, status, timeout):
    arquivo = str(params.get("arquivo", "")).strip()
    contagem = int(params.get("contagem", 0) or 0)

    ok, msg = validar_arquivo(arquivo)
    if not ok:
        return erro(msg)
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")

    cmd = ["tshark", "-r", arquivo]
    if contagem > 0:
        cmd.extend(["-c", str(contagem)])
    if params.get("detalhado"):
        cmd.append("-V")
    return resultado(cmd, timeout, status, "ler captura", arquivo)


def h_arquivo_filtrar(params, status, timeout):
    arquivo = str(params.get("arquivo", "")).strip()
    filtro = str(params.get("filtro", "")).strip()
    contagem = int(params.get("contagem", 0) or 0)

    ok, msg = validar_arquivo(arquivo)
    if not ok:
        return erro(msg)
    if not filtro:
        return erro("filtro de exibição é obrigatório")
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")

    cmd = ["tshark", "-r", arquivo, "-Y", filtro]
    if contagem > 0:
        cmd.extend(["-c", str(contagem)])
    return resultado(cmd, timeout, status, "filtrar captura", arquivo)


def h_arquivo_extrair(params, status, timeout):
    arquivo = str(params.get("arquivo", "")).strip()
    campos = str(params.get("campos", "")).strip()
    filtro = str(params.get("filtro", "")).strip()
    separador = str(params.get("separador", "")).strip()

    ok, msg = validar_arquivo(arquivo)
    if not ok:
        return erro(msg)
    if not campos:
        return erro("lista de campos é obrigatória")

    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")

    cmd = ["tshark", "-r", arquivo, "-T", "fields"]
    for c in campos.split(","):
        cmd.extend(["-e", c.strip()])
    if params.get("com_cabecalho", True):
        cmd.extend(["-E", "header=y"])
    if separador:
        cmd.extend(["-E", f"separator={separador}"])
    if filtro:
        cmd.extend(["-Y", filtro])
    return resultado(cmd, timeout, status, "extrair campos", arquivo)


def h_arquivo_estatisticas(params, status, timeout):
    arquivo = str(params.get("arquivo", "")).strip()
    tipo = str(params.get("tipo", "io,phs")).strip()

    ok, msg = validar_arquivo(arquivo)
    if not ok:
        return erro(msg)
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")

    cmd = ["tshark", "-r", arquivo, "-q", "-z", tipo]
    return resultado(cmd, timeout, status, f"estatísticas ({tipo})", arquivo)


def h_arquivo_converter(params, status, timeout):
    entrada = str(params.get("entrada", "")).strip()
    saida = str(params.get("saida", "")).strip()
    formato = str(params.get("formato", "pcap")).strip()

    ok, msg = validar_arquivo(entrada)
    if not ok:
        return erro(msg)
    ok, msg = validar_arquivo(saida)
    if not ok:
        return erro(msg)
    if not verificar_binario("editcap"):
        return erro("editcap não está instalado (pacote wireshark-common)")

    cmd = ["editcap", "-F", formato, entrada, saida]
    return resultado(cmd, timeout, status, f"converter para {formato}", entrada)


def h_arquivo_dividir(params, status, timeout):
    entrada = str(params.get("entrada", "")).strip()
    prefixo = str(params.get("prefixo", "")).strip()
    pacotes = int(params.get("pacotes_por_arquivo", 1000) or 1000)

    ok, msg = validar_arquivo(entrada)
    if not ok:
        return erro(msg)
    if not prefixo:
        return erro("prefixo de saída é obrigatório")
    if not verificar_binario("editcap"):
        return erro("editcap não está instalado (pacote wireshark-common)")

    cmd = ["editcap", "-c", str(pacotes), entrada, prefixo]
    return resultado(cmd, timeout, status, "dividir captura", entrada)