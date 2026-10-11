"""Helpers compartilhados entre workflows e módulos."""
import re
import shutil
import subprocess
import time


# Erros que valem uma segunda tentativa (transientes).
# FileNotFoundError e PermissionError ficam de fora: não adianta tentar de novo.
ERROS_TRANSITORIOS = (subprocess.TimeoutExpired, ConnectionError, OSError)
PADROES_NAO_RETRYAVEIS = ("permission denied", "no such file", "command not found",
                          "não encontrado", "não é possível")


def rodar(cmd, timeout):
    """Executa um comando e devolve (codigo, stdout, stderr, estourou_tempo)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        saida = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        erro = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return None, saida, erro, True


def validar_arquivo(caminho):
    """Valida um caminho de arquivo (não pode começar com '-')."""
    if not caminho:
        return False, "caminho vazio"
    if caminho.startswith("-"):
        return False, f"caminho inválido: {caminho!r} (não pode começar com '-')"
    return True, ""


def erro(msg, saida="", codigo=None):
    """Devolve um dict no formato esperado pelo menu."""
    return {"status": "erro", "saida": saida, "erro": msg, "codigo": codigo}


def ok(saida="", relatorio=None, codigo=0):
    """Devolve um dict de sucesso no formato do menu."""
    return {"status": "ok", "saida": saida, "erro": "", "codigo": codigo,
            "relatorio": relatorio}


def binario_existe(nome):
    return shutil.which(nome) is not None


def erro_e_transitorio(codigo, stderr, estourou):
    """Decide se uma falha vale retry.

    Timeout sempre vale. Código != 0 vale, exceto se o stderr contém
    mensagens claramente determinísticas (permissão, arquivo inexistente).
    """
    if estourou:
        return True
    if codigo == 0:
        return False
    texto = (stderr or "").lower()
    for padrao in PADROES_NAO_RETRYAVEIS:
        if padrao in texto:
            return False
    return True


def tentar_com_retry(nome_etapa, funcao, status, max_tentativas=3):
    """Executa `funcao` com retry em erro transiente.

    `funcao` é um callable sem argumentos que devolve
    (sucesso: bool, resultado: str, codigo: int, stderr: str, estourou: bool).

    Devolve (sucesso, resultado_final, tentativas_feitas).
    Narra cada passo via `status`.
    """
    status(f"iniciando {nome_etapa}")
    for tentativa in range(1, max_tentativas + 1):
        sucesso, resultado, codigo, stderr, estourou = funcao()
        if sucesso:
            status(f"{nome_etapa} concluído")
            return True, resultado, tentativa

        if not erro_e_transitorio(codigo, stderr, estourou):
            status(f"{nome_etapa} falhou: {stderr.strip()[:120] or 'erro determinístico'}")
            return False, resultado, tentativa

        if tentativa < max_tentativas:
            status(f"{nome_etapa} falhou, tentando novamente ({tentativa}/{max_tentativas})")
            time.sleep(1)
        else:
            status(f"{nome_etapa} erro crítico após {max_tentativas} tentativas")

    return False, resultado, max_tentativas


def limitar_linhas(texto, max_linhas, aviso="..."):
    """Trunca texto para as primeiras `max_linhas`, com aviso."""
    linhas = texto.strip().splitlines()
    if len(linhas) <= max_linhas:
        return texto.strip()
    resto = len(linhas) - max_linhas
    return "\n".join(linhas[:max_linhas]) + f"\n{aviso} (+{resto} linhas)"


def limpar_nome_ferramenta(nome):
    """Remove caracteres que atrapalham em nomes de seção."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", nome)