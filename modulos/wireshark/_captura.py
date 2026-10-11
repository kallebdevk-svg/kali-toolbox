"""tshark/dumpcap: captura de pacotes."""
from pathlib import Path

from ._core import (erro, formatar_pacotes, resultado, rodar, validar_iface,
                    verificar_binario)


def _foto_arquivos(prefixo):
    """Retorna {(nome, tamanho)} dos arquivos que casam com o prefixo.
    Usado para detectar se a captura criou ou cresceu arquivos."""
    if not prefixo:
        return set()
    try:
        return {(str(p), p.stat().st_size)
                for p in Path(prefixo).parent.glob(Path(prefixo).name + "*")
                if p.is_file()}
    except OSError:
        return set()


def h_interfaces(params, status, timeout):
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado (pacote wireshark-common)")
    cmd = ["tshark", "-D"]
    return resultado(cmd, timeout, status, "listar interfaces", "sistema")


def h_captura_iniciar(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    filtro_cap = str(params.get("filtro_captura", "")).strip()
    filtro_disp = str(params.get("filtro_display", "")).strip()
    contagem = int(params.get("contagem", 0) or 0)
    salvar = str(params.get("salvar", "")).strip()
    formato = str(params.get("formato", "tabela")).strip()

    if salvar.lower() in ("vazio", "nenhum", "none", "-", "n/a", "na"):
        salvar = ""

    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")

    cmd = ["tshark", "-i", iface]
    if filtro_cap:
        cmd.extend(["-f", filtro_cap])
    if filtro_disp:
        cmd.extend(["-Y", filtro_disp])
    if contagem > 0:
        cmd.extend(["-c", str(contagem)])
    if salvar:
        cmd.extend(["-w", salvar])
    if params.get("promiscuo") is False:
        cmd.append("-p")
    if params.get("sem_dns"):
        cmd.append("-n")

    # Formato tabela só faz sentido quando não estamos salvando em arquivo
    usar_tabela = formato == "tabela" and not salvar
    if usar_tabela:
        cmd.extend(["-T", "fields",
                    "-e", "frame.number",
                    "-e", "frame.time_relative",
                    "-e", "_ws.col.Source",
                    "-e", "_ws.col.Destination",
                    "-e", "_ws.col.Protocol",
                    "-e", "frame.len",
                    "-e", "_ws.col.Info",
                    "-E", "separator=/t",
                    "-E", "occurrence=f"])

    antes = _foto_arquivos(salvar) if salvar else set()

    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)

    # Timeout: pode ser parada normal ou erro. Decide pelo contexto:
    #   - salvando em arquivo: sucesso se arquivos foram criados/cresceram
    #   - mostrando na tela: sucesso se houve saída de pacotes
    if estourou:
        if salvar:
            depois = _foto_arquivos(salvar)
            cresceu = depois != antes and depois
            if cresceu:
                arquivos = sorted(nome for nome, _ in depois)
                status(f"captura encerrada pelo timeout de {timeout}s")
                resumo = (
                    f"[captura interrompida pelo timeout de {timeout}s — parada normal]\n\n"
                    f"Arquivos gerados:\n"
                    + "\n".join(f"  {a}  ({t} bytes)" for a, t in sorted(depois))
                )
                relatorio = (
                    f"Captura em ring buffer\n"
                    f"Interface: {iface}\n"
                    f"Prefixo: {salvar}\n"
                    f"Filtro BPF: {filtro_cap or '(nenhum)'}\n"
                    f"Tempo: {timeout}s\n\n"
                    f"{resumo}\n"
                )
                return {"status": "ok", "saida": resumo, "erro": "",
                        "codigo": None, "relatorio": relatorio}
            return erro(
                f"timeout de {timeout}s e nenhum arquivo foi criado — "
                f"verifique se o diretório de '{salvar}' existe e tem permissão de escrita "
                f"para o usuário 'wireshark'",
                saida=saida)

        if saida.strip():
            corpo = formatar_pacotes(saida) if usar_tabela else saida
            aviso = f"[captura interrompida pelo timeout de {timeout}s — parada normal]\n\n"
            status(f"captura interrompida pelo timeout de {timeout}s")
            relatorio = (
                f"Captura ao vivo\n"
                f"Interface: {iface}\n"
                f"Filtro BPF: {filtro_cap or '(nenhum)'}\n"
                f"Filtro display: {filtro_disp or '(nenhum)'}\n"
                f"Tempo: {timeout}s\n\n"
                f"{corpo}\n"
            )
            return {"status": "ok", "saida": aviso + corpo, "erro": "",
                    "codigo": None, "relatorio": relatorio}

        return erro(f"o comando excedeu o tempo limite de {timeout}s sem capturar nada",
                    saida=saida)

    # Sem timeout: caminho normal.
    corpo = formatar_pacotes(saida) if usar_tabela else saida
    ok = codigo == 0
    relatorio = (
        f"Captura ao vivo\n"
        f"Interface: {iface}\n"
        f"Comando: {' '.join(cmd)}\n\n"
        f"{corpo}\n"
    )
    status("concluído" if ok else "o comando retornou erro")
    return {
        "status": "ok" if ok else "erro",
        "saida": corpo,
        "erro": e if e.strip() else ("" if ok else "comando retornou código diferente de zero"),
        "codigo": codigo,
        "relatorio": relatorio,
    }


def h_captura_ringbuffer(params, status, timeout):
    iface = str(params.get("interface", "")).strip()
    prefixo = str(params.get("prefixo", "")).strip()
    arquivos = int(params.get("arquivos", 5) or 5)
    tamanho_kb = int(params.get("tamanho_kb", 1024) or 1024)
    filtro_cap = str(params.get("filtro_captura", "")).strip()

    if prefixo.lower() in ("vazio", "nenhum", "none", "-", "n/a", "na"):
        prefixo = ""

    ok, msg = validar_iface(iface)
    if not ok:
        return erro(msg)
    if not prefixo:
        return erro("prefixo de saída é obrigatório")
    if not verificar_binario("tshark"):
        return erro("tshark não está instalado")

    cmd = ["tshark", "-i", iface, "-w", prefixo,
           "-b", f"files:{arquivos}", "-b", f"filesize:{tamanho_kb}"]
    if filtro_cap:
        cmd.extend(["-f", filtro_cap])

    antes = _foto_arquivos(prefixo)

    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)

    depois = _foto_arquivos(prefixo)
    cresceu = depois != antes and depois

    if estourou:
        if cresceu:
            status(f"captura encerrada pelo timeout de {timeout}s")
            resumo = (
                f"[captura interrompida pelo timeout de {timeout}s — parada normal]\n\n"
                f"Arquivos gerados:\n"
                + "\n".join(f"  {a}  ({t} bytes)" for a, t in sorted(depois))
            )
            relatorio = (
                f"Captura em ring buffer\n"
                f"Interface: {iface}\n"
                f"Prefixo: {prefixo}\n"
                f"Filtro BPF: {filtro_cap or '(nenhum)'}\n"
                f"Tempo: {timeout}s\n\n"
                f"{resumo}\n"
            )
            return {"status": "ok", "saida": resumo, "erro": "",
                    "codigo": None, "relatorio": relatorio}
        return erro(
            f"timeout de {timeout}s e nenhum arquivo foi criado — "
            f"verifique se o diretório de '{prefixo}' existe e tem permissão de escrita "
            f"para o usuário 'wireshark'",
            saida=saida)

    if codigo == 0 and cresceu:
        status("captura concluída")
        resumo = ("Arquivos gerados:\n"
                  + "\n".join(f"  {a}  ({t} bytes)" for a, t in sorted(depois)))
        relatorio = (
            f"Captura em ring buffer\n"
            f"Interface: {iface}\n"
            f"Prefixo: {prefixo}\n"
            f"Comando: {' '.join(cmd)}\n\n"
            f"{resumo}\n"
        )
        return {"status": "ok", "saida": resumo, "erro": "", "codigo": codigo,
                "relatorio": relatorio}

    status("o comando retornou erro")
    return erro(
        e.strip() or "o tshark terminou sem produzir arquivos",
        saida=saida, codigo=codigo)