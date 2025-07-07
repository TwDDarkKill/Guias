import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Select
import uuid
import json
import os
import re
import asyncio

data_folder = './data'
os.makedirs(data_folder, exist_ok=True)

def get_guides_data():
    file_path = os.path.join(data_folder, 'guias.json')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_guides_data(data):
    file_path = os.path.join(data_folder, 'guias.json')
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
        
def save_message_ids(data):
    file_path = os.path.join(data_folder, 'message_ids.json')
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def get_message_ids():
    file_path = os.path.join(data_folder, 'message_ids.json')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}


class NewCategoryModal(Modal):
    def __init__(self):
        super().__init__(title='Criar Nova Categoria e Guia', timeout=300)

        self.category_input = TextInput(
            label='Título da Categoria',
            placeholder='Digite o nome da nova categoria...'
        )
        self.guide_title_input = TextInput(
            label='Título do Guia',
            placeholder='Digite o título do guia...'
        )
        self.guide_link_input = TextInput(
            label='Link do Conteúdo',
            placeholder='Cole o link do conteúdo...'
        )

        self.add_item(self.category_input)
        self.add_item(self.guide_title_input)
        self.add_item(self.guide_link_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        category_name = self.category_input.value.strip()
        guide_title = self.guide_title_input.value.strip()
        guide_link = self.guide_link_input.value.strip()

        if not category_name or not guide_title or not guide_link:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} Nenhum dos campos pode estar vazio.**',
                view=None
            )
            return

        if not re.match(r'^https?://\S+\.\S+', guide_link):
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} O link do guia deve ser uma URL válida.**',
                view=None
            )
            return

        data = get_guides_data()
        guide_id = str(uuid.uuid4())
        new_guide = {
            "id": guide_id,
            "title": guide_title,
            "link": guide_link
        }

        if category_name not in data:
            data[category_name] = []

        data[category_name].append(new_guide)
        save_guides_data(data)

        # Enviar o guia ao canal de guias
        canal_guias_id = 1130628269251768441
        canal = interaction.client.get_channel(canal_guias_id)
        if canal:
            conteudo = f"> ㅤㅤ\n> **{category_name}**\n> ㅤㅤ\n"
            for guia in data[category_name]:
                conteudo += f"- [{guia['title']}]({guia['link']})\n"
            try:
                msg = await canal.send(conteudo)
                # Salvar o ID da mensagem para a nova categoria
                message_ids = get_message_ids()
                message_ids[category_name] = msg.id
                save_message_ids(message_ids)
            except Exception as e:
                await interaction.edit_original_response(
                    content=f'**✅ {interaction.user.mention} Categoria **{category_name}** criada com sucesso com o guia **{guide_title}**!\n🚫 Mas houve um erro ao enviar a mensagem ao canal: {e}**',
                    view=None
                )
                return
        else:
            await interaction.edit_original_response(
                content=f'**✅ {interaction.user.mention} Categoria **{category_name}** criada com sucesso com o guia **{guide_title}**!\n🚫 Mas não consegui acessar o canal de guias.**',
                view=None
            )
            return

        await interaction.edit_original_response(
            content=f'**✅ {interaction.user.mention} Categoria **{category_name}** criada com sucesso com o guia **{guide_title}** e enviada ao canal!**',
            view=None
        )


class GuideModal(Modal):
    def __init__(self, guide_id=None, title='', link=''):
        super().__init__(title='Editar Guia', timeout=300)
        self.guide_id = guide_id

        self.title_input = TextInput(
            label='Título do Guia',
            placeholder='Digite o título do guia...',
            default=title
        )
        self.link_input = TextInput(
            label='Link do Conteúdo',
            placeholder='Cole o link do conteúdo...',
            default=link
        )
        self.add_item(self.title_input)
        self.add_item(self.link_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        title = self.title_input.value.strip()
        link = self.link_input.value.strip()

        if not title or not link:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} O título e o link não podem estar vazios.**',
                view=None
            )
            return

        if not re.match(r'^https?://\S+\.\S+', link):
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} O link deve ser uma URL válida.**',
                view=None
            )
            return

        data = get_guides_data()
        updated = False
        category_updated = None

        for categoria in data:
            for guia in data[categoria]:
                if guia['id'] == self.guide_id:
                    guia['title'] = title
                    guia['link'] = link
                    updated = True
                    category_updated = categoria
                    break
            if updated:
                break

        if not updated:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} Guia não encontrado.**',
                view=None
            )
            return

        save_guides_data(data)

        channel_id = 1130628269251768441
        message_ids = get_message_ids()
        message_id = message_ids.get(category_updated)

        if message_id:
            channel = interaction.client.get_channel(channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(message_id)
                    conteudo = f"> ㅤㅤ\n> **{category_updated}**\n> ㅤㅤ\n"
                    for guia in data[category_updated]:
                        conteudo += f"- [{guia['title']}]({guia['link']})\n"
                    await msg.edit(content=conteudo)
                except Exception as e:
                    await interaction.edit_original_response(
                        content=f'**🚫 {interaction.user.mention} Guia atualizado, mas houve um erro ao editar a mensagem no canal de guias: {e}**',
                        view=None
                    )
                    return
            else:
                await interaction.edit_original_response(
                    content=f'**🚫 {interaction.user.mention} Guia atualizado, mas não consegui acessar o canal de guias.**',
                    view=None
                )
                return
        else:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} Guia atualizado, mas não encontrei o ID da mensagem para a categoria **{category_updated}**.**',
                view=None
            )
            return

        await interaction.edit_original_response(
            content=f'**✅ {interaction.user.mention} Guia atualizado com sucesso!**',
            view=None
        )

class GuideSelect(Select):
    def __init__(self, categoria, guias):
        options = [
            discord.SelectOption(label=guia['title'], value=guia['id'])
            for guia in guias
        ]
        super().__init__(placeholder=f"Guias em {categoria}", options=options)
        self.categoria = categoria

    async def callback(self, interaction: discord.Interaction):
        data = get_guides_data()
        guias_categoria = data.get(self.categoria, [])
        selected_guide = next((g for g in guias_categoria if g['id'] == self.values[0]), None)
        if not selected_guide:
            await interaction.response.send_message(
                content=f'**🚫 {interaction.user.mention} Guia não encontrado.**',
                ephemeral=True,
                view=None
            )
            return

        modal = GuideModal(
            guide_id=selected_guide['id'],
            title=selected_guide['title'],
            link=selected_guide['link']
        )
        await interaction.response.send_modal(modal)

class CategorySelect(Select):
    def __init__(self, categorias):
        data = get_guides_data()

        options = []
        for categoria in categorias:
            quantidade = len(data.get(categoria, []))
            options.append(discord.SelectOption(
                label=categoria,
                value=categoria,
                description=f"{quantidade} guia(s) nesta categoria"
            ))

        options.append(discord.SelectOption(label="Criar nova categoria", value="nova_categoria"))

        super().__init__(placeholder="Selecione uma categoria ou crie nova", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "nova_categoria":
            modal = NewCategoryModal()
            await interaction.response.send_modal(modal)
            return

        categoria = self.values[0]
        data = get_guides_data()
        guias = data.get(categoria, [])

        view = View(timeout=None)
        # Adiciona opção de novo guia
        view.add_item(GuideSelectWithNewOption(categoria, guias))
        await interaction.response.send_message(
            f'**{interaction.user.mention} Guias disponíveis na categoria {categoria}:**',
            view=view,
            ephemeral=True
        )

class GuideSelectWithNewOption(Select):
    def __init__(self, categoria, guias):
        options = [
            discord.SelectOption(label=guia['title'], value=guia['id'])
            for guia in guias
        ]
        options.append(discord.SelectOption(label="Adicionar novo guia", value="novo_guia"))
        super().__init__(placeholder=f"Guias em {categoria}", options=options)
        self.categoria = categoria

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "novo_guia":
            # Modal para adicionar novo guia à categoria existente
            modal = AddGuideToCategoryModal(self.categoria)
            await interaction.response.send_modal(modal)
            return

        data = get_guides_data()
        guias_categoria = data.get(self.categoria, [])
        selected_guide = next((g for g in guias_categoria if g['id'] == self.values[0]), None)
        if not selected_guide:
            await interaction.response.send_message(
                content=f'**🚫 {interaction.user.mention} Guia não encontrado.**',
                ephemeral=True,
                view=None
            )
            return

        modal = GuideModal(
            guide_id=selected_guide['id'],
            title=selected_guide['title'],
            link=selected_guide['link']
        )
        await interaction.response.send_modal(modal)

class AddGuideToCategoryModal(Modal):
    def __init__(self, categoria):
        super().__init__(title=f'Adicionar Guia em {categoria}', timeout=300)
        self.categoria = categoria

        self.guide_title_input = TextInput(
            label='Título do Guia',
            placeholder='Digite o título do guia...'
        )
        self.guide_link_input = TextInput(
            label='Link do Conteúdo',
            placeholder='Cole o link do conteúdo...'
        )

        self.add_item(self.guide_title_input)
        self.add_item(self.guide_link_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guide_title = self.guide_title_input.value.strip()
        guide_link = self.guide_link_input.value.strip()

        if not guide_title or not guide_link:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} O título e o link não podem estar vazios.**',
                view=None
            )
            return

        if not re.match(r'^https?://\S+\.\S+', guide_link):
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} O link deve ser uma URL válida.**',
                view=None
            )
            return

        data = get_guides_data()
        guide_id = str(uuid.uuid4())
        new_guide = {
            "id": guide_id,
            "title": guide_title,
            "link": guide_link
        }

        if self.categoria not in data:
            data[self.categoria] = []

        data[self.categoria].append(new_guide)
        save_guides_data(data)

        # Atualiza mensagem no canal de guias
        canal_guias_id = 1130628269251768441
        message_ids = get_message_ids()
        message_id = message_ids.get(self.categoria)
        channel = interaction.client.get_channel(canal_guias_id)
        if channel and message_id:
            try:
                msg = await channel.fetch_message(message_id)
                conteudo = f"> ㅤㅤ\n> **{self.categoria}**\n> ㅤㅤ\n"
                for guia in data[self.categoria]:
                    conteudo += f"- [{guia['title']}]({guia['link']})\n"
                await msg.edit(content=conteudo)
            except Exception as e:
                await interaction.edit_original_response(
                    content=f'**✅ {interaction.user.mention} Guia adicionado à categoria **{self.categoria}**!\n🚫 Mas houve um erro ao atualizar a mensagem no canal: {e}**',
                    view=None
                )
                return
        else:
            await interaction.edit_original_response(
                content=f'**✅ {interaction.user.mention} Guia adicionado à categoria **{self.categoria}**!\n🚫 Mas não consegui acessar o canal de guias ou a mensagem.**',
                view=None
            )
            return

        await interaction.edit_original_response(
            content=f'**✅ {interaction.user.mention} Guia adicionado à categoria **{self.categoria}** com sucesso!**',
            view=None
        )


class GuideChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="reenviar_guias", description="Envia todos os guias novamente ao canal e salva os IDs das mensagens.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def reenviar_guias(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        data = get_guides_data()
        if not data:
            await interaction.edit_original_response(content=f'**🚫 {interaction.user.mention} Nenhum guia encontrado no arquivo guias.json.**')
            return

        canal_guias_id = 1130628269251768441
        canal = self.bot.get_channel(canal_guias_id)
        if not canal:
            await interaction.edit_original_response(content=f'**🚫 {interaction.user.mention} Não consegui acessar o canal de guias.**')
            return

        try:
            async for msg in canal.history(limit=None, oldest_first=True):
                try:
                    await msg.delete()
                    await asyncio.sleep(1)
                except Exception:
                    continue
        except Exception as e:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} Erro ao apagar mensagens do canal: {e}**'
            )
            return

        message_ids = {}

        for categoria, guias in data.items():
            if not guias:
                continue

            conteudo = f"> ㅤㅤ\n> **{categoria}**\n> ㅤㅤ\n"
            for guia in guias:
                conteudo += f"- [{guia['title']}]({guia['link']})\n"

            try:
                msg = await canal.send(conteudo)
                message_ids[categoria] = msg.id
                await asyncio.sleep(1)
            except Exception as e:
                await interaction.edit_original_response(
                    content=f'**🚫 {interaction.user.mention} Erro ao enviar mensagens da categoria {categoria}: {e}**'
                )
                return

        save_message_ids(message_ids)

        await interaction.edit_original_response(
            content=f'**✅ {interaction.user.mention} Todos os guias foram reenviados ao canal <#{canal_guias_id}>.**'
        )

    @discord.app_commands.command(name="guia", description="Gerenciar guias por categoria.")
    async def guia(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message_ids = get_message_ids()
        categorias = list(message_ids.keys())

        if not categorias:
            await interaction.edit_original_response(
                content=f'**🚫 {interaction.user.mention} Nenhuma categoria encontrada.**',
                view=None
            )
            return

        view = View(timeout=None)
        view.add_item(CategorySelect(categorias))
        await interaction.edit_original_response(
            content=f'**{interaction.user.mention} Selecione a categoria para listar seus guias:**',
            view=view
        )

async def setup(bot):
    await bot.add_cog(GuideChannel(bot))