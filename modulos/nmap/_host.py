"""Descoberta de hosts."""
import shutil

from ._core import (erro, extrair_hosts_vivos, resolver_alvo, rodar,
                    validar_alvo)


def h_descoberta(params, status, timeout):
    alvo = str(params.get("alvo", "")).strip()
    metodo = str(params.get("metodo", "sn")).strip()
    formato = str(params.get("formato", "tabela")).strip()

    alvo, e = resolver_alvo(alvo)
    if e:
        return erro(e)
    status("validando o alvo")
    ok, msg = validar_alvo(alvo)
    if not ok:
        return erro(msg)
    if not shutil.which("nmap"):
        return erro("nmap não está instalado")

    cmd = ["nmap", "-" + metodo]
    if params.get("sem_arp"):
        cmd.append("--disable-arp-ping")
    if params.get("traceroute"):
        cmd.append("--traceroute")
    if params.get("sem_dns"):
        cmd.append("-n")
    # -v só ajuda no formato bruto; na tabela ele só gera ruído
    if params.get("verbose") and formato == "bruto":
        cmd.append("-v")
    cmd.append(alvo)

    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)

    if estourou:
        return erro(f"o nmap excedeu o tempo limite de {timeout}s e foi encerrado", saida=saida)

    ok = codigo == 0
    usar_tabela = formato == "tabela" and metodo == "sn" and ok
    corpo = extrair_hosts_vivos(saida) if usar_tabela else saida

    if usar_tabela and corpo.startswith("(nenhum host vivo") and "/" in alvo:
        corpo += ("\n\nDica: se você sabe que há dispositivos na rede, verifique "
                  "se o Wi-Fi tem 'isolamento de cliente' (AP isolation) ativado "
                  "no roteador. Nesse modo, hosts Wi-Fi não se comunicam entre si "
                  "e o nmap só consegue ver o gateway.")

    relatorio = (
        f"Relatório nmap\n"
        f"Operação: descoberta de hosts\n"
        f"Alvo: {alvo}\n"
        f"Comando: {' '.join(cmd)}\n\n"
        f"{corpo}\n"
    )
    status("concluído" if ok else "o nmap retornou erro")
    return {
        "status": "ok" if ok else "erro",
        "saida": corpo,
        "erro": e if e.strip() else ("" if ok else "o nmap retornou código diferente de zero"),
        "codigo": codigo,
        "relatorio": relatorio,
    }