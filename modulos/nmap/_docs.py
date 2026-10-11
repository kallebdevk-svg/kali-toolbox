DOCS = """
O QUE É O NMAP:
  Nmap (Network Mapper) é um scanner de rede de código aberto usado para
  descoberta de hosts e serviços, mapeamento de rede e auditoria de
  segurança. Ele envia pacotes especialmente construídos aos alvos e
  analisa as respostas para determinar quais hosts estão ativos, quais
  portas estão abertas, quais serviços e versões estão rodando, qual
  sistema operacional está em uso e quais filtros de firewall existem
  no caminho. É uma das ferramentas mais antigas e amplamente usadas em
  segurança ofensiva e defensiva.

COMO O NMAP FUNCIONA POR DENTRO:
  O nmap opera em quatro fases principais, executadas nesta ordem:

  1. Descoberta de host (host discovery)
     Determina quais alvos estão ativos antes de escaneá-los. Por padrão,
     envia um ICMP Echo Request (ping) e um pacote TCP ACK para a porta 80.
     Em rede local, usa ARP, que é mais rápido e confiável. Opções como
     -Pn desativam essa fase e assumem que todos os alvos estão ativos.

  2. Scan de portas (port scanning)
     Determina o estado de cada porta (aberta, fechada, filtrada). A técnica
     varia conforme o tipo de pacote enviado. Cada técnica explora uma
     característica diferente do protocolo TCP, UDP ou SCTP para inferir o
     estado da porta.

  3. Detecção de serviço e versão (version detection)
     Após encontrar portas abertas, o nmap envia sondas específicas para
     identificar qual aplicação e versão estão rodando. Usa o banco
     nmap-service-probes, com mais de 6.500 assinaturas para 650+ protocolos.

  4. Detecção de sistema operacional (OS detection)
     Analisa peculiaridades da pilha TCP/IP do alvo (como valores de TTL,
     tamanho de janela, opções TCP) para inferir o sistema operacional.
     Não é infalível: depende de como o sistema operacional implementa a
     pilha, e pode ser enganado por firewalls ou NAT.

  Os scripts NSE (Nmap Scripting Engine) podem rodar em qualquer uma dessas
  fases: antes do scan (prerule), durante o scan de host (host), contra
  serviços específicos (service) ou após o scan (postrule).

TÉCNICAS DE DESCOBERTA DE HOSTS:

  -sn               Desativa o scan de portas. Só faz descoberta de hosts.

  -Pn               Desativa a descoberta. Assume todos os alvos ativos.

  -PS <portas>      Envia pacote TCP SYN para as portas indicadas.
                    Resposta SYN/ACK = host ativo. RST = host ativo mas
                    porta fechada. Sem resposta = host inativo ou filtrado.

  -PA <portas>      Envia pacote TCP ACK. Resposta RST = host ativo.
                    Útil para atravessar firewalls que bloqueiam SYN.

  -PU <portas>      Envia pacote UDP vazio. ICMP Port Unreachable = host
                    ativo. Porta padrão: 31338. Funciona onde TCP é filtrado.

  -PE               Envia ICMP Echo Request (ping clássico).

  -PP               Envia ICMP Timestamp Request.

  -PM               Envia ICMP Address Mask Request.

  -PO <protocolos>  Envia pacotes de protocolo IP específicos.

  -PR               ARP scan. Só funciona em rede local. Mais rápido
                    e confiável que qualquer outro método. É o padrão
                    automático em rede local.

  --disable-arp-ping  Desativa o ARP e usa os outros métodos mesmo em rede local.

  As opções podem ser combinadas: -PS22,80 -PA80 -PE envia SYN para 22 e 80,
  ACK para 80, e ICMP Echo Request. Quanto mais sondas, maior a chance de
  atravessar firewalls.

TÉCNICAS DE SCAN DE PORTAS (TCP):

  -sS   SYN scan ("half-open", "stealth"). Envia SYN. Se recebe SYN/ACK,
        a porta está aberta (mas o nmap envia RST em vez de completar a
        conexão). Se recebe RST, fechada. Se não recebe nada, filtrada.
        É o scan padrão do nmap quando executado como root, por ser rápido
        e relativamente discreto (não completa a conexão TCP).

  -sT   Connect scan. Usa a chamada de sistema connect() do sistema
        operacional para completar a conexão TCP de três vias. Funciona
        sem privilégio de root, mas é mais lento e deixa registro nos logs
        do alvo (a conexão é completada e depois encerrada).

  -sA   ACK scan. Envia pacote ACK. Não determina portas abertas ou
        fechadas — determina se a porta é filtrada ou não filtrada.
        Se receber RST, a porta não é filtrada. Se não receber nada,
        é filtrada. Útil para mapear regras de firewall.

  -sW   Window scan. Semelhante ao ACK, mas analisa o campo de tamanho de
        janela TCP dos pacotes RST para distinguir portas abertas de
        fechadas em alguns sistemas. Não é confiável em todos os alvos.

  -sN   Null scan. Envia pacote TCP sem nenhuma flag ligada (todos os
        bits zero). Em sistemas que seguem a RFC 793, portas fechadas
        respondem com RST; portas abertas ignoram. Não funciona no Windows.

  -sF   FIN scan. Envia pacote com a flag FIN ligada. Mesma lógica do Null.

  -sX   Xmas scan. Envia pacote com FIN, PSH e URG ligadas ("árvore de
        Natal"). Mesma lógica do Null e FIN.

  -sM   Maimon scan. Envia pacote FIN/ACK. Espera RST de portas abertas
        (comportamento de alguns sistemas BSD antigos). Pouco usado hoje.

  --scanflags <flags>  Permite definir manualmente as flags TCP do scan.
        Ex: --scanflags URGACKPSH. Cobre casos não previstos pelas técnicas fixas.

TÉCNICAS DE SCAN DE PORTAS (UDP E SCTP):

  -sU   UDP scan. Envia pacote UDP vazio para cada porta. Se receber ICMP
        Port Unreachable, a porta está fechada. Se receber resposta UDP,
        a porta está aberta. Se não receber nada, open|filtered (ambíguo).
        É muito lento e exige root. Recomendado usar com -sS em paralelo.

  -sY   SCTP INIT scan. Envia pacote SCTP INIT. Resposta INIT-ACK = aberta.
        Resposta ABORT = fechada. Sem resposta = filtrada. Exige root.

  -sZ   SCTP COOKIE-ECHO scan. Envia pacote SCTP COOKIE-ECHO. Resposta
        ABORT = aberta (comportamento peculiar do SCTP). Sem resposta =
        fechada ou filtrada.

  -sO   IP protocol scan. Determina quais protocolos IP (não portas) são
        suportados pelo alvo. Ex: TCP (6), UDP (17), ICMP (1). Exige root.

  -sI <zombie>  Idle scan. Usa um host "zombie" com IP ID previsível para
        escanear o alvo sem que o IP de origem apareça nos logs do alvo.
        O scan é atribuído ao zombie. Extremamente discreto, mas exige
        um zombie compatível e é mais lento.

  -p <portas>   Especifica portas. Formatos: 22, 22,80,443, 1-1024,
        T:22,80 (só TCP), U:53,123 (só UDP), P:1-100 (só protocolo IP).

  -F            Fast scan: escaneia apenas as 100 portas mais comuns.

  --top-ports <N>  Escaneia as N portas mais comuns (ex: 1000, 5000).

  -r            Scan sequencial: escaneia portas em ordem crescente, em
                vez de aleatória. Menos discreto, mas mais organizado.

  --open        Mostra apenas portas abertas. Omite fechadas e filtradas.

DETECÇÃO DE SERVIÇO E VERSÃO:

  -sV                     Ativa a detecção de serviço e versão.

  --version-intensity <0-9>  Define a intensidade das sondas (0 = leve,
                          9 = todas as sondas). Padrão: 7. Números altos
                          demoram mais, mas identificam mais serviços.

  --version-light         Usa apenas as sondas mais prováveis (intensidade 2).
                          Mais rápido, menos preciso.

  --version-all           Tenta todas as sondas (intensidade 9). Mais lento,
                          mais preciso.

  --version-trace         Mostra o trace detalhado das sondas enviadas.
                          Útil para depurar por que um serviço não foi
                          identificado corretamente.

DETECÇÃO DE SISTEMA OPERACIONAL:

  -O                      Ativa a detecção de SO. Exige root.

  --osscan-limit          Só tenta detectar SO em hosts com pelo menos uma
                          porta aberta e uma fechada. Economiza tempo em
                          scans de rede grande.

  --osscan-guess          Força sugestões agressivas quando a detecção não
                          é conclusiva. Mostra a melhor aposta em vez de
                          "unknown".

  A detecção de SO envia uma série de pacotes TCP, UDP e ICMP com
  combinações incomuns de flags e campos, e compara as respostas com uma
  base de fingerprints de sistemas conhecidos.

SCRIPTS NSE (NMAP SCRIPTING ENGINE):

  -sC                     Executa os scripts da categoria "default".
                          Equivalente a --script=default.

  --script <expressão>    Executa scripts por categoria, nome ou caminho.
                          Ex: --script vuln, --script "http-*",
                          --script "default and safe".

  --script-args <args>    Passa argumentos para os scripts.
                          Ex: --script-args user=admin,pass=123.

  --script-trace          Mostra os pacotes enviados e recebidos pelos
                          scripts. Só para depuração.

  --script-updatedb       Atualiza o banco de dados de scripts. Útil
                          depois de instalar scripts novos.

  CATEGORIAS DE SCRIPTS (as principais):

    auth        Testa credenciais e bypass de autenticação (FTP, SSH, HTTP).

    broadcast   Descobre hosts via broadcast em rede local.

    brute       Ataques de força bruta contra serviços.

    default     Scripts seguros e úteis, executados com -sC. Equilibrado.

    discovery   Descobre informações sobre a rede e serviços.

    dos         Testa vulnerabilidade a negação de serviço. Cuidado.

    exploit     Tenta explorar vulnerabilidades conhecidas. Use com autorização.

    external    Envia dados para serviços externos (ex: whois, VirusTotal).

    fuzzer      Envia dados aleatórios para testar robustez de serviços.

    intrusive   Scripts agressivos que podem derrubar serviços ou disparar IDS.

    malware     Detecta backdoors e malware conhecidos.

    safe        Scripts que não afetam o alvo, seguros de rodar.

    version     Complementa a detecção de versão (-sV).

    vuln        Detecta vulnerabilidades conhecidas no alvo.

TIMING E PERFORMANCE:

  -T<0-5>   Templates de timing:

            T0 (paranoid)  — 1 porta por vez, 5 minutos entre sondas.
                             Evasão máxima de IDS, extremamente lento.

            T1 (sneaky)    — 15 segundos entre sondas. Evita IDS.

            T2 (polite)    — 0,4 segundos entre sondas. Usa pouca banda.

            T3 (normal)    — Padrão do nmap. Paralelismo moderado.

            T4 (aggressive) — 1250 ms de timeout, 6 retransmissões.
                             Recomendado para redes confiáveis. Padrão do módulo.

            T5 (insane)    — 300 ms de timeout, 2 retransmissões. Só para
                             redes extremamente rápidas. Pode perder precisão.

EVASÃO DE FIREWALL E IDS:

  -f                Fragmenta pacotes IP em pedaços de 8 bytes. Dificulta a
                    inspeção por filtros de pacotes. Pode ser usado duas
                    vezes para fragmentos de 16 bytes.

  --mtu <valor>     Alternativa ao -f. Define o MTU manualmente. Deve ser
                    múltiplo de 8. Ex: --mtu 24.

  -D <decoys>       Usa endereços IP "iscas" junto com o IP real. O alvo vê
                    o scan vindo de múltiplos IPs, dificultando identificar
                    a origem. Ex: -D RND:10,10.0.0.1,10.0.0.2,ME.

  -S <ip>           Falsifica o IP de origem. Não funciona com todas as
                    configurações de rede, pois a resposta vai para o IP
                    falsificado, não para você.

  --source-port <porta>  Usa uma porta de origem específica. Alguns firewalls
                    mal configurados confiam apenas na porta de origem.
                    Ex: --source-port 53 (parece DNS).

  --ttl <valor>     Define o TTL dos pacotes. Valores baixos podem fazer
                    pacotes morrerem antes de chegar ao alvo, mas podem
                    enganar IDS que só olham tráfego que passa por ele.
                    Ex: --ttl 64.

  --spoof-mac <mac>  Falsifica o endereço MAC. Ex: --spoof-mac 0 (MAC
                    aleatório), --spoof-mac Apple (MAC da Apple).

  --data-length <N>  Adiciona N bytes de dados aleatórios aos pacotes.
                    Muda a assinatura dos pacotes, dificultando a detecção
                    por IDS baseado em assinatura fixa.

  --randomize-hosts  Aleatoriza a ordem dos hosts escaneados.

SAÍDA E FORMATOS:

  -oN <arquivo>     Saída normal (texto legível por humanos), como aparece
                    no terminal.

  -oX <arquivo>     Saída em XML. Ideal para processamento por outras
                    ferramentas e para importar em relatórios.

  -oG <arquivo>     Saída "grepable" (formato antigo, fácil de filtrar com
                    grep e awk). Descontinuado, mas ainda usado.

  -oA <basename>    Gera os três formatos de uma vez: basename.nmap,
                    basename.xml e basename.gnmap.

  -v                Aumenta a verbosidade. Pode ser usado várias vezes
                    (-vv, -vvv) para mais detalhes.

  -d                Debug. Níveis de 0 a 9. Para desenvolvimento.

REDE LOCAL (auxiliar do módulo):

  A função rede_local lista as interfaces IPv4 ativas da máquina e o
  endereço de rede correspondente a cada uma. Também é usada por qualquer
  função que aceite "alvo": quando o usuário digita o valor especial
  "local", o módulo executa `ip -o -4 addr show`, descarta a interface
  "lo" (loopback), pega a primeira interface IPv4 ativa e substitui
  "local" pelo CIDR da rede correspondente antes de montar o comando
  nmap. Assim, para escanear a rede à qual você está conectado, basta
  digitar "local" no campo alvo.

  Detalhe técnico da conversão: dada uma interface com o endereço
  192.168.1.100/24, a máscara /24 corresponde aos 24 primeiros bits
  em 1 (255.255.255.0), e o endereço de rede resultante é 192.168.1.0/24.
  É esse valor que o nmap recebe — endereço de rede em notação CIDR.
  Nenhuma dependência extra é usada: o módulo se apoia no comando `ip`
  (iproute2), que já vem instalado no Kali.

REFERÊNCIAS:

  - Documentação oficial: https://nmap.org/book/man.html

  - Livro "Nmap Network Scanning" (Gordon Lyon): https://nmap.org/book/

  - Lista completa de opções: https://nmap.org/book/man-briefoptions.html

  - NSE (scripts): https://nmap.org/nsedoc/

  - Manual do sistema: man nmap
"""