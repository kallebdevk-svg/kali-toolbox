"""Helpers compartilhados do módulo aircrack-ng."""
import re
import shutil
import subprocess
from datetime import datetime


def rodar(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        saida = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        erro = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return None, saida, erro, True


def validar_iface(iface):
    """Valida nome de interface de rede (ex: wlan0, wlan0mon, eth0)."""
    if not iface:
        return False, "interface vazia"
    if iface.startswith("-"):
        return False, f"interface inválida: {iface!r} (não pode começar com '-')"
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", iface):
        return False, f"interface inválida: {iface!r}"
    return True, ""


def validar_mac(mac):
    """Valida endereço MAC no formato AA:BB:CC:DD:EE:FF."""
    if not mac:
        return False, "MAC vazio"
    if not re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", mac):
        return False, f"MAC inválido: {mac!r} (use o formato AA:BB:CC:DD:EE:FF)"
    return True, ""


def validar_arquivo(caminho):
    """Valida se o caminho de arquivo não começa com '-' (para não virar flag)."""
    if not caminho:
        return False, "caminho vazio"
    if caminho.startswith("-"):
        return False, f"caminho inválido: {caminho!r} (não pode começar com '-')"
    return True, ""


def erro(msg, saida="", codigo=None):
    return {"status": "erro", "saida": saida, "erro": msg, "codigo": codigo}


def resultado(cmd, timeout, status, rotulo, alvo):
    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)
    if estourou:
        status("tempo limite atingido")
        return erro(f"o comando excedeu o tempo limite de {timeout}s e foi encerrado", saida=saida)
    ok = codigo == 0
    relatorio = (
        f"Relatório aircrack-ng\n"
        f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"Operação: {rotulo}\n"
        f"Alvo: {alvo}\n"
        f"Comando: {' '.join(cmd)}\n"
        f"Resultado: {'ok' if ok else 'erro'}\n\n"
        f"{saida}"
    )
    status("concluído" if ok else "o comando retornou erro")
    return {
        "status": "ok" if ok else "erro",
        "saida": saida,
        "erro": e if e.strip() else ("" if ok else "comando retornou código diferente de zero"),
        "codigo": codigo,
        "relatorio": relatorio,
    }


def verificar_binario(nome):
    return shutil.which(nome) is not None