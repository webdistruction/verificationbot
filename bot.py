import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, Button, View
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

verification_channel_id = 1  # ID канала верификации
moderation_channel_id = 1  # ID канала для модерации заявок
verified_role_id = 1       # ID роли верифицированного пользователя

class VerificationModal(Modal, title="Верификация"):
    name = TextInput(label="Ваше имя", placeholder="Как вас зовут?", required=True)
    age = TextInput(label="Возраст", placeholder="Сколько вам лет?", min_length=1, max_length=2, required=True)
    purpose = TextInput(label="Цель пребывания на сервере", placeholder="Что планируете делать на сервере?", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Заявка на верификацию", description=f"**Пользователь:** {interaction.user.mention}\n**ID пользователя:** {interaction.user.id}\n**Дата регистрации:** {interaction.user.created_at.strftime('%d-%m-%Y')}", timestamp=datetime.now(), color=discord.Color.blurple())
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.add_field(name="Имя", value=self.name.value, inline=False)
        embed.add_field(name="Возраст", value=self.age.value, inline=False)
        embed.add_field(name="Цель пребывания на сервере", value=self.purpose.value, inline=False)
        embed.set_footer(text=f"Заявка создана: {datetime.now().strftime('%H:%M %d-%m-%Y')}")

        view = ModeratorView(user_id=str(interaction.user.id))
        message = await bot.get_channel(moderation_channel_id).send(embed=embed, view=view)
        view.message = message

        await interaction.response.send_message("Спасибо за заполнение анкеты! Ожидайте решения модератора.", ephemeral=True)

class ModeratorView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.manage_messages:
            guild = interaction.guild
            member = guild.get_member(int(self.user_id))  # Получаем Member
            role = interaction.guild.get_role(verified_role_id)

            if role is None:
                await interaction.response.send_message("Роль верификации не найдена.", ephemeral=True)
                return

            try:
                await member.add_roles(role)  # Используем Member для добавления роли
                embed = self.message.embeds[0]
                embed.description += f"\n\n**Решение:** Заявка принята\n**Модератор:** {interaction.user.mention}"
                await self.message.edit(embed=embed)

                embed_dm = discord.Embed(title="Поздравляю!", description=f"Ваша заявка на верификацию была принята. Теперь вы можете полноценно пользоваться сервером.", color=discord.Color.green())
                await member.send(embed=embed_dm)

                await interaction.response.send_message("Вы приняли заявку пользователя.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Произошла ошибка при добавлении роли: {e}", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red)
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.manage_messages:
            modal = DeclineReasonModal(user_id=self.user_id, message=self.message, view=self)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("У вас нет прав для выполнения этого действия.", ephemeral=True)

class DeclineReasonModal(Modal, title="Причина отклонения заявки"):
    reason = TextInput(label="Причина", style=discord.TextStyle.long, required=True)

    def __init__(self, user_id, message, view):
        super().__init__()
        self.user_id = user_id
        self.message = message
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        user = bot.get_user(int(self.user_id))
        embed = self.message.embeds[0]
        embed.description += f"\n\n**Решение:** Заявка отклонена\n**Модератор:** {interaction.user.mention}\n**Причина:** {self.reason.value}"
        await self.message.edit(embed=embed)

        embed_dm = discord.Embed(title="К сожалению, ваша заявка на верификацию была отклонена. Причина:", description=f"{self.reason.value}", color=discord.Color.red())
        await user.send(embed=embed_dm)

        await interaction.response.send_message("Вы отклонили заявку пользователя.", ephemeral=True)

@bot.event
async def on_ready():
    verification_channel = bot.get_channel(verification_channel_id)
    embed = discord.Embed(title="Добро пожаловать!", description="Пожалуйста, нажмите на кнопку ниже, чтобы начать процесс верификации.", color=discord.Color.blurple())
    view = View()
    view.add_item(Button(label="Начать верификацию", custom_id="start_verification"))
    message = await verification_channel.send(embed=embed, view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data["custom_id"] == "start_verification":
        await interaction.response.send_modal(VerificationModal())

@bot.tree.command(name="test_command", description="Тестовая команда для проверки работы бота")
@app_commands.checks.has_any_role("Администратор", "Модератор")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("Команда выполнена успешно!", ephemeral=True)

bot.run('TOKEN')  # Замените 'YOUR_BOT_TOKEN_HERE' на ваш токен бота           
