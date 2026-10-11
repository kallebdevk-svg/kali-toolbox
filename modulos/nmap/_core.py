"""Helpers compartilhados do módulo nmap."""
import ipaddress
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


def validar_alvo(alvo):
    if not alvo:
        return False, "alvo vazio"
    if alvo.startswith("-"):
        return False, f"alvo inválido: {alvo!r} (não pode começar com '-')"
    if not re.fullmatch(r"[A-Za-z0-9._:/-]+", alvo):
        return False, f"alvo inválido: {alvo!r}"
    return True, ""


def validar_portas(portas):
    if not portas:
        return True, ""
    if not re.fullmatch(r"[\d,\-]+", portas):
        return False, f"portas inválidas: {portas!r}"
    for parte in portas.split(","):
        if "-" in parte:
            a, _, b = parte.partition("-")
            if not (a.isdigit() and b.isdigit()):
                return False, f"intervalo inválido: {parte!r}"
            if not (1 <= int(a) <= 65535 and 1 <= int(b) <= 65535):
                return False, f"porta fora de 1-65535: {parte!r}"
            if int(a) > int(b):
                return False, f"intervalo invertido: {parte!r}"
        else:
            if not parte.isdigit() or not (1 <= int(parte) <= 65535):
                return False, f"porta fora de 1-65535: {parte!r}"
    return True, ""


def redes_locais():
    if not shutil.which("ip"):
        return []
    try:
        p = subprocess.run(["ip", "-o", "-4", "addr", "show"],
                           capture_output=True, text=True, timeout=5)
    except Exception:
        return []
    if p.returncode != 0:
        return []
    redes = []
    for linha in p.stdout.splitlines():
        partes = linha.split()
        if len(partes) < 4 or partes[2] != "inet":
            continue
        iface = partes[1]
        if iface == "lo":
            continue
        cidr = partes[3]
        try:
            rede = str(ipaddress.IPv4Interface(cidr).network)
        except Exception:
            rede = cidr
        redes.append((iface, cidr, rede))
    return redes


def resolver_alvo(alvo):
    if alvo in ("local", "auto"):
        redes = redes_locais()
        if not redes:
            return None, "não foi possível detectar a rede local (nenhuma interface IPv4 ativa)"
        return redes[0][2], None
    return alvo, None


def erro(msg, saida="", codigo=None):
    return {"status": "erro", "saida": saida, "erro": msg, "codigo": codigo}


def resultado(cmd, timeout, status, rotulo, alvo):
    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)
    if estourou:
        status("tempo limite atingido")
        return erro(f"o nmap excedeu o tempo limite de {timeout}s e foi encerrado", saida=saida)
    ok = codigo == 0
    relatorio = (
        f"Relatório nmap\n"
        f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"Operação: {rotulo}\n"
        f"Alvo: {alvo}\n"
        f"Comando: {' '.join(cmd)}\n"
        f"Resultado: {'ok' if ok else 'erro'}\n\n"
        f"{saida}"
    )
    status("concluído" if ok else "o nmap retornou erro")
    return {
        "status": "ok" if ok else "erro",
        "saida": saida,
        "erro": e if e.strip() else ("" if ok else "o nmap retornou código diferente de zero"),
        "codigo": codigo,
        "relatorio": relatorio,
    }


def extrair_hosts_vivos(texto):
    """Extrai os hosts vivos da saída de 'nmap -sn' e devolve uma tabela alinhada."""
    linhas = texto.splitlines()
    hosts = []
    atual = None
    for l in linhas:
        m = re.match(r"Nmap scan report for (.+)", l)
        if m:
            atual = {"alvo": m.group(1).strip(), "up": False,
                     "mac": "", "vendor": "", "latencia": "-"}
            hosts.append(atual)
            continue
        if atual is None:
            continue
        if "Host is up" in l:
            atual["up"] = True
            lat = re.search(r"\(([^)]+)\)", l)
            if lat:
                atual["latencia"] = lat.group(1)
        elif "MAC Address:" in l:
            m2 = re.match(r"MAC Address: (\S+)\s*(?:\((.+)\))?", l.strip())
            if m2:
                atual["mac"] = m2.group(1)
                atual["vendor"] = m2.group(2) or ""

    vivos = [h for h in hosts if h["up"]]
    if not vivos:
        return "(nenhum host vivo encontrado)"

    linhas_saida = [f"Hosts vivos: {len(vivos)} (de {len(hosts)} endereços verificados)", ""]
    larg_ip = max(len("IP/Nome"), max(len(h["alvo"]) for h in vivos)) + 2
    larg_mac = max(len("MAC"), max((len(h["mac"]) for h in vivos), default=3)) + 2
    cab = f"{'IP/Nome':<{larg_ip}}{'MAC':<{larg_mac}}{'Fabricante':<20}{'Latência':<10}"
    linhas_saida.append(cab)
    linhas_saida.append("-" * len(cab))
    for h in vivos:
        linhas_saida.append(
            f"{h['alvo']:<{larg_ip}}{h['mac'] or '-':<{larg_mac}}"
            f"{h['vendor'] or '-':<20}{h['latencia']:<10}"
        )
    return "\n".join(linhas_saida)