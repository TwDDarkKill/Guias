import re
import discord

async def safe_send(channel, content: str, **kwargs):
    # 1) Impede envio de embeds explícitos
    if "embed" in kwargs or "embeds" in kwargs:
        raise ValueError("Envio de embeds não permitido.")
    
    # 2) Se quiser remover o próprio link do texto:
    # content = re.sub(r'https?://\S+', '', content).strip()

    # 3) Envia a mensagem normalmente
    msg = await channel.send(content, **kwargs)

    # 4) Suprime embeds editando a mensagem
    try:
        await msg.edit(suppress=True)
    except Exception as e:
        print(f"Falha ao suprimir embeds: {e}")

    return msg
