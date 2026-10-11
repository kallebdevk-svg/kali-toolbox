"""FUNCOES do workflow de análise de firmware."""

FUNCOES = {
    "completa": {
        "titulo": "Análise completa de firmware",
        "descricao": "Identificação, estrutura, extração e análise dos arquivos extraídos",
        "usa_timeout": True,
        "timeout_padrao": 1800,
        "parametros": [
            {"nome": "arquivo",
             "descricao": "Caminho do firmware (.bin, .img, .trx, etc.)",
             "tipo": "str", "obrigatorio": True},
            {"nome": "procurar",
             "descricao": "Padrões regex extras a procurar nos arquivos extraídos, separados por vírgula (ex: '\\.conf$,admin,senha.*txt'; vazio = só o padrão fixo do workflow)",
             "tipo": "str", "padrao": ""},
            {"nome": "detalhado",
             "descricao": "Incluir todos os detalhes no painel",
             "tipo": "bool", "padrao": False},
        ],
    },
    "estrutura_simples": {
        "titulo": "Só identificar e mapear estrutura",
        "descricao": "Não extrai nada — só file, hashes e binwalk",
        "usa_timeout": True,
        "timeout_padrao": 300,
        "parametros": [
            {"nome": "arquivo",
             "descricao": "Caminho do firmware",
             "tipo": "str", "obrigatorio": True},
            {"nome": "detalhado",
             "descricao": "Incluir todos os detalhes no painel",
             "tipo": "bool", "padrao": True},
        ],
    },
}
