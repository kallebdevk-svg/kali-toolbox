"""FUNCOES do workflow de análise de arquivo."""

FUNCOES = {
    "completa": {
        "titulo": "Análise completa",
        "descricao": "Roda todas as etapas: file, hashes, exiftool, strings, binwalk",
        "usa_timeout": True,
        "timeout_padrao": 600,
        "parametros": [
            {"nome": "arquivo",
             "descricao": "Caminho do arquivo a analisar",
             "tipo": "str", "obrigatorio": True},
            {"nome": "detalhado",
             "descricao": "Incluir detalhes de cada etapa no painel (o arquivo de relatório sempre tem)",
             "tipo": "bool", "padrao": False},
            {"nome": "pular",
             "descricao": "Etapas a pular, separadas por vírgula (ex: strings,binwalk; vazio = rodar tudo)",
             "tipo": "str", "padrao": ""},
        ],
    },
    "rapida": {
        "titulo": "Análise rápida (sem binwalk)",
        "descricao": "file, hashes e exiftool — não roda strings nem binwalk",
        "usa_timeout": True,
        "timeout_padrao": 120,
        "parametros": [
            {"nome": "arquivo",
             "descricao": "Caminho do arquivo a analisar",
             "tipo": "str", "obrigatorio": True},
            {"nome": "detalhado",
             "descricao": "Incluir detalhes no painel",
             "tipo": "bool", "padrao": False},
        ],
    },
    "etapa_unica": {
        "titulo": "Rodar uma etapa só",
        "descricao": "Escolhe qual das etapas rodar isoladamente",
        "usa_timeout": True,
        "timeout_padrao": 300,
        "parametros": [
            {"nome": "arquivo",
             "descricao": "Caminho do arquivo",
             "tipo": "str", "obrigatorio": True},
            {"nome": "etapa",
             "descricao": "Qual etapa rodar",
             "tipo": "str", "padrao": "file",
             "opcoes": ["file", "hashes", "exiftool", "strings", "binwalk"]},
            {"nome": "detalhado",
             "descricao": "Incluir detalhes no painel",
             "tipo": "bool", "padrao": True},
        ],
    },
}
