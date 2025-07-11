import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Select
import uuid
import json
import os
import re

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

CANAL_GUIAS_ID = 1130628269251768441

# --------------------- Modais --------------------- #

class GuideModal(Modal):
    def __init__(self, categoria, guide_id=None, title='', link='', is_edit=False):
        super().__init__(title='✏️ Editar Guia' if is_edit else '➕ Adicionar Guia', timeout=300)
        self.categoria = categoria
        self.guide_id = guide_id
        self.is_edit = is_edit
        self.title_input = TextInput(label='📌 Título do Guia', default=title)
        self.link_input = TextInput(label='🔗 Link do Conteúdo', default=link)
        self.add_item(self.title_input)
        self.add_item(self.link_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        title = self.title_input.value.strip()
        link = self.link_input.value.strip()
        if not title or not link or not re.match(r'^https?://\S+\.\S+', link):
            await interaction.edit_original_response(content=f'🚫 **{interaction.user.mention} Preencha corretamente os campos.**', view=None)
            return
        data = get_guides_data()
        if self.is_edit:
            for guia in data[self.categoria]:
                if guia['id'] == self.guide_id:
                    guia['title'] = title
                    guia['link'] = link
                    break
        else:
            data.setdefault(self.categoria, []).append({
                "id": str(uuid.uuid4()),
                "title": title,
                "link": link
            })
        save_guides_data(data)
        await update_category_message(interaction.client, self.categoria)
        await interaction.edit_original_response(content=f'**✅ {interaction.user.mention} Guia {"editado" if self.is_edit else "adicionado"} com sucesso!**', view=None)

class CategoryModal(Modal):
    def __init__(self):
        super().__init__(title='📁 Nova Categoria', timeout=300)
        self.category_input = TextInput(label='📌 Título da Categoria')
        self.add_item(self.category_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        categoria = self.category_input.value.strip()
        if not categoria:
            await interaction.edit_original_response(content=f'🚫 **{interaction.user.mention} Nome inválido.**', view=None)
            return
        data = get_guides_data()
        if categoria in data:
            await interaction.edit_original_response(content=f'**🚫 {interaction.user.mention} Categoria já existe.**', view=None)
            return
        data[categoria] = []
        save_guides_data(data)
        await update_category_message(interaction.client, categoria)
        await interaction.edit_original_response(content=f'**✅ {interaction.user.mention} Categoria "{categoria}" criada com sucesso!**', view=None)

# --------------------- Atualizar Mensagem --------------------- #

async def update_category_message(bot, categoria):
    data = get_guides_data()
    message_ids = get_message_ids()
    canal = bot.get_channel(CANAL_GUIAS_ID)
    conteudo = f"> ㅤㅤ\n>  **{categoria}**\n> ㅤㅤ\n"
    for guia in data.get(categoria, []):
        conteudo += f"- [{guia['title']}]({guia['link']})\n"
    msg_id = message_ids.get(categoria)
    if canal:
        if msg_id:
            try:
                msg = await canal.fetch_message(msg_id)
                await msg.edit(content=conteudo)
            except Exception:
                msg = await canal.send(conteudo)
                message_ids[categoria] = msg.id
        else:
            msg = await canal.send(conteudo)
            message_ids[categoria] = msg.id
        save_message_ids(message_ids)

# --------------------- Menu Paginado com Voltar --------------------- #

class PaginatedSelectMenu(discord.ui.View):
    def __init__(self, options, placeholder, callback_fn, previous_view=None, per_page=25):
        super().__init__(timeout=120)
        self.options = options
        self.placeholder = placeholder
        self.callback_fn = callback_fn
        self.page = 0
        self.per_page = per_page
        self.total_pages = (len(options) - 1) // per_page + 1
        self.previous_view = previous_view
        self._build_page()

    def _build_page(self):
        self.clear_items()
        start = self.page * self.per_page
        end = start + self.per_page
        chunk = self.options[start:end]

        select = discord.ui.Select(
            placeholder=f"{self.placeholder} ({self.page+1}/{self.total_pages})",
            options=chunk,
            min_values=1,
            max_values=1
        )

        async def select_callback(interaction: discord.Interaction):
            await self.callback_fn(interaction, select.values[0])

        select.callback = select_callback
        self.add_item(select)

        if self.page > 0:
            prev_button = discord.ui.Button(label="⬅️ Página Anterior", style=discord.ButtonStyle.secondary)
            async def prev_callback(inter: discord.Interaction):
                self.page -= 1
                self._build_page()
                await inter.response.edit_message(view=self)
            prev_button.callback = prev_callback
            self.add_item(prev_button)

        if self.page < self.total_pages - 1:
            next_button = discord.ui.Button(label="Próxima Página ➡️", style=discord.ButtonStyle.secondary)
            async def next_callback(inter: discord.Interaction):
                self.page += 1
                self._build_page()
                await inter.response.edit_message(view=self)
            next_button.callback = next_callback
            self.add_item(next_button)

        if self.previous_view is not None:
            back_button = discord.ui.Button(label="⬅️ Menu Anterior", style=discord.ButtonStyle.success)
            async def back_callback(inter: discord.Interaction):
                await inter.response.edit_message(content="**Retornando ao menu anterior...**", view=self.previous_view)
            back_button.callback = back_callback
            self.add_item(back_button)

# --------------------- Utilitários --------------------- #

def get_category_options(categorias):
    return [discord.SelectOption(label=f"📁 {cat}", value=cat, description="Clique para selecionar esta categoria") for cat in categorias]

def get_guide_options(guias):
    options = []
    for g in guias:
        desc = g['link']
        if len(desc) > 100:
            desc = desc[:97] + "..."
        options.append(
            discord.SelectOption(
                label=f"📌 {g['title']}",
                value=g['id'],
                description=desc
            )
        )
    return options

async def category_callback(interaction, categoria, acao, previous_view):
    data = get_guides_data()
    guias = data.get(categoria, [])

    if acao == "listar":
        if not guias:
            await interaction.response.edit_message(content=f"**🔎 {interaction.user.mention} Nenhum guia nesta categoria.**", view=previous_view)
            return
        msg = "\n".join(f"- [{g['title']}]({g['link']})" for g in guias)
        await interaction.response.edit_message(content=f"**📂 {interaction.user.mention} Guias em {categoria}:**\n{msg}", view=previous_view)

    elif acao == "adicionar":
        await interaction.response.send_modal(GuideModal(categoria))

    elif acao in ["editar", "remover"]:
        if not guias:
            await interaction.response.edit_message(content=f"**🔎 {interaction.user.mention} Nenhum guia nesta categoria.**", view=previous_view)
            return

        async def guide_callback(i, guia_id):
            guia = next((g for g in guias if g['id'] == guia_id), None)
            if not guia:
                await i.response.edit_message(content=f"**🚫 {i.user.mention} Guia não encontrado.**", view=previous_view)
                return
            if acao == "editar":
                await i.response.send_modal(
                    GuideModal(categoria, guide_id=guia_id, title=guia['title'], link=guia['link'], is_edit=True)
                )
            else:
                guias.remove(guia)
                save_guides_data(data)
                await update_category_message(i.client, categoria)
                await i.response.edit_message(content=f"**✅ {i.user.mention} Guia removido com sucesso!**", view=None)

        view = PaginatedSelectMenu(
            get_guide_options(guias),
            "Selecione o guia",
            guide_callback,
            previous_view=previous_view
        )
        await interaction.response.edit_message(content=f"**{interaction.user.mention} Selecione o guia para {acao}:**", view=view)

# --------------------- Menu Principal --------------------- #

class MainMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainSelect(self))

class MainSelect(Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="📄 Listar Guias", value="listar", description="Veja todos os guias existentes"),
            discord.SelectOption(label="➕ Adicionar Guia", value="adicionar", description="Adicione um novo guia"),
            discord.SelectOption(label="✏️ Editar Guia", value="editar", description="Edite um guia existente"),
            discord.SelectOption(label="🗑️ Remover Guia", value="remover", description="Remova um guia existente"),
            discord.SelectOption(label="📁 Nova Categoria", value="nova_categoria", description="Crie uma nova categoria de guias"),
        ]
        self.parent_view = parent_view
        super().__init__(placeholder="📝 O que deseja fazer?", options=options)

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        data = get_guides_data()
        categorias = list(data.keys())

        if value == "nova_categoria":
            await interaction.response.send_modal(CategoryModal())
        else:
            view = PaginatedSelectMenu(
                get_category_options(categorias),
                "Selecione a categoria",
                lambda i, cat: category_callback(i, cat, value, self.parent_view),
                previous_view=self.parent_view
            )
            await interaction.response.edit_message(content=f"**📁 {interaction.user.mention} Selecione a categoria:**", view=view)

# --------------------- Cog --------------------- #

class GuideChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="guia", description="📚 Gerencie guias e categorias em um único menu.")
    async def guia(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content=f"**{interaction.user.mention} Menu de Gerenciamento de Guias:**",  
            view=MainMenu()
        )

async def setup(bot):
    await bot.add_cog(GuideChannel(bot))
