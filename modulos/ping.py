"""
Módulo de teste do Kali Toolbox: ping.

Usa o `ping` do sistema (já vem no Kali) só para provar que o menu
reconhece, monta o submenu, executa, mostra o log ao vivo e recebe o relatório.
"""
import re
import shutil
import subprocess
from datetime import datetime

# --- Cabeçalho (obrigatório): é o que faz o menu reconhecer o módulo --------
META = {
    "modulo": True,
    "ferramenta": "ping",
    "versao": "1.0",
    "descricao": "Testa conectividade com um host usando o ping do sistema",
    "categoria": "network",
}

# --- Funções que viram o submenu (obrigatório) ------------------------------
FUNCOES = {
    "ping_host": {
        "titulo": "Pingar um host",
        "descricao": "Envia pacotes ICMP e mostra perda e tempo de resposta",
        "usa_timeout": True,
        "timeout_padrao": 15,
        "parametros": [
            {"nome": "host", "descricao": "Host ou IP de destino", "tipo": "str", "obrigatorio": True},
            {"nome": "quantidade", "descricao": "Quantidade de pacotes (1 a 20)", "tipo": "int", "padrao": 4},
        ],
    },
    "versao": {
        "titulo": "Ver versão do ping instalado",
        "descricao": "Roda ping -V",
        "usa_timeout": False,
    },
}

# --- Documentação (opcional): aparece na opção [d] do menu ------------------
DOCS = """
O que faz:
  Encapsula o comando `ping`. Envia pacotes ICMP echo para um host e informa
  se ele respondeu, quantos pacotes se perderam e o tempo de resposta.

Como funciona por baixo:
  ping_host monta a lista [ping, -c, N, -W, 2, host] e chama subprocess.run
  SEM shell, com o tempo limite escolhido no menu. O host é validado antes
  para impedir que um valor como "-f" seja interpretado como opção.

Exemplos:
  host=127.0.0.1  quantidade=3
  host=kali.org   quantidade=4

Referência: man ping
"""


# --- Verificação (opcional) -------------------------------------------------
def verificar():
    caminho = shutil.which("ping")
    if caminho:
        return True, f"ping encontrado em {caminho}"
    return False, "o binário 'ping' não está instalado (pacote iputils-ping)"


# --- Execução (obrigatório) -------------------------------------------------
def executar(funcao, parametros, status, timeout):
    if funcao == "ping_host":
        return _ping_host(parametros, status, timeout)
    if funcao == "versao":
        return _versao(status)
    return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}", "codigo": None}


def _rodar(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        saida = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        erro = e.stderr.decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return None, saida, erro, True


def _versao(status):
    status("verificando se o ping está instalado")
    if not shutil.which("ping"):
        return {"status": "erro", "saida": "", "erro": "ping não está instalado", "codigo": None}
    status("consultando a versão (ping -V)")
    codigo, saida, erro, _ = _rodar(["ping", "-V"], 10)
    return {"status": "ok" if codigo == 0 else "erro", "saida": saida, "erro": erro, "codigo": codigo}


def _ping_host(parametros, status, timeout):
    host = str(parametros.get("host", "")).strip()
    qtd = max(1, min(int(parametros.get("quantidade", 4)), 20))

    status("validando os parâmetros")
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", host) or host.startswith("-"):
        return {"status": "erro", "saida": "", "codigo": None,
                "erro": f"host inválido: {host!r} (use apenas letras, números, '.', ':' e '-', sem começar com '-')"}

    if not shutil.which("ping"):
        return {"status": "erro", "saida": "", "codigo": None, "erro": "ping não está instalado"}

    status(f"enviando {qtd} pacote(s) ICMP para {host}")
    codigo, saida, erro, estourou = _rodar(["ping", "-c", str(qtd), "-W", "2", host], timeout)

    if estourou:
        status("tempo limite atingido, encerrando o ping")
        return {"status": "erro", "saida": saida, "codigo": None,
                "erro": f"o ping excedeu o tempo limite de {timeout}s e foi encerrado"}

    status("analisando a resposta")
    ok = codigo == 0
    relatorio = (
        f"Relatório ping\n"
        f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"Host: {host}\n"
        f"Pacotes: {qtd}\n"
        f"Resultado: {'host respondeu' if ok else 'sem resposta ou erro'}\n\n"
        f"{saida}"
    )
    status("host respondeu" if ok else "host não respondeu")
    return {
        "status": "ok" if ok else "erro",
        "saida": saida,
        "erro": erro if erro.strip() else ("" if ok else "o host não respondeu (ou o nome não foi resolvido)"),
        "codigo": codigo,
        "relatorio": relatorio,
    }