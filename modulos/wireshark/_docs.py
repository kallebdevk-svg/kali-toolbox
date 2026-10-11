DOCS = """
O QUE É O WIRESHARK:
  Wireshark é o analisador de protocolos de rede mais usado no mundo.
  Ele captura tráfego em tempo real e permite inspecionar pacote por
  pacote, com decodificação de centenas de protocolos. A suíte inclui
  várias ferramentas de linha de comando, das quais as duas principais
  são o tshark (análise e captura) e o dumpcap (captura pura).

FERRAMENTAS DA SUÍTE:

  tshark    Versão de terminal do Wireshark. Captura pacotes ao vivo,
            lê arquivos .pcap/.pcapng, aplica filtros de captura (BPF)
            e filtros de exibição (Wireshark display filter), extrai
            campos específicos e gera estatísticas.

  dumpcap   Ferramenta de captura pura. Escreve pacotes em arquivo sem
            decodificar. É o motor de captura usado internamente pelo
            Wireshark e pelo tshark.

  editcap   Utilitário para manipular arquivos de captura: converter
            entre formatos (pcap ↔ pcapng), dividir em vários arquivos,
            remover pacotes duplicados, ajustar timestamps.

  capinfos  Mostra metadados de um arquivo de captura (duração, número
            de pacotes, tamanho, taxas, etc.).

  mergecap  Junta vários arquivos de captura em um só, ordenando por
            timestamp.

DOIS TIPOS DE FILTRO (importante):

  1. Filtro de CAPTURA (BPF) — aplicado com -f. Usa a sintaxe da libpcap
     (mesma do tcpdump). Só os pacotes que casam são capturados. Exemplos:
       port 80 or port 443
       host 10.0.0.1
       not port 22

  2. Filtro de EXIBIÇÃO (Wireshark) — aplicado com -Y. Usa a sintaxe
     do Wireshark. Mais poderoso, pode filtrar por qualquer campo de
     qualquer protocolo. Exemplos:
       http
       ip.addr == 192.168.1.50
       tcp.flags.reset == 1
       dns.flags.response == 0

FLUXO TÍPICO DE ANÁLISE:

  1. tshark -D                        → lista interfaces
  2. tshark -i eth0 -c 100            → captura 100 pacotes
  3. tshark -i eth0 -f 'port 80' -w cap.pcapng  → salva só HTTP
  4. tshark -r cap.pcapng -Y 'http'   → filtra HTTP do arquivo
  5. tshark -r cap.pcapng -T fields -e ip.src -e ip.dst -e tcp.port
  6. tshark -r cap.pcapng -z io,phs   → hierarquia de protocolos

CAMPOS MAIS USADOS EM -T fields:

  frame.number       Número do frame
  frame.time         Timestamp
  frame.len          Tamanho do frame em bytes
  ip.src / ip.dst    IP de origem / destino
  ip.proto           Número do protocolo IP
  tcp.srcport / tcp.dstport   Portas TCP
  udp.srcport / udp.dstport   Portas UDP
  http.request.method         Método HTTP (GET, POST, ...)
  http.host          Host HTTP
  http.request.uri   URI requisitada
  dns.qry.name       Nome consultado no DNS
  tls.handshake.extensions_server_name   SNI em TLS

REFERÊNCIAS:
  - Documentação: https://www.wireshark.org/docs/
  - Manual do tshark: https://www.wireshark.org/docs/man-pages/tshark.html
  - Manual do dumpcap: https://www.wireshark.org/docs/man-pages/dumpcap.html
  - Display filter reference: https://www.wireshark.org/docs/dfref/
  - Wiki do Wireshark: https://wiki.wireshark.org/

ATENÇÃO: capturar tráfego de rede em que você não é o administrador ou
não tem autorização pode ser ilegal. Use apenas em redes próprias ou
com consentimento explícito.
"""