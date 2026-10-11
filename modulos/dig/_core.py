"""Helpers compartilhados do módulo dig."""
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


def validar_nome(nome):
    """Valida um nome de domínio (permite wildcards, subdomínios, ponto final)."""
    if not nome:
        return False, "nome vazio"
    if nome.startswith("-"):
        return False, f"nome inválido: {nome!r} (não pode começar com '-')"
    if not re.fullmatch(r"[A-Za-z0-9._*-]+", nome):
        return False, f"nome inválido: {nome!r}"
    if len(nome) > 253:
        return False, "nome excede 253 caracteres"
    return True, ""


def validar_ip(valor):
    """Valida IPv4 ou IPv6 (permite colchetes para IPv6)."""
    if not valor:
        return False, "IP vazio"
    if valor.startswith("-"):
        return False, f"IP inválido: {valor!r}"
    valor = valor.strip("[]")
    # Aceita apenas caracteres de IP: dígitos, hex, ':', '.'
    if not re.fullmatch(r"[0-9A-Fa-f.:]+", valor):
        return False, f"IP inválido: {valor!r}"
    return True, ""


def validar_servidor(servidor):
    """Servidor DNS pode ser IP ou nome."""
    if not servidor:
        return True, ""
    if servidor.startswith("-"):
        return False, f"servidor inválido: {servidor!r}"
    if not re.fullmatch(r"[A-Za-z0-9._:%-]+", servidor):
        return False, f"servidor inválido: {servidor!r}"
    return True, ""


def validar_arquivo(caminho):
    if not caminho:
        return False, "caminho vazio"
    if caminho.startswith("-"):
        return False, f"caminho inválido: {caminho!r}"
    return True, ""


def erro(msg, saida="", codigo=None):
    return {"status": "erro", "saida": saida, "erro": msg, "codigo": codigo}


def montar_formato(formato):
    """Traduz o formato escolhido em flags do dig."""
    if formato == "short":
        return ["+short"]
    if formato == "resposta":
        return ["+noall", "+answer"]
    return []  # bruto


def resultado(cmd, timeout, status, rotulo, alvo, formato="resposta"):
    status(f"executando: {' '.join(cmd)}")
    codigo, saida, e, estourou = rodar(cmd, timeout)
    if estourou:
        status("tempo limite atingido")
        return erro(f"o dig excedeu o tempo limite de {timeout}s e foi encerrado", saida=saida)
    ok = codigo == 0

    # Sinaliza ausência de resposta quando o formato é resumido e a saída é vazia
    corpo = saida
    if ok and not saida.strip() and formato in ("short", "resposta"):
        corpo = "(sem resposta para esta consulta)"

    relatorio = (
        f"Relatório dig\n"
        f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"Operação: {rotulo}\n"
        f"Alvo: {alvo}\n"
        f"Comando: {' '.join(cmd)}\n"
        f"Formato: {formato}\n"
        f"Resultado: {'ok' if ok else 'erro'}\n\n"
        f"{saida}\n"
    )
    status("concluído" if ok else "o dig retornou erro")
    return {
        "status": "ok" if ok else "erro",
        "saida": corpo,
        "erro": e if e.strip() else ("" if ok else "o dig retornou código diferente de zero"),
        "codigo": codigo,
        "relatorio": relatorio,
    }


def verificar_binario(nome):
    return shutil.which(nome) is not None