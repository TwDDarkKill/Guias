import re
import discord
import asyncio

# Lock global para serializar envios
send_lock = asyncio.Lock()

async def safe_send(channel, content: str, **kwargs):
    async with send_lock:
        # 1) Impede envio de embeds explícitos
        if "embed" in kwargs or "embeds" in kwargs:
            raise ValueError("Envio de embeds não permitido.")

        # 2) Envia a mensagem normalmente
        msg = await channel.send(content, **kwargs)

        # 3) Aguarda um intervalo antes de suprimir embeds
        await asyncio.sleep(0.5)  # intervalo de 0,5 segundos (ajuste conforme necessário)

        # 4) Suprime embeds editando a mensagem
        try:
            await msg.edit(suppress=True)
        except Exception as e:
            print(f"Falha ao suprimir embeds: {e}")

        # 5) Remove o anexo, se houver
        if msg.attachments:
            try:
                await msg.edit(attachments=[])
                await asyncio.sleep(0.5)  # Aguarda remoção do anexo
            except Exception as e:
                print(f"Falha ao remover anexo: {e}")

        return msg
