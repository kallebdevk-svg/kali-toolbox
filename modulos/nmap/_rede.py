"""Detecção da rede local."""
import shutil
from datetime import datetime

from ._core import erro, redes_locais, rodar


def h_rede_local(params, status, timeout):
    status("consultando as interfaces de rede")
    if not shutil.which("ip"):
        return erro("comando 'ip' não encontrado (pacote iproute2)")

    codigo, saida, e, estourou = rodar(["ip", "-o", "-4", "addr", "show"], timeout)
    if estourou:
        return erro(f"tempo limite de {timeout}s ao consultar interfaces")
    if codigo != 0:
        return erro(e or "falha ao executar 'ip'", saida=saida, codigo=codigo)

    redes = redes_locais()
    if not redes:
        return erro("nenhuma interface IPv4 ativa encontrada (só loopback)")

    linhas = [f"  {iface:<12} {cidr:<22} rede: {rede}" for iface, cidr, rede in redes]
    texto = "Interfaces IPv4 ativas (sem loopback):\n" + "\n".join(linhas)
    texto += f"\n\nA primeira rede detectada é: {redes[0][2]}"
    texto += "\nDigite 'local' no campo alvo de qualquer scan para usar essa rede."

    relatorio = f"Redes locais\nData: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n{texto}\n"
    if params.get("mostrar_raw"):
        relatorio += f"\nSaída bruta de 'ip -o -4 addr show':\n{saida}"

    status("detecção concluída")
    return {"status": "ok", "saida": texto, "erro": "", "codigo": 0, "relatorio": relatorio}