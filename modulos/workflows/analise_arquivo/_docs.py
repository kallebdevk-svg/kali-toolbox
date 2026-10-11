DOCS = """
O QUE ESTE WORKFLOW FAZ:
  Analisa um arquivo qualquer (documento, executável, imagem, dump) usando
  várias ferramentas em sequência, e devolve um relatório agregado. O
  objetivo é servir como primeiro passo em forense digital ou engenharia
  reversa: descobrir o que o arquivo realmente é, o que tem dentro, e
  coletar hashes e metadados antes de investigar mais a fundo.

ETAPAS EXECUTADAS:

  file       Identifica o tipo real do arquivo olhando o cabeçalho. Não
             confia na extensão. Um arquivo ".pdf" pode ser, na verdade,
             um zip com PDF renomeado.

  hashes     Calcula MD5, SHA-1 e SHA-256. Serve como impressão digital
             para procurar o arquivo em bases públicas (VirusTotal, etc.)
             e para garantir integridade durante a investigação.

  exiftool   Extrai metadados embutidos: autor, software que gerou, datas,
             GPS em fotos, revisões em documentos, etc. Metadados são
             frequentemente esquecidos e revelam informação útil.

  strings    Extrai sequências de texto legível (6+ caracteres) do arquivo.
             URLs, e-mails, caminhos de arquivo, mensagens de erro e nomes
             de função aparecem aqui mesmo em binários compilados.

  binwalk    Analisa a estrutura e detecta arquivos embutidos: arquivos
             comprimidos, imagens dentro de PDFs, executáveis dentro de
             documentos. Não extrai nada — só mapeia o que existe.

COMPORTAMENTO:

  Tolerante. Se uma etapa falha de forma determinística (arquivo não existe,
  sem permissão), ela é marcada como falhou e o workflow segue para a
  próxima. Se falha de forma transiente (timeout, lock), tenta de novo até
  3 vezes antes de desistir. Se a ferramenta não está instalada, a etapa
  é marcada como ausente e o resto segue normalmente.

  Cada etapa narra seu estado ao vivo: "iniciando file", "file concluído",
  "strings falhou, tentando novamente (1/3)". Você vê o que está
  acontecendo sem precisar adivinhar.

COMO LER O RELATÓRIO:

  Símbolos do resumo:

    [✓] ok        a etapa rodou e produziu resultado
    [!] parcial   a etapa rodou mas não encontrou o esperado
    [✗] falhou    a etapa rodou e retornou erro
    [-] pulada    o usuário pulou ou a ferramenta está ausente

  O painel mostra o resumo e, se "detalhado" estiver ligado, os detalhes
  de cada etapa. O arquivo de relatório salvo pelo menu sempre contém a
  saída completa de cada ferramenta, mesmo quando o painel corta.

USO TÍPICO:

  1. Baixou um arquivo suspeito? Rode "Análise completa" nele.
  2. O arquivo é grande e você só quer saber o tipo? Rode "Análise rápida".
  3. Quer rodar só o binwalk para ver a estrutura? Rode "Rodar uma etapa só".

REFERÊNCIAS:

  - man file, man sha256sum, man exiftool, man strings, man binwalk
  - https://exiftool.org/
  - https://github.com/ReFirmLabs/binwalk
"""
