#!/usr/bin/env python3
"""
Kali Toolbox - menu orquestrador de módulos.

O menu NÃO conhece nenhuma ferramenta. Ele só:
  1. varre a pasta de módulos e acopla automaticamente cada arquivo .py válido;
  2. monta os submenus a partir do que cada módulo declara em FUNCOES;
  3. pede os parâmetros e o tempo limite, e manda tudo de volta para o módulo;
  4. roda o módulo numa thread, mostra o log ao vivo e protege contra erros;
  5. recebe o resultado/relatório e registra tudo em logs/menu.log.

Para adicionar uma ferramenta: coloque um módulo na pasta (veja
docs/COMO_CRIAR_MODULO.md). Nenhuma alteração neste arquivo é necessária.

Uso:  python3 menu.py [--pasta CAMINHO_DOS_MODULOS]
"""
from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import queue
import re
import shutil
import sys
import textwrap
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

if sys.version_info < (3, 10):
    sys.exit("Kali Toolbox precisa do Python 3.10 ou superior.")

# --------------------------------------------------------------------------
# Configuração
# --------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
PASTA_MODULOS = BASE / "modulos"      # pasta varrida em busca de módulos
PASTA_LOGS = BASE / "logs"
PASTA_RELATORIOS = BASE / "relatorios"

TIMEOUT_PADRAO = 30       # s, usado se a função não definir "timeout_padrao"
TOLERANCIA = 5            # s extras antes do menu desistir de esperar a thread
ESPERA_VERIFICAR = 15     # s máximos para a função opcional verificar()
MAX_LINHAS_PAINEL = 40    # linhas de saída mostradas no painel (o resto vai ao log)

log = logging.getLogger("kali_toolbox")


# --------------------------------------------------------------------------
# Estruturas
# --------------------------------------------------------------------------
@dataclass
class Modulo:
    arquivo: Path
    nome: str                      # META["ferramenta"]
    versao: str                    # META["versao"]
    meta: dict
    funcoes: dict
    executar: Callable
    verificar: Callable | None
    docs: str | None
    pacote: bool = False           # True se o módulo é uma pasta com __init__.py


@dataclass
class Rejeitado:
    arquivo: Path
    motivo: str
    pacote: bool = False


# --------------------------------------------------------------------------
# Apresentação (terminal)
# --------------------------------------------------------------------------
USAR_COR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def cor(texto: str, codigo: str) -> str:
    return f"\033[{codigo}m{texto}\033[0m" if USAR_COR else texto


def largura() -> int:
    return max(60, min(shutil.get_terminal_size((100, 24)).columns, 110))


def painel(titulo: str, linhas: list[str], cor_borda: str = "36") -> None:
    """Desenha um painel com borda. Texto interno é sempre sem cor (largura exata)."""
    total = largura()
    interno = total - 4
    titulo = titulo[: interno - 2]
    corpo: list[str] = []
    for linha in linhas:
        if not linha.strip():
            corpo.append("")
            continue
        recuo = len(linha) - len(linha.lstrip())
        corpo += textwrap.wrap(linha, interno, subsequent_indent=" " * recuo) or [""]
    topo = "╭─ " + titulo + " " + "─" * max(0, total - len(titulo) - 5) + "╮"
    print(cor(topo, cor_borda))
    for linha in corpo:
        print(cor("│", cor_borda) + " " + linha.ljust(interno) + " " + cor("│", cor_borda))
    print(cor("╰" + "─" * (total - 2) + "╯", cor_borda))


def ler(prompt: str) -> str:
    return input(cor(f"{prompt} > ", "1")).strip()


def imprimir_status(m: Modulo, momento: datetime, msg: str) -> None:
    hora = momento.strftime("%H:%M:%S")
    print(f"{cor(hora, '90')} {cor('[' + m.nome + ']', '36')} {cor('[v' + m.versao + ']', '33')} {msg}")


def resumo_excecao(e: BaseException) -> str:
    """Tipo, mensagem e ONDE o erro aconteceu (arquivo, linha, função)."""
    if isinstance(e, SystemExit):
        return "o módulo tentou encerrar o programa (sys.exit)"
    onde = ""
    quadros = traceback.extract_tb(e.__traceback__)
    if quadros:
        q = quadros[-1]
        onde = f" (em {Path(q.filename).name}, linha {q.lineno}, função {q.name})"
    return f"{type(e).__name__}: {e}{onde}"


# --------------------------------------------------------------------------
# Descoberta e validação de módulos
# --------------------------------------------------------------------------
def limpar_modulo(nome: str) -> None:
    """Remove o módulo e seus submódulos do cache, para que alterações sejam relidas."""
    for chave in [k for k in sys.modules if k == nome or k.startswith(nome + ".")]:
        del sys.modules[chave]


_AVISADOS: set[tuple[str, str]] = set()


def carregar_arquivo(arquivo: Path, pasta: Path) -> Modulo | Rejeitado:
    """`arquivo` é um .py solto ou o __init__.py de uma pasta (módulo em pacote)."""
    pacote = arquivo.name == "__init__.py"
    rel = (arquivo.parent if pacote else arquivo).relative_to(pasta)
    nome_interno = "kt_" + re.sub(r"\W", "_", str(rel if pacote else rel.with_suffix("")))

    def rejeitar(motivo: str) -> Rejeitado:
        limpar_modulo(nome_interno)
        return Rejeitado(rel, motivo, pacote)

    # 1) importação dinâmica, protegida (limpa o cache para ler a versão atual)
    limpar_modulo(nome_interno)
    try:
        extra = {"submodule_search_locations": [str(arquivo.parent)]} if pacote else {}
        spec = importlib.util.spec_from_file_location(nome_interno, arquivo, **extra)
        if spec is None or spec.loader is None:
            return rejeitar("não foi possível criar o carregador de importação")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[nome_interno] = mod
        spec.loader.exec_module(mod)
    except SyntaxError as e:
        onde = Path(e.filename).name if e.filename else arquivo.name
        return rejeitar(f"erro de sintaxe em {onde}, linha {e.lineno}: {e.msg}")
    except (Exception, SystemExit) as e:
        return rejeitar(f"erro ao importar: {resumo_excecao(e)}")

    # 2) validação do contrato (junta todos os problemas de uma vez)
    problemas: list[str] = []

    meta = getattr(mod, "META", None)
    if not isinstance(meta, dict):
        problemas.append("cabeçalho META ausente ou não é um dict")
        meta = {}
    else:
        if meta.get("modulo") is not True:
            problemas.append('META["modulo"] precisa ser True')
        for chave in ("ferramenta", "versao"):
            if not str(meta.get(chave, "")).strip():
                problemas.append(f'META["{chave}"] ausente ou vazio')
        ordem = meta.get("ordem")
        if ordem is not None and (not isinstance(ordem, list) or not all(isinstance(x, str) for x in ordem)):
            problemas.append('META["ordem"] precisa ser uma lista de chaves de FUNCOES')

    funcoes = getattr(mod, "FUNCOES", None)
    if not isinstance(funcoes, dict) or not funcoes:
        problemas.append("FUNCOES ausente, vazio ou não é um dict")
        funcoes = {}
    else:
        for chave, f in funcoes.items():
            if not isinstance(chave, str) or not chave or any(not parte for parte in chave.split(".")):
                problemas.append(f"FUNCOES: chave inválida {chave!r} (use texto; partes separadas por ponto não podem ser vazias)")
                continue
            if not isinstance(f, dict):
                problemas.append(f'FUNCOES["{chave}"] precisa ser um dict')
                continue
            params = f.get("parametros", [])
            if not isinstance(params, list) or not all(
                isinstance(p, dict) and p.get("nome") for p in params
            ):
                problemas.append(
                    f'FUNCOES["{chave}"]["parametros"] precisa ser uma lista de dicts com "nome"'
                )

    executar = getattr(mod, "executar", None)
    if not callable(executar):
        problemas.append("função executar ausente")

    verificar = getattr(mod, "verificar", None)
    if verificar is not None and not callable(verificar):
        problemas.append("verificar existe mas não é uma função")
        verificar = None

    docs = getattr(mod, "DOCS", None)
    if docs is not None and not isinstance(docs, str):
        problemas.append("DOCS existe mas não é texto")
        docs = None

    if problemas:
        return rejeitar("; ".join(problemas))

    # ordem de exibição: META["ordem"] primeiro (se existir), o resto na ordem do dict
    nome = str(meta["ferramenta"]).strip()
    pedida = meta.get("ordem") or []
    for chave in pedida:
        if chave not in funcoes and (nome, chave) not in _AVISADOS:
            _AVISADOS.add((nome, chave))
            log.warning("[%s] META['ordem'] cita uma chave que não existe em FUNCOES: %s", nome, chave)
    ordenadas = list(dict.fromkeys([c for c in pedida if c in funcoes] + list(funcoes)))
    funcoes = {c: funcoes[c] for c in ordenadas}

    return Modulo(
        arquivo=rel,
        nome=nome,
        versao=str(meta["versao"]).strip(),
        meta=meta,
        funcoes=funcoes,
        executar=executar,
        verificar=verificar,
        docs=docs,
        pacote=pacote,
    )


def _entradas(atual: Path):
    """Cada .py solto e cada pasta com __init__.py (pacote) é UM módulo.
    Pastas sem __init__.py são só categorias: o menu entra nelas.
    Nomes que começam com _ ou . são ignorados (inclusive _core.py dentro de um pacote)."""
    for item in sorted(atual.iterdir()):
        if item.name.startswith(("_", ".")):
            continue
        if item.is_dir():
            init = item / "__init__.py"
            if init.is_file():
                yield init
            else:
                yield from _entradas(item)
        elif item.suffix == ".py":
            yield item


def descobrir(pasta: Path) -> tuple[list[Modulo], list[Rejeitado]]:
    """Varre a pasta (recursivamente) e carrega cada módulo encontrado."""
    modulos: list[Modulo] = []
    rejeitados: list[Rejeitado] = []
    if not pasta.is_dir():
        return [], [Rejeitado(Path(str(pasta)), "a pasta de módulos não existe")]
    for arq in _entradas(pasta):
        r = carregar_arquivo(arq, pasta)
        (modulos if isinstance(r, Modulo) else rejeitados).append(r)
    return modulos, rejeitados


# --------------------------------------------------------------------------
# Parâmetros e timeout (perguntados pelo menu, definidos pelo módulo)
# --------------------------------------------------------------------------
def converter(valor: str, tipo: str, opcoes: list | None):
    if tipo == "int":
        v = int(valor)
    elif tipo == "float":
        v = float(valor)
    elif tipo == "bool":
        baixo = valor.lower()
        if baixo in ("s", "sim", "y", "yes", "true", "1"):
            v = True
        elif baixo in ("n", "nao", "não", "no", "false", "0"):
            v = False
        else:
            raise ValueError("responda sim ou não")
    else:
        v = valor
    if opcoes and v not in opcoes:
        raise ValueError(f"escolha uma das opções: {', '.join(map(str, opcoes))}")
    return v


def pedir_parametros(funcao: dict) -> dict:
    params: dict = {}
    for p in funcao.get("parametros", []):
        nome = p["nome"]
        tipo = p.get("tipo", "str")
        obrigatorio = p.get("obrigatorio", False)
        padrao = p.get("padrao")
        opcoes = p.get("opcoes")
        desc = p.get("descricao", nome)
        if padrao is not None:
            dica = f" [padrão: {padrao}]"
        else:
            dica = "" if obrigatorio else " [opcional]"
        if opcoes:
            dica += f" ({'/'.join(map(str, opcoes))})"
        while True:
            bruto = input(f"  {desc}{dica}: ").strip()
            if not bruto:
                if padrao is not None:
                    params[nome] = padrao
                    break
                if obrigatorio:
                    print(cor("  Este parâmetro é obrigatório.", "33"))
                    continue
                break
            try:
                params[nome] = converter(bruto, tipo, opcoes)
                break
            except ValueError as e:
                print(cor(f"  Valor inválido: {e}", "33"))
    return params


def pedir_timeout(funcao: dict) -> float | None:
    if not funcao.get("usa_timeout"):
        return None
    padrao = funcao.get("timeout_padrao", TIMEOUT_PADRAO)
    while True:
        bruto = input(f"  Tempo limite em segundos [padrão: {padrao}]: ").strip()
        if not bruto:
            return padrao
        try:
            valor = float(bruto)
            if valor <= 0:
                raise ValueError
            return int(valor) if valor.is_integer() else valor
        except ValueError:
            print(cor("  Digite um número maior que zero.", "33"))


# --------------------------------------------------------------------------
# Execução protegida
# --------------------------------------------------------------------------
def normalizar(valor) -> dict:
    """Garante que o resultado tenha sempre o mesmo formato."""
    if not isinstance(valor, dict):
        return {
            "status": "erro", "saida": "", "codigo": None, "relatorio": None,
            "erro": f"o módulo devolveu {type(valor).__name__} em vez de um dict",
        }
    status = str(valor.get("status", "")).lower()
    erro = str(valor.get("erro") or "")
    if status not in ("ok", "erro"):
        aviso = f'campo "status" inválido ou ausente ({valor.get("status")!r}); esperado "ok" ou "erro"'
        erro = f"{erro}\n{aviso}" if erro else aviso
        status = "erro"
    return {
        "status": status,
        "saida": str(valor.get("saida") or ""),
        "erro": erro,
        "codigo": valor.get("codigo"),
        "relatorio": valor.get("relatorio"),
    }


def salvar_relatorio(m: Modulo, relatorio) -> str | None:
    """Relatório pode ser um caminho de arquivo existente ou o próprio texto."""
    if not relatorio:
        return None
    texto = str(relatorio)
    try:
        if "\n" not in texto and len(texto) < 400 and Path(texto).is_file():
            return texto
    except OSError:
        pass
    try:
        PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)
        selo = datetime.now().strftime("%Y%m%d_%H%M%S")
        seguro = re.sub(r"[^\w.-]", "_", m.nome)
        destino = PASTA_RELATORIOS / f"{seguro}_{selo}.txt"
        destino.write_text(texto, encoding="utf-8")
        return str(destino)
    except OSError as e:
        log.error("falha ao salvar relatório: %s", e)
        return None


def limitar(texto: str) -> list[str]:
    linhas = texto.replace("\r", "").rstrip().splitlines()
    if len(linhas) > MAX_LINHAS_PAINEL:
        resto = len(linhas) - MAX_LINHAS_PAINEL
        linhas = linhas[:MAX_LINHAS_PAINEL] + [f"... (+{resto} linhas; saída completa em logs/menu.log)"]
    return ["  " + l for l in linhas]


def mostrar_resultado(m: Modulo, titulo: str, res: dict, duracao: float, caminho_rel: str | None) -> None:
    ok = res["status"] == "ok"
    linhas = [f"Status: {'OK' if ok else 'ERRO'}", f"Duração: {duracao:.1f}s"]
    if res["codigo"] is not None:
        linhas.append(f"Código de retorno: {res['codigo']}")
    if res["saida"].strip():
        linhas += ["", "Saída:"] + limitar(res["saida"])
    if res["erro"].strip():
        linhas += ["", "O que deu errado / mensagens de erro:"] + limitar(res["erro"])
    if caminho_rel:
        linhas += ["", f"Relatório: {caminho_rel}"]
    painel(f"RESULTADO · {m.nome} · {titulo}", linhas, "32" if ok else "31")


def executar_funcao(m: Modulo, chave: str) -> None:
    f = m.funcoes[chave]
    titulo = f.get("titulo", chave)
    print()
    print(cor(f"▶ {m.nome} · {titulo}", "1"))
    if f.get("descricao"):
        print(cor(f"  {f['descricao']}", "90"))
    print(cor("  (Ctrl+C cancela)", "90"))
    try:
        params = pedir_parametros(f)
        timeout = pedir_timeout(f)
    except KeyboardInterrupt:
        print("\nCancelado.")
        return

    fila: queue.Queue = queue.Queue()

    def status(msg) -> None:
        fila.put((datetime.now(), str(msg)))

    caixa: dict = {}

    def alvo() -> None:
        try:
            caixa["valor"] = m.executar(chave, params, status, timeout)
        except (Exception, SystemExit) as e:
            caixa["excecao"] = e
            caixa["traceback"] = traceback.format_exc()

    def drenar() -> None:
        while True:
            try:
                momento, msg = fila.get_nowait()
            except queue.Empty:
                return
            imprimir_status(m, momento, msg)
            log.info("[%s] status: %s", m.nome, msg)

    log.info("[%s] executando %s params=%s timeout=%s", m.nome, chave, params, timeout)
    print()
    inicio = time.monotonic()
    limite = (timeout + TOLERANCIA) if timeout else None
    thread = threading.Thread(target=alvo, name=f"mod-{m.nome}", daemon=True)
    thread.start()

    motivo = None  # None | "timeout" | "interrompido"
    try:
        while thread.is_alive():
            drenar()
            if limite is not None and time.monotonic() - inicio > limite:
                motivo = "timeout"
                break
            thread.join(0.1)
    except KeyboardInterrupt:
        motivo = "interrompido"
    drenar()
    duracao = time.monotonic() - inicio

    if motivo == "timeout":
        res = normalizar({
            "status": "erro",
            "erro": (f"o módulo não respondeu dentro de {timeout}s (+{TOLERANCIA}s de tolerância). "
                     "A execução dele pode continuar em segundo plano até terminar."),
        })
    elif motivo == "interrompido":
        res = normalizar({
            "status": "erro",
            "erro": "interrompido pelo usuário (Ctrl+C). A execução do módulo pode continuar em segundo plano.",
        })
    elif "excecao" in caixa:
        res = normalizar({"status": "erro", "erro": resumo_excecao(caixa["excecao"])})
        log.error("[%s] exceção em %s:\n%s", m.nome, chave, caixa["traceback"])
    else:
        res = normalizar(caixa.get("valor"))

    caminho = salvar_relatorio(m, res["relatorio"])
    log.info("[%s] %s terminou: status=%s codigo=%s duracao=%.1fs relatorio=%s",
             m.nome, chave, res["status"], res["codigo"], duracao, caminho)
    if res["saida"].strip():
        log.info("[%s] saída completa:\n%s", m.nome, res["saida"])
    if res["erro"].strip():
        log.info("[%s] erro: %s", m.nome, res["erro"])

    print()
    mostrar_resultado(m, titulo, res, duracao, caminho)


def rodar_verificar(m: Modulo) -> None:
    caixa: dict = {}

    def alvo() -> None:
        try:
            caixa["valor"] = m.verificar()
        except (Exception, SystemExit) as e:
            caixa["erro"] = resumo_excecao(e)

    t = threading.Thread(target=alvo, daemon=True)
    t.start()
    t.join(ESPERA_VERIFICAR)

    if t.is_alive():
        linhas, cor_b = [f"verificar() não respondeu em {ESPERA_VERIFICAR}s."], "31"
    elif "erro" in caixa:
        linhas, cor_b = [f"verificar() falhou: {caixa['erro']}"], "31"
    else:
        v = caixa["valor"]
        ok, msg = (bool(v[0]), str(v[1])) if isinstance(v, tuple) and len(v) == 2 else (bool(v), "")
        linhas = ["Funcionando." if ok else "Não está funcionando."] + ([msg] if msg else [])
        cor_b = "32" if ok else "31"
    log.info("[%s] verificar: %s", m.nome, " | ".join(linhas))
    painel(f"VERIFICAÇÃO · {m.nome}", linhas, cor_b)


# --------------------------------------------------------------------------
# Menus
# --------------------------------------------------------------------------
def nome_grupo(nome: str) -> str:
    return nome.replace("_", " ").capitalize()


def agrupar_nivel(chaves: list[str], prefixo: list[str]) -> list[list]:
    """Itens do nível atual: ["funcao", chave, rótulo] ou ["grupo", nome, quantidade].
    Chaves como "portas.tcp" formam o grupo "portas" com a função "tcp"."""
    itens: list[list] = []
    grupos: dict[str, list] = {}
    n = len(prefixo)
    for chave in chaves:
        partes = chave.split(".")
        if partes[:n] != prefixo:
            continue
        resto = partes[n:]
        if not resto:
            continue
        if len(resto) == 1:
            itens.append(["funcao", chave, resto[0]])
        else:
            g = grupos.get(resto[0])
            if g is None:
                g = grupos[resto[0]] = ["grupo", resto[0], 0]
                itens.append(g)
            g[2] += 1
    return itens


def menu_modulo(m: Modulo) -> None:
    chaves = list(m.funcoes)
    prefixo: list[str] = []
    while True:
        print()
        topo = not prefixo
        itens = agrupar_nivel(chaves, prefixo)
        linhas: list[str] = []
        if topo:
            linhas.append(f"Ferramenta: {m.nome}   Versão: {m.versao}   "
                          f"Arquivo: {m.arquivo}{'/' if m.pacote else ''}")
            if m.meta.get("descricao"):
                linhas.append(str(m.meta["descricao"]))
        else:
            linhas.append("Grupo: " + " › ".join(nome_grupo(p) for p in prefixo))
        linhas.append("")
        for i, (tipo, a, b) in enumerate(itens, 1):
            if tipo == "grupo":
                linhas.append(f"[{i}] {nome_grupo(a)} >   ({b} {'função' if b == 1 else 'funções'})")
            else:
                f = m.funcoes[a]
                extra = "  (tempo limite)" if f.get("usa_timeout") else ""
                linhas.append(f"[{i}] {f.get('titulo', b)}{extra}")
                if f.get("descricao"):
                    linhas.append(f"      {f['descricao']}")
        linhas.append("")
        if topo and m.verificar:
            linhas.append("[v] Verificar se o módulo está funcionando")
        if topo and m.docs:
            linhas.append("[d] Documentação")
        linhas.append("[0] Voltar")
        painel("MÓDULO · " + m.nome + "".join(" › " + nome_grupo(p) for p in prefixo), linhas)

        esc = ler("Escolha").lower()
        if esc == "0":
            if prefixo:
                prefixo.pop()
                continue
            return
        if esc == "v" and topo and m.verificar:
            rodar_verificar(m)
        elif esc == "d" and topo and m.docs:
            painel(f"DOCUMENTAÇÃO · {m.nome}", textwrap.dedent(m.docs).strip().splitlines())
        elif esc.isdigit() and 1 <= int(esc) <= len(itens):
            tipo, a, _ = itens[int(esc) - 1]
            if tipo == "grupo":
                prefixo.append(a)
            else:
                executar_funcao(m, a)
        else:
            print(cor("Opção inválida.", "33"))


def mostrar_rejeitados(rejeitados: list[Rejeitado]) -> None:
    linhas: list[str] = []
    for r in rejeitados:
        linhas += [f"{r.arquivo}{'/' if r.pacote else ''}", f"  motivo: {r.motivo}", ""]
    painel("MÓDULOS REJEITADOS", linhas[:-1], "31")


def menu_principal(pasta: Path) -> None:
    while True:
        modulos, rejeitados = descobrir(pasta)   # varre de novo a cada volta: acopla módulos novos
        print()
        linhas = [f"Pasta de módulos: {pasta}", ""]
        if modulos:
            for i, m in enumerate(modulos, 1):
                desc = f"  {m.meta['descricao']}" if m.meta.get("descricao") else ""
                linhas.append(f"[{i}] {m.nome} v{m.versao}{desc}")
        else:
            linhas.append("Nenhum módulo conectado.")
        linhas.append("")
        if rejeitados:
            linhas.append(f"[r] Ver módulos rejeitados ({len(rejeitados)})")
        linhas += ["[Enter] Atualizar lista", "[0] Sair"]
        painel("KALI TOOLBOX", linhas)

        esc = ler("Escolha").lower()
        if esc == "0":
            print("Até logo.")
            return
        if esc == "r" and rejeitados:
            mostrar_rejeitados(rejeitados)
        elif esc.isdigit() and 1 <= int(esc) <= len(modulos):
            menu_modulo(modulos[int(esc) - 1])
        elif esc:
            print(cor("Opção inválida.", "33"))


def configurar_log() -> None:
    try:
        PASTA_LOGS.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(PASTA_LOGS / "menu.log", encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    except OSError as e:
        print(cor(f"Aviso: não foi possível gravar o log ({e}).", "33"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Kali Toolbox - menu orquestrador de módulos")
    ap.add_argument("--pasta", type=Path, default=PASTA_MODULOS,
                    help="pasta onde ficam os módulos (padrão: ./modulos)")
    args = ap.parse_args()
    configurar_log()
    try:
        menu_principal(args.pasta.resolve())
    except (KeyboardInterrupt, EOFError):
        print("\nAté logo.")


if __name__ == "__main__":
    main()