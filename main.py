import os
import asyncio
import discord
from discord.ext import commands
from discord import Intents, Interaction
from dotenv import load_dotenv
from managers.logger import *
from discord import app_commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID"))

# Inicializa os intents
intents = Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)

async def carregar_cogs(bot):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            extension = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(extension)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Erro ao carregar cog '{filename}': `{e}`")
                
async def recarregar_cogs(bot, interaction):
    total_cogs = len([filename for filename in os.listdir('./cogs') if filename.endswith('.py')])
    carregadas = 0

    await interaction.response.send_message(
        f'**🔄 {interaction.user.mention} Iniciando o recarregamento das cogs...**',
        ephemeral=True,
    )

    message = await interaction.original_response()

    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.reload_extension(f'cogs.{filename[:-3]}')
                carregadas += 1
                porcentagem = (carregadas / total_cogs) * 100
                await message.edit(content=f'**🔄 {interaction.user.mention} Recarregando cogs: `{porcentagem:.2f}%` completo**')
            except Exception as e:
                if f'Extension "cogs.{filename[:-3]}" has not been loaded.' in str(e):
                    try:
                        await bot.load_extension(f'cogs.{filename[:-3]}')
                        carregadas += 1
                        porcentagem = (carregadas / total_cogs) * 100
                        await message.edit(content=f'**🔄 {interaction.user.mention} Carregando cogs: `{porcentagem:.2f}%` completo**')
                    except Exception as load_error:
                        logger.error(f"Erro ao carregar cog '{filename}': `{load_error}`")
                        await message.edit(content=f'**🔄 {interaction.user.mention} Erro ao carregar cog "{filename}": `{load_error}`**')
                else:
                    logger.error(f"Erro ao recarregar cog '{filename}': `{e}`")
                    await message.edit(content=f'**🔄 {interaction.user.mention} Erro ao recarregar cog "{filename}": `{e}`**')

    await message.edit(content=f'**✅ {interaction.user.mention} Todas as cogs foram recarregadas.**')


@bot.tree.command(name="reload_cogs", description="Recarrega todas as cogs do bot")
async def recarregar(interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            f"**🚫 Este comando não pode ser utilizado em DMs.**",
            ephemeral=True,
        )
        return

    if interaction.user.id != BOT_OWNER_ID:
        return await interaction.response.send_message(
            f'**🚫 {interaction.user.mention} Você não tem permissão para usar este comando.**',
            ephemeral=True,
        )

    await recarregar_cogs(bot, interaction)
    
    
@bot.tree.command(name="mod_sync", description="Força a atualização dos comandos")
async def sync(interaction: Interaction):
    user_mention = interaction.user.mention
    if interaction.guild is None:
        await interaction.response.send_message(
            f"**🚫 {user_mention} Este comando não pode ser utilizado em DMs.**",
            ephemeral=True,
        )
        return
    if (
        interaction.user.id != BOT_OWNER_ID
        and not interaction.user.guild_permissions.administrator
    ):
        try:
            await interaction.response.send_message(
                f"**🚫 {interaction.user.mention} Você não tem permissão para usar este comando.**",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            logger.error(f"Erro ao tentar enviar mensagem de permissão: `{e}`")
        return
    try:
        ping = bot.latency * 1000
        await interaction.response.send_message(
            f"**🔄 {interaction.user.mention} Sincronização dos comandos iniciada, por favor aguarde... (Ping: {ping:.2f} ms)**",
            ephemeral=True,
        )
        await bot.tree.sync()
        await interaction.edit_original_response(
            content=f"**✅ {interaction.user.mention} Comandos sincronizados manualmente! (Ping: {ping:.2f} ms)**"
        )
        logger.info("Comandos sincronizados manualmente.")
    except Exception as e:
        try:
            await interaction.edit_original_response(
                content=f"🚫 {interaction.user.mention} Erro ao sincronizar comandos: `{e}` (Ping: {ping:.2f} ms)"
            )
        except discord.HTTPException as error:
            logger.error(f"Erro ao editar resposta de erro: {error}")
        logger.error(f"Erro ao sincronizar comandos manualmente: `{e}`")

async def setup_bot():
    GUILD_ID = 471470882775367691
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    await bot.change_presence(activity=discord.Game(name="Black Desert Online"))

@bot.event
async def on_ready():
    try:
        await setup_bot()
        logger.info(f"Carregando extensões aguarde...")
        await carregar_cogs(bot)
        logger.info(f"Bot {bot.user.name} está online e pronto para uso!")
    except Exception as e:
        logger.error(f"Ocorreu um erro em 'on_ready': `{e}`")

bot.run(TOKEN)