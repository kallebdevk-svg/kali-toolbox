"""Uma função por etapa. Cada uma roda uma ferramenta externa.

Cada etapa devolve um dicionário com os campos:
  nome      identificador curto da etapa
  estado    "ok" | "parcial" | "falhou" | "pulada" | "ausente"
  duracao   segundos gastos
  resumo    uma linha para o resumo do relatório
  detalhe   saída completa para o relatório
"""
import sys
import time
from pathlib import Path

_raiz = Path(__file__).resolve().parents[2]
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

from _lib._core import binario_existe, limitar_linhas, rodar, tentar_com_retry


# Timeout individual de cada ferramenta, em segundos.
TIMEOUTS = {
    "file": 10,
    "hashes": 30,
    "exiftool": 30,
    "strings": 120,
    "binwalk": 300,
}


def _etapa_ok(nome, resumo, detalhe, duracao):
    return {"nome": nome, "estado": "ok", "resumo": resumo,
            "detalhe": detalhe, "duracao": duracao}


def _etapa_parcial(nome, resumo, detalhe, duracao):
    return {"nome": nome, "estado": "parcial", "resumo": resumo,
            "detalhe": detalhe, "duracao": duracao}


def _etapa_falhou(nome, resumo, detalhe, duracao):
    return {"nome": nome, "estado": "falhou", "resumo": resumo,
            "detalhe": detalhe, "duracao": duracao}


def _etapa_pulada(nome, motivo):
    return {"nome": nome, "estado": "pulada", "resumo": motivo,
            "detalhe": motivo, "duracao": 0.0}


def _etapa_ausente(nome):
    return {"nome": nome, "estado": "ausente",
            "resumo": f"{nome} não está instalado",
            "detalhe": f"o binário '{nome}' não foi encontrado no PATH",
            "duracao": 0.0}


# --------------------------------------------------------------------------
# Etapas
# --------------------------------------------------------------------------
def etapa_file(caminho, status):
    if not binario_existe("file"):
        return _etapa_ausente("file")

    def acao():
        codigo, saida, erro, estourou = rodar(["file", "-b", caminho],
                                              TIMEOUTS["file"])
        sucesso = (codigo == 0 and not estourou)
        return sucesso, saida.strip(), codigo, erro, estourou

    inicio = time.monotonic()
    sucesso, resultado, tentativas = tentar_com_retry("file", acao, status)
    duracao = time.monotonic() - inicio
    if sucesso:
        return _etapa_ok("file", resultado, resultado, duracao)
    return _etapa_falhou("file", "não foi possível identificar o arquivo",
                        resultado or "(sem saída)", duracao)


def etapa_hashes(caminho, status):
    if not binario_existe("sha256sum"):
        return _etapa_ausente("hashes")

    def acao():
        resultados = {}
        for algo in ("md5sum", "sha1sum", "sha256sum"):
            if not binario_existe(algo):
                resultados[algo] = "(ausente)"
                continue
            codigo, saida, erro, estourou = rodar([algo, caminho],
                                                  TIMEOUTS["hashes"])
            if codigo != 0 or estourou:
                return False, "", codigo, erro, estourou
            resultados[algo] = saida.split()[0]
        return True, resultados, 0, "", False

    inicio = time.monotonic()
    sucesso, resultado, tentativas = tentar_com_retry("hashes", acao, status)
    duracao = time.monotonic() - inicio
    if sucesso and isinstance(resultado, dict):
        detalhe = "\n".join(f"  {k:<10} {v}" for k, v in resultado.items())
        resumo = " ".join(f"{k.replace('sum','')}={v[:12]}..." for k, v in resultado.items()
                          if v and v != "(ausente)")
        return _etapa_ok("hashes", resumo, detalhe, duracao)
    return _etapa_falhou("hashes", "não foi possível calcular os hashes",
                        str(resultado) or "(sem saída)", duracao)


def etapa_exiftool(caminho, status):
    if not binario_existe("exiftool"):
        return _etapa_ausente("exiftool")

    def acao():
        codigo, saida, erro, estourou = rodar(["exiftool", caminho],
                                              TIMEOUTS["exiftool"])
        sucesso = (codigo == 0 and not estourou)
        return sucesso, saida, codigo, erro, estourou

    inicio = time.monotonic()
    sucesso, resultado, tentativas = tentar_com_retry("exiftool", acao, status)
    duracao = time.monotonic() - inicio
    if not sucesso:
        return _etapa_falhou("exiftool", "não foi possível extrair metadados",
                            str(resultado) or "(sem saída)", duracao)

    linhas = [l for l in (resultado or "").splitlines() if l.strip()]
    if not linhas:
        return _etapa_parcial("exiftool", "nenhum metadado extraído",
                             "(sem metadados)", duracao)
    detalhe = limitar_linhas(resultado, 60, "... (mais metadados no arquivo completo)")
    resumo = f"{len(linhas)} metadados extraídos"
    return _etapa_ok("exiftool", resumo, detalhe, duracao)


def etapa_strings(caminho, status):
    if not binario_existe("strings"):
        return _etapa_ausente("strings")

    def acao():
        codigo, saida, erro, estourou = rodar(
            ["strings", "-n", "6", caminho], TIMEOUTS["strings"])
        sucesso = (codigo == 0 and not estourou)
        return sucesso, saida, codigo, erro, estourou

    inicio = time.monotonic()
    sucesso, resultado, tentativas = tentar_com_retry("strings", acao, status)
    duracao = time.monotonic() - inicio
    if not sucesso:
        return _etapa_falhou("strings", "falha ao extrair strings",
                            str(resultado) or "(sem saída)", duracao)

    linhas = [l for l in (resultado or "").splitlines() if l.strip()]
    if not linhas:
        return _etapa_parcial("strings", "nenhuma string notável",
                             "(nenhuma string com 6+ caracteres)", duracao)
    detalhe = limitar_linhas(resultado, 80, "... (mais strings no arquivo completo)")
    resumo = f"{len(linhas)} strings (top 15 abaixo)"
    return _etapa_ok("strings", resumo, detalhe, duracao)


def etapa_binwalk(caminho, status):
    if not binario_existe("binwalk"):
        return _etapa_ausente("binwalk")

    def acao():
        codigo, saida, erro, estourou = rodar(
            ["binwalk", caminho], TIMEOUTS["binwalk"])
        sucesso = (codigo == 0 and not estourou)
        return sucesso, saida, codigo, erro, estourou

    inicio = time.monotonic()
    sucesso, resultado, tentativas = tentar_com_retry("binwalk", acao, status)
    duracao = time.monotonic() - inicio
    if not sucesso:
        return _etapa_falhou("binwalk", "falha na análise de estrutura",
                            str(resultado) or "(sem saída)", duracao)

    linhas = [l for l in (resultado or "").splitlines() if l.strip()]
    # Binwalk sempre imprime um cabeçalho; filtramos para ver se achou algo
    corpo = [l for l in linhas
             if not l.startswith(("DECIMAL", "----", "Scan Time",
                                  "Target File", "MD5 Checksum",
                                  "Signatures", "WARNING", "NOTE:"))]
    if not corpo:
        return _etapa_parcial("binwalk", "nada extraível encontrado",
                             "(nenhuma estrutura embutida identificada)", duracao)
    detalhe = limitar_linhas(resultado, 50, "... (mais entradas no arquivo completo)")
    resumo = f"{len(corpo)} estruturas identificadas"
    return _etapa_ok("binwalk", resumo, detalhe, duracao)


TODAS_AS_ETAPAS = {
    "file": etapa_file,
    "hashes": etapa_hashes,
    "exiftool": etapa_exiftool,
    "strings": etapa_strings,
    "binwalk": etapa_binwalk,
}
