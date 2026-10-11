DOCS = """
O QUE É O AIRCRACK-NG:
  Aircrack-ng é uma suíte de ferramentas para auditoria de segurança
  de redes Wi-Fi. Ela cobre captura de pacotes 802.11, injeção de
  tráfego, ataque de desautenticação, quebra de chaves WEP e
  WPA/WPA2-PSK e decriptação de capturas. É composta por vários
  binários independentes, cada um com uma função específica.

FERRAMENTAS DA SUÍTE:

  airmon-ng    Ativa e desativa o modo monitor em interfaces wireless.
               Também lista processos que podem interferir com a placa.

  airodump-ng  Captura pacotes 802.11 brutos. Lista APs e clientes
               próximos, salva capturas em .cap/.ivs e pode filtrar
               por canal, BSSID ou ESSID.

  aireplay-ng  Injeta pacotes na rede. Usado para desautenticação
               (forçar handshake), autenticação falsa, replay de ARP
               (para WEP) e teste de injeção.

  aircrack-ng  Quebra chaves WEP (PTW/FMS/KoreK) e senhas WPA/WPA2
               via dicionário. Consome arquivos .cap ou .ivs.

  airdecap-ng  Decripta capturas WEP/WPA usando a chave ou senha.

FLUXO TÍPICO DE UM TESTE:

  1. airmon-ng start wlan0          → ativa modo monitor (wlan0mon)
  2. airodump-ng wlan0mon           → lista redes e clientes
  3. airodump-ng -c 6 -w cap wlan0mon → captura canal 6
  4. aireplay-ng -0 5 -a <BSSID> wlan0mon → força handshake
  5. aircrack-ng -w wordlist cap-01.cap → quebra a senha

REFERÊNCIA: https://www.aircrack-ng.org/documentation.html

ATENÇÃO: uso restrito a laboratório próprio ou alvos com autorização
explícita. Capturar, injetar ou quebrar redes sem permissão é ilegal
na maioria das jurisdições.
"""