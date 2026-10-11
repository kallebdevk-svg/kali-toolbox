DOCS = """
O QUE É O DIG:
  dig (Domain Information Groper) é a ferramenta de linha de comando do
  pacote BIND para consultar servidores DNS. Substituiu o antigo nslookup
  como padrão de fato em ambientes Unix. É usada para consultar qualquer
  tipo de registro DNS, depurar problemas de resolução, verificar
  delegações e investigar configurações de zonas.

COMO O DNS FUNCIONA POR DENTRO:

  O DNS é um sistema hierárquico e distribuído. Uma consulta típica
  percorre esta cadeia:

  1. O cliente pergunta ao resolvedor local (geralmente em
     127.0.0.53 ou em /etc/resolv.conf) qual o IP de um nome.

  2. Se o resolvedor não tem em cache, ele pergunta a um dos 13
     servidores-raiz (a-m.root-servers.net).

  3. A raiz responde com o servidor autoritativo do TLD (.com, .org,
     .br, etc.).

  4. O resolvedor pergunta ao servidor do TLD, que responde com o
     servidor autoritativo do domínio consultado.

  5. O resolvedor pergunta ao autoritativo, que devolve a resposta
     final (o IP, o MX, o TXT, etc.).

  6. O resolvedor guarda em cache pelo TTL informado e devolve ao
     cliente.

  Cada resposta tem quatro seções: QUESTION (o que foi perguntado),
  ANSWER (a resposta), AUTHORITY (quem é autoritativo) e ADDITIONAL
  (informações extras).

TIPOS DE REGISTRO MAIS COMUNS:

  A       Endereço IPv4 (ex: 93.184.216.34).

  AAAA    Endereço IPv6.

  CNAME   Apelido — aponta um nome para outro nome.

  MX      Servidor de e-mail do domínio, com prioridade.

  NS      Servidores de nome autoritativos do domínio.

  SOA     Start of Authority — metadados da zona (serial, refresh,
          retry, expire, minimum TTL, e-mail do responsável).

  TXT     Texto livre. Usado para SPF, DKIM, DMARC, verificações
          de posse de domínio, etc.

  PTR     Reverse DNS — mapeia IP para nome (usado em -x).

  SRV     Serviço específico (protocolo + host + porta + prioridade).

  CAA     Autoridade de certificação permitida a emitir certificados
          para o domínio.

  DNSKEY  Chave pública DNSSEC.

  DS      Delegation Signer — elo DNSSEC entre pai e filho.

  ANY     Pede todos os registros disponíveis. Raramente responde
          tudo hoje em dia (muitos servidores recusam por segurança).

FORMATO DA SAÍDA DO DIG:

  A saída padrão tem quatro blocos:

    ; <<>> DiG 9.x <<>> exemplo.com A
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 12345
    ;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

    ;; QUESTION SECTION:
    ;exemplo.com.       IN  A

    ;; ANSWER SECTION:
    exemplo.com.  3600  IN  A  93.184.216.34

    ;; Query time: 12 msec
    ;; SERVER: 127.0.0.53#53(127.0.0.53)
    ;; WHEN: ...
    ;; MSG SIZE  rcvd: 56

  O cabeçalho mostra o STATUS (NOERROR, NXDOMAIN, SERVFAIL, REFUSED).
  NOERROR = resposta válida. NXDOMAIN = nome não existe. SERVFAIL = erro
  do servidor. REFUSED = servidor recusou a consulta.

  Este módulo oferece três formatos de saída:

    resposta  → só a seção ANSWER, o essencial.
    short     → só o valor final, ideal para scripts.
    bruto     → saída completa do dig, útil para depuração.

FLAGS MAIS USADAS:

  +short        Mostra só a resposta (sem cabeçalhos).

  +noall +answer   Mostra só o bloco ANSWER.

  +trace        Segue a delegação desde a raiz. Excelente para
                depurar problemas de resolução e ver a cadeia
                completa de servidores autoritativos.

  +dnssec       Pede os registros RRSIG junto com a resposta.
                Verifica se a zona está assinada.

  +tcp          Força consulta por TCP em vez de UDP. Útil quando
                a resposta é grande (>512 bytes sem EDNS) ou
                quando o firewall bloqueia UDP/53.

  +norecurse    Pede ao servidor para não recursar. Só faz sentido
                consultando um autoritativo diretamente.

  -x IP         Consulta reversa. Converte o IP em nome.

  -f ARQUIVO    Lê consultas de um arquivo texto, uma por linha.

  @SERVIDOR     Consulta um servidor específico em vez do
                resolv.conf. Ex: @8.8.8.8, @1.1.1.1.

REFERÊNCIAS:

  - Documentação: https://bind9.readthedocs.io/en/latest/manpages.html

  - Manual do sistema: man dig

  - RFC 1035 (DNS original): https://www.rfc-editor.org/rfc/rfc1035

  - DNSSEC: https://www.icann.org/resources/pages/dnssec-what-is-it-why-important-2019-03-05-en
"""