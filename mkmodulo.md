# Como criar um módulo para o Kali Toolbox

Este documento descreve tudo o que um módulo precisa ter para ser reconhecido pelo menu e como ele conversa com ele.

## 1. A ideia

- O **menu não conhece nenhuma ferramenta**. Ele só procura módulos na pasta, mostra os submenus que cada módulo declara, pergunta os parâmetros e manda de volta para o módulo executar.
- Cada módulo é **um arquivo `.py`** e cuida sozinho do funcionamento da sua ferramenta.
- Para adicionar um módulo, basta **colocar o arquivo na pasta de módulos**. Nenhuma linha do menu muda. O menu varre a pasta toda vez que a tela principal é exibida, então um módulo novo aparece sem reiniciar.

Regras da varredura:

- A pasta é varrida recursivamente (`modulos/network/ping.py` funciona). Pastas comuns servem só de categoria.
- Um módulo pode ser **um arquivo `.py`** ou **uma pasta com `__init__.py`** (veja a seção 8).
- Arquivos e pastas que **começam com `_`** (ou `.`) são ignorados (use `_rascunho.py` para o que ainda não está pronto).
- A pasta padrão é `./modulos`. Para usar outra: `python3 menu.py --pasta /caminho/dos/modulos`.

## 2. O que é obrigatório

Um módulo só é reconhecido se tiver os **três** itens abaixo. Se faltar algum, ele vai para a lista de **rejeitados**, com o motivo exato.

### 2.1 `META` — o cabeçalho

Um `dict` que identifica o módulo.

```python
META = {
    "modulo": True,          # obrigatório: marca o arquivo como módulo
    "ferramenta": "ping",    # obrigatório: nome da ferramenta (aparece no menu e no log)
    "versao": "1.0",         # obrigatório: versão do módulo
    "descricao": "...",      # opcional: frase curta mostrada no menu
    "categoria": "network",  # opcional
    "ordem": ["a", "b.c"],   # opcional: ordem de exibição das funções (veja 2.2.2)
}
```

### 2.2 `FUNCOES` — o que vira submenu

Um `dict` em que cada chave é o identificador de uma função e o valor descreve como o menu deve apresentá-la. **O módulo declara, o menu formata.**

```python
FUNCOES = {
    "ping_host": {
        "titulo": "Pingar um host",              # texto do item no submenu
        "descricao": "Envia pacotes ICMP",       # opcional: linha de apoio
        "usa_timeout": True,                     # opcional: se True, o menu pergunta o tempo limite
        "timeout_padrao": 15,                    # opcional: segundos sugeridos
        "parametros": [                          # opcional: o que o menu deve perguntar
            {"nome": "host", "descricao": "Host de destino",
             "tipo": "str", "obrigatorio": True},
            {"nome": "quantidade", "descricao": "Pacotes",
             "tipo": "int", "padrao": 4},
        ],
    },
}
```

Campos de cada parâmetro:

| Campo | Obrigatório | Significado |
|---|---|---|
| `nome` | sim | chave com que o valor chega em `parametros` |
| `descricao` | não | texto da pergunta |
| `tipo` | não | `str` (padrão), `int`, `float` ou `bool` |
| `obrigatorio` | não | se `True`, o menu insiste até receber um valor |
| `padrao` | não | valor usado se o usuário apertar Enter |
| `opcoes` | não | lista de valores aceitos |

O menu converte o tipo antes de entregar. Se o usuário digitar algo inválido, ele pergunta de novo.

#### 2.2.1 Grupos (submenus) com ponto na chave

Quando o módulo tem muitas funções, use um **ponto na chave** para agrupá-las. O menu cria um submenu para cada prefixo:

```python
FUNCOES = {
    "portas.tcp":          {"titulo": "Scan TCP"},
    "portas.udp":          {"titulo": "Scan UDP"},
    "portas.avancado.syn": {"titulo": "Scan SYN"},   # grupos podem ter subgrupos
    "servico.versao":      {"titulo": "Detectar versão"},
    "sobre":               {"titulo": "Sobre"},       # sem ponto: fica no nível principal
}
```

No menu aparece `Portas >`, `Servico >` e `Sobre`. Entrar no grupo mostra só as funções dele, e `[0] Voltar` sobe um nível.

- A chave **completa** (`"portas.tcp"`) é o que chega ao `executar` em `funcao`.
- O nome do grupo vem do prefixo (`_` vira espaço, primeira letra maiúscula). Como a chave é texto simples, evite acentos no prefixo.
- Partes vazias (`"a..b"`, `".x"`) são rejeitadas.
- Quem não usa ponto não muda nada: a lista continua plana.

#### 2.2.2 Ordem de exibição (`META["ordem"]`)

Por padrão o menu mostra as funções na ordem do dicionário. Para fixar outra ordem (útil quando as funções vêm de arquivos diferentes), liste as chaves em `META["ordem"]`:

```python
META = {..., "ordem": ["servico.versao", "portas.tcp", "portas.udp"]}
```

As chaves listadas vêm primeiro, na ordem dada; as que não estão na lista vêm depois, na ordem do dicionário. Uma chave que não existe em `FUNCOES` é ignorada (e registrada no log). Os grupos aparecem na posição da primeira função deles. `ordem` precisa ser uma lista de textos, senão o módulo é rejeitado.

### 2.3 `executar` — a função que faz o trabalho

```python
def executar(funcao, parametros, status, timeout):
    ...
    return {"status": "ok", "saida": "...", "erro": "", "codigo": 0, "relatorio": None}
```

Argumentos que o menu envia:

| Argumento | O que é |
|---|---|
| `funcao` | a chave escolhida em `FUNCOES` (ex.: `"ping_host"`) |
| `parametros` | `dict` com os valores já convertidos (ex.: `{"host": "127.0.0.1", "quantidade": 4}`) |
| `status` | função para mandar mensagens de progresso ao vivo (veja a seção 4) |
| `timeout` | tempo limite em segundos escolhido no menu, ou `None` se `usa_timeout` for falso |

Retorno (sempre um `dict`):

| Chave | Significado |
|---|---|
| `status` | **obrigatório**: `"ok"` ou `"erro"` |
| `saida` | texto da saída da ferramenta |
| `erro` | mensagem de erro, se houver |
| `codigo` | código de retorno do processo, se houver |
| `relatorio` | opcional: texto do relatório **ou** caminho de um arquivo já gerado |

Se o retorno não for um `dict`, ou o `status` for inválido, o menu trata como erro e explica o motivo.

## 3. O que é opcional

O menu usa estes itens **se existirem** e simplesmente não mostra a opção se não existirem.

### `verificar()` — checagem de funcionamento

```python
def verificar():
    return True, "ping encontrado em /usr/bin/ping"   # ou apenas True/False
```

Se existir, o submenu ganha a opção **[v]**. Pode devolver `bool` ou `(bool, mensagem)`. O menu espera no máximo 15 segundos.

### `DOCS` — documentação embutida

Um texto (string). Se existir, o submenu ganha a opção **[d]**. Sugestão de conteúdo: o que a ferramenta faz, como o módulo a chama por baixo, exemplos e referências.

## 4. Log ao vivo com `status()`

Chame `status("frase curta")` a cada etapa relevante. O menu coloca o prefixo com nome e versão do módulo e mostra na hora:

```
14:02:11 [nmap] [v1.01] ouvindo através da interface wlan0
```

Boas práticas:

- Uma frase curta e objetiva, descrevendo o que está acontecendo **agora**.
- Não precisa repetir o nome nem a versão, o menu já coloca.
- Se o módulo nunca chamar `status`, nada é mostrado durante a execução e o resultado aparece normalmente no final.

## 5. Timeout, thread e proteção contra erros

O menu roda `executar` em **uma thread separada**, então a tela continua viva e o log aparece em tempo real.

**Erros (exceções):** o menu já envolve a chamada em `try/except`. O módulo não é obrigado a ter o próprio, mas pode tratar erros que ele sabe explicar melhor. Se uma exceção escapar, o menu mostra o tipo, a mensagem e **onde** aconteceu (arquivo, linha e função), e grava o traceback completo em `logs/menu.log`. Isso inclui `sys.exit()`: ele é capturado e não encerra o menu.

**Tempo limite:** o valor escolhido no menu chega em `timeout`. **Use-o no `subprocess.run(..., timeout=timeout)`**. É assim que a ferramenta externa realmente é encerrada.

Atenção: o Python não consegue matar uma thread à força. Se o módulo travar sem usar o timeout (por exemplo, um `while True`), o menu desiste de esperar após `timeout + 5s`, avisa o que aconteceu e volta ao normal, mas aquela thread pode continuar rodando em segundo plano. Por isso o timeout no `subprocess` é o mecanismo principal.

## 6. Relatório

Se o módulo devolver `relatorio`, o menu cuida do resto:

- se for um **caminho de arquivo existente**, o menu apenas mostra o caminho;
- se for **texto**, o menu salva uma cópia em `relatorios/<ferramenta>_<data>.txt` e mostra o caminho.

## 7. Boas práticas

- **Não use `print()` nem `input()`** dentro do módulo. O terminal é do menu. Para mostrar progresso use `status()`; para pedir dados, declare `parametros`.
- **Não use `shell=True`.** Monte o comando como lista: `["ping", "-c", "4", host]`.
- **Valide as entradas** antes de montar o comando (por exemplo, rejeite um host que comece com `-`, para não virar opção da ferramenta).
- **Sempre passe `timeout`** ao `subprocess.run`.
- **Não use `sys.exit()`** nem altere o diretório de trabalho do programa.
- Verifique com `shutil.which("ferramenta")` se o binário existe e devolva uma mensagem clara se não existir.
- Só rode ferramentas contra alvos seus ou com autorização. O uso é acadêmico e de laboratório.

## 8. Módulo em pacote (pasta)

Para módulos grandes, use uma **pasta com `__init__.py`**. O `__init__.py` guarda `META`, `FUNCOES`, `executar` (e, se quiser, `verificar` e `DOCS`); o resto do código fica em arquivos separados:

```
modulos/
  nmap/
    __init__.py      <- contrato do módulo (é este arquivo que o menu lê)
    _core.py         <- código de apoio
    _portas.py
```

```python
# nmap/__init__.py
from ._core import rodar_scan      # import relativo: use o ponto

META = {"modulo": True, "ferramenta": "nmap", "versao": "1.0"}
...
```

Regras:

- A pasta inteira conta como **um único módulo**. O menu não entra nela procurando outros.
- Os arquivos de apoio **devem começar com `_`**, e os imports entre eles devem ser **relativos** (`from ._core import ...`). Não precisa mexer em `sys.path`.
- Se uma pasta **sem** `__init__.py` estiver em `modulos/`, ela é tratada como categoria. Por isso não coloque `__init__.py` em pastas que só agrupam módulos.
- Ao atualizar a lista, o menu recarrega o pacote e os arquivos de apoio, então edições aparecem sem reiniciar.
- Nas mensagens de rejeição o pacote aparece com `/` no final (ex.: `nmap/`), e erros de sintaxe indicam o arquivo exato.

## 9. Modelo para copiar

Salve como `modulos/minha_ferramenta.py` e ajuste. (Um arquivo `_modelo.py` com este conteúdo é ignorado pelo menu.)

```python
"""Módulo para <ferramenta>."""
import shutil
import subprocess

META = {
    "modulo": True,
    "ferramenta": "minha_ferramenta",
    "versao": "1.0",
    "descricao": "O que este módulo faz, em uma frase",
}

FUNCOES = {
    "rodar": {
        "titulo": "Rodar a ferramenta",
        "descricao": "Explica a função",
        "usa_timeout": True,
        "timeout_padrao": 30,
        "parametros": [
            {"nome": "alvo", "descricao": "Alvo", "tipo": "str", "obrigatorio": True},
        ],
    },
}

DOCS = """
O que faz:
Como funciona por baixo:
Exemplos:
Referências:
"""


def verificar():
    if shutil.which("minha_ferramenta"):
        return True, "binário encontrado"
    return False, "binário não instalado"


def executar(funcao, parametros, status, timeout):
    if funcao != "rodar":
        return {"status": "erro", "saida": "", "erro": f"função desconhecida: {funcao}", "codigo": None}

    alvo = parametros["alvo"]
    status(f"executando contra {alvo}")
    try:
        p = subprocess.run(["minha_ferramenta", alvo],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "erro", "saida": "", "codigo": None,
                "erro": f"excedeu o tempo limite de {timeout}s"}

    status("processando o resultado")
    return {
        "status": "ok" if p.returncode == 0 else "erro",
        "saida": p.stdout,
        "erro": p.stderr,
        "codigo": p.returncode,
        "relatorio": p.stdout,
    }
```

## 10. Por que um módulo é rejeitado

A lista de rejeitados (opção **[r]** no menu principal) mostra o arquivo e o motivo. Os mais comuns:

| Mensagem | Causa |
|---|---|
| `erro de sintaxe na linha N` | o arquivo tem erro de Python |
| `erro ao importar: ...` | algo falhou ao carregar (import inexistente, exceção no topo do arquivo) |
| `cabeçalho META ausente ou não é um dict` | falta o `META` |
| `META["modulo"] precisa ser True` | faltou a marca de módulo |
| `META["ferramenta"] ausente ou vazio` | falta o nome da ferramenta |
| `META["versao"] ausente ou vazio` | falta a versão |
| `FUNCOES ausente, vazio ou não é um dict` | o menu não teria o que mostrar |
| `função executar ausente` | o menu não teria como mandar comandos |
| `FUNCOES: chave inválida ...` | chave que não é texto, vazia ou com parte vazia entre pontos |
| `META["ordem"] precisa ser uma lista de chaves de FUNCOES` | `ordem` com tipo errado |
| `verificar existe mas não é uma função` / `DOCS existe mas não é texto` | item opcional com tipo errado |

## 11. Checklist

- [ ] O arquivo está na pasta de módulos e o nome não começa com `_`
- [ ] `META` tem `modulo: True`, `ferramenta` e `versao`
- [ ] `FUNCOES` descreve cada função, seus parâmetros e se usa timeout
- [ ] `executar(funcao, parametros, status, timeout)` devolve sempre um `dict` com `status`
- [ ] O `timeout` é passado ao `subprocess.run`
- [ ] Nenhum `print`, `input`, `shell=True` ou `sys.exit`
- [ ] Se for pacote: contrato no `__init__.py`, apoio em arquivos `_*.py` com import relativo
- [ ] (opcional) `verificar` e `DOCS`