DOCS = """
O QUE ESTE WORKFLOW FAZ:
  Analisa um arquivo de firmware (de roteador, câmera IP, dispositivo IoT)
  em quatro etapas encadeadas: identificação, mapeamento de estrutura,
  extração e análise dos arquivos extraídos. O objetivo é chegar o mais
  longe possível na investigação sem intervenção manual.

ETAPAS E DEPENDÊNCIAS:

  1. identificacao
     Roda file, md5sum e sha256sum. Não depende de nada, sempre roda.

  2. estrutura
     Roda binwalk sem -e, só mapeia as assinaturas. Também sempre roda.

  3. extracao
     Roda binwalk -e num diretório isolado. SÓ RODA se a etapa 2
     encontrou pelo menos uma assinatura. Firmware sem estrutura
     reconhecível não é extraído.

  4. pos_processamento
     Analisa o que foi extraído: conta binários ELF, procura por
     arquivos sensíveis (chaves, hashes de senha, certificados) e roda
     strings nos ELFs procurando URLs, e-mails, credenciais e IPs.
     SÓ RODA se a etapa 3 extraiu algo.

DIRETÓRIO DE TRABALHO:

  Cada execução cria /tmp/workflow_firmware_<timestamp>/ e extrai tudo
  lá. Nada suja o diretório do menu. O caminho aparece no relatório,
  então você pode inspecionar o resultado manualmente depois.

  A extração é pulada se houver menos de 200 MB livres em /tmp, para
  não encher o disco em firmware grande.

SUMÁRIO EXECUTIVO:

  O relatório começa com um sumário dos achados mais importantes:
  tipo do arquivo, hashes, quantas estruturas embutidas, quantos
  binários ELF, se achou arquivos sensíveis e credenciais. A parte
  de "Etapas" vem em seguida, com o estado de cada uma.

REFERÊNCIAS:

  - man binwalk
  - https://github.com/ReFirmLabs/binwalk/wiki
  - https://github.com/firmware-analysis-toolkit
"""
