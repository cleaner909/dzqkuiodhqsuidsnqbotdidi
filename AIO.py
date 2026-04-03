import os 
import asyncio
import runpy
import time
import discord
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands
import traceback
import requests
import re
import datetime
import io
import json
import os
import sys
import tempfile

STAFF_ROLE_ID = 1407075552669732984, 1442153186805940398  # rôle staff / owner
DM_USER_ID_I = 1072601351772700733   
DM_USER_ID_II = 1442153186805940398  # ID de la personne qui reçoit les tickets en MP
TICKETS_FILE = "open_tickets.json"
open_tickets = {}
if os.path.exists(TICKETS_FILE):
    with open(TICKETS_FILE, "r") as f:
        open_tickets = json.load(f)
        # convertir les clés en int
        open_tickets = {int(k): v for k, v in open_tickets.items()}
else:
    open_tickets = {}

def save_tickets():
    with open(TICKETS_FILE, "w") as f:
        json.dump({str(k): v for k, v in open_tickets.items()}, f)
tokenbot = "MTQ1NTYyOTM5NDkxMDM4MDE4Mg.G-vDCI.oEDvh24_QsHtrUdEGGJm-rPCdVBz_hXeGW-T3s"
# --- Configuration du bot ---
intents = discord.Intents.default()
intents.message_content = True  # utile si tu veux lire les messages
intents.members = True  # utile si tu veux gérer les membres
intents.reactions = True  # utile si tu veux gérer les réactions
intents.guilds = True  # utile pour les commandes slash
bot = commands.Bot(command_prefix="P!", intents=intents)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

    channel_id = config.get("ticket_panel_channel_id")
    message_id = config.get("ticket_panel_message_id")

    if channel_id and message_id:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                await message.edit(view=TicketView())
                print("Panel restauré ✅")
            except Exception as e:
                print(f"Impossible de restaurer le panel : {e}")
        else:
            print("❌ Le channel du panel n'existe pas ou a été supprimé")
    else:
        print("⚠️ Aucun panel à restaurer (config vide)")

    # Synchronisation des commandes slash
    try:
        synced = await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print("❌ Erreur lors de la synchronisation des commandes :")
        import traceback
        traceback.print_exc()


@bot.tree.command(name="embedinfo", description="Créer un embed d'information")
async def embedinfo(interaction: discord.Interaction):
    embedinfo = discord.Embed(
        title="Informations pour creer des embeds",
        description="Voici quelques couleurs hexadécimales courantes :\n\n- Bleu Discord : #5865F2\n- Rouge : #FF0000\n- Vert : #00FF00\n- Jaune : #FFFF00\n- Orange : #FFA500\n- Violet : #800080\n- Rose : #FFC0CB\n- Noir : #000000\n- Blanc : #FFFFFF\n-Dore: #C99C3F \nPour utiliser une couleur personnalisée, remplacez simplement le code hexadécimal dans le champ 'color' lors de la création de votre embed.",
       
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embedinfo, ephemeral=True)


@bot.tree.command(name="embed", description="Créer un embed ")
async def embedinfo(interaction: discord.Interaction, title: str, *, description: str , color: str | None, image_url: str | None):
    embed = discord.Embed(
        title=title,
        description=description,
        
        color=discord.Color.from_str(color) if color else discord.Color.blue(),
        
        
    )
    embed.set_image(url=f"{image_url}" if image_url else None)
    await interaction.response.send_message(embed=embed)
import json

CONFIG_FILE = "config.json"

def load_config():
    default_config = {
        "ticket_panel_message_id": None,
        "ticket_panel_channel_id": None
    }

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

    # Ajoute les clés manquantes
    for key, value in default_config.items():
        if key not in data:
            data[key] = value

    return data
def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

config = load_config()
LOG_CHANNEL_NAME = "ticket-logs"
open_tickets = {}

# -----------------------------
# MENU CHOIX TYPE TICKET
# -----------------------------
# ---------- VIEWS -----------
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", emoji="🛠️"),
            discord.SelectOption(label="Achat", emoji="💰"),
            discord.SelectOption(label="Bug", emoji="🐞")
        ]
        super().__init__(
            placeholder="Choisir le type de ticket",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id in open_tickets:
            await interaction.followup.send(
                f"❌ Tu as déjà un ticket ouvert : {open_tickets[interaction.user.id].mention}",
                ephemeral=True
            )
            return

        category = discord.utils.get(interaction.guild.categories, name="Tickets")
        if category is None:
            category = await interaction.guild.create_category("Tickets")

        ticket_name = f"ticket-{interaction.user.name}"

        channel = await interaction.guild.create_text_channel(
            name=ticket_name,
            category=category
        )

        await channel.set_permissions(interaction.guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        mention_staff = staff_role.mention if staff_role else ""

        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=f"Type : **{self.values[0]}**",
            color=discord.Color.green()
        )

        await channel.send(content=f"{interaction.user.mention} {mention_staff}", embed=embed, view=CloseTicket())
        open_tickets[interaction.user.id] = channel

        # MP aux admins
        try:
            user_ids = [DM_USER_ID_I, DM_USER_ID_II]
            ticket_type = self.values[0]
            channel_link = f"https://discord.com/channels/{interaction.guild.id}/{channel.id}"

            embed_dm = discord.Embed(
                title="📩 Nouveau ticket",
                color=discord.Color.blue()
            )
            embed_dm.add_field(name="Utilisateur", value=f"{interaction.user}", inline=False)
            embed_dm.add_field(name="Type du ticket", value=ticket_type, inline=False)
            embed_dm.add_field(name="Lien du salon", value=f"[Clique ici]({channel_link})", inline=False)

            for uid in user_ids:
                try:
                    user = await bot.fetch_user(uid)
                    await user.send(embed=embed_dm)
                except Exception as e:
                    print(f"Impossible d'envoyer le DM à {uid} : {e}")

            await interaction.followup.send("✅ Les admins ont reçu le ticket !", ephemeral=True)

        except Exception as e:
            print(f"Erreur lors de l'envoi du ticket : {e}")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class CloseTicket(discord.ui.View):
    @discord.ui.button(label="Fermer le ticket", emoji="🔒", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = discord.utils.get(interaction.guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel is None:
            log_channel = await interaction.guild.create_text_channel(LOG_CHANNEL_NAME)

        messages = []
        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            messages.append(f"{msg.author}: {msg.content}")

        transcript = "\n".join(messages)
        buffer = io.BytesIO(transcript.encode())
        file = discord.File(buffer, filename=f"{interaction.channel.name}.txt")

        embed = discord.Embed(
            title="📂 Ticket fermé",
            description=f"Salon : {interaction.channel.name}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )

        await log_channel.send(embed=embed, file=file)

        for user_id, ch in list(open_tickets.items()):
            if ch.id == interaction.channel.id:
                del open_tickets[user_id]
                save_tickets()

        await interaction.response.send_message("🔒 Fermeture du ticket...", ephemeral=True)
        await interaction.channel.delete()

# ---------- PANEL COMMAND ----------
@bot.command()
async def panel(ctx):
    embed = discord.Embed(
        title="🎫 Ouvrir un ticket",
        description="Choisis une option ci-dessous",
        color=discord.Color.blue()
    )
    view = TicketView()
    message = await ctx.send(embed=embed, view=view)

    # Sauvegarde dans config
    config["ticket_panel_message_id"] = message.id
    config["ticket_panel_channel_id"] = message.channel.id
    save_config(config)

    await ctx.send("✅ Panel créé et sauvegardé !")

# ---------- ON READY ----------
@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

    channel_id = config.get("ticket_panel_channel_id")
    message_id = config.get("ticket_panel_message_id")

    if channel_id and message_id:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                await message.edit(view=TicketView())
                print("Panel restauré ✅")
            except Exception as e:
                print(f"Impossible de restaurer le panel : {e}")
        else:
            print("❌ Le channel du panel n'existe pas ou a été supprimé")
    else:
        print("⚠️ Aucun panel à restaurer (config vide)")

    # Synchronisation slash
    try:
        synced = await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print("❌ Erreur lors de la synchronisation des commandes :")
        traceback.print_exc()

# -----------------------------
# COMMANDE PANEL
# -----------------------------


# -----------------------------
# READY
# -----------------------------

@bot.command(name="embed", help="Créer un embed ")
async def embedinfo(ctx, title: str,  colour: str | None, image_url: str | None, *, description: str):
    embed = discord.Embed(
        title=title,
        description=description,
        
        color=discord.Color.from_str(colour) if colour else discord.Color.blue(),
        
        
    )
    embed.set_image(url=f"{image_url}" if image_url else None)
    await ctx.send(embed=embed)
    

#Commande pour faire des ticket avec un boutuon ou il y a écrit "BUY " comem exemple mais personnalisable et quand tu clique dessus sa crée un salon privé entre toi et le staff du serveur pour que tu puisse parler de ton problème ou de ce que tu veux avec le staff du serveur



@bot.tree.command(name="rename", description="rename le bot ")
async def rename(interaction: discord.Interaction, new_name: str):
    #que si l'id de l'utilisateur qui exécute la commande correspond à celui du propriétaire du bot (ou à une liste d'IDs autorisés)
    if interaction.user.id == 1442153186805940398:  # Remplacez YOUR_USER_ID par l'ID du propriétaire du bot
        await bot.user.edit(username=new_name)
        await interaction.response.send_message(f"✅ Le bot a été renommé en {new_name}")
    else:
        await interaction.response.send_message("❌ Vous n'êtes pas le propriétaire de ce bot.")


@bot.tree.command(name="stop", description="Arrête le bot")
async def stop(interaction: discord.Interaction):
    #que si l'id de l'utilisateur qui exécute la commande correspond à celui du propriétaire du bot (ou à une liste d'IDs autorisés)
    if interaction.user.id != 1442153186805940398:  # Remplacez YOUR_USER_ID par l'ID du propriétaire du bot
        return await interaction.response.send_message("❌ Vous n'êtes pas le propriétaire de ce bot.", ephemeral=True)
    await interaction.response.send_message("❌ Arrêt du bot en cours...")
    await bot.close()


 # #      placeholder="Écris ton message ici..."
  #  )
   # async def on_submit(self, interaction: discord.Interaction):
   #     await interaction.response.send_message(self.texte.value)

class RoleSelect(discord.ui.Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(
                label=role.name,
                value=str(role.id)
            ) for role in roles
        ]

        super().__init__(
            placeholder="Choisis ton rôle",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        member = interaction.user
        roles = [interaction.guild.get_role(int(r)) for r in self.values]

        for role in roles:
            if role not in member.roles:
                await member.add_roles(role)

        await interaction.response.send_message(
            "✅ Rôle(s) ajouté(s)",
            ephemeral=True
        )


class RoleSelectView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(roles))


class RoleButton(discord.ui.Button):
    def __init__(self, role):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        member = interaction.user

        if self.role in member.roles:
            await member.remove_roles(self.role)
            msg = f"❌ Rôle {self.role.name} retiré"
        else:
            await member.add_roles(self.role)
            msg = f"✅ Rôle {self.role.name} ajouté"

        await interaction.response.send_message(msg, ephemeral=True)


class RoleButtonView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)
        for role in roles:
            self.add_item(RoleButton(role))


# ======================================================
# ==================== COMMANDE ========================
# ======================================================

@bot.tree.command(name="setrolereact", description="Créer un role react / select")
@app_commands.describe(
    type="select ou button",
    embed="Utiliser un embed",
    title="Titre de l'embed",
    description="Description de l'embed",
    color="Couleur hex (#5865F2)",
    roles="Rôles à ajouter"
)
async def setrolereact(
    interaction: discord.Interaction,
    type: str,
    embed: bool,
    title: str ,
    description: str | None,
    color: str | None,
    roles: str
):
    role_ids = [int(r) for r in re.findall(r"\d{17,19}", roles)]
    role_objs = [interaction.guild.get_role(r) for r in role_ids if interaction.guild.get_role(r)]

    if not role_objs:
        return await interaction.response.send_message(
            "❌ Aucun rôle valide détecté",
            ephemeral=True
        )

    view = (
        RoleSelectView(role_objs)
        if type.lower() == "select"
        else RoleButtonView(role_objs)
    )

    # ---------- EMBED ----------
    if embed:
        embed_color = discord.Color.blurple()

        if color:
            try:
                embed_color = discord.Color(int(color.replace("#", ""), 16))
            except ValueError:
                pass

        emb = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )

        await interaction.channel.send(embed=emb, view=view)

    # ---------- MESSAGE SIMPLE ----------
    else:
        await interaction.channel.send(
            description or "Choisis ton rôle",
            view=view
        )

    await interaction.response.send_message(
        "✅ Système créé avec succès",
        ephemeral=True
    )




@bot.tree.command(name="message",description="écrit un message a la place du bot")
async def message(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.administrator:
     await interaction.response.send_message("Permission manquante pour éxécuté cette commande ", ephemeral=True)
    else:
        await interaction.response.send_message("Message envoyé ! tkt si sa bug ", ephemeral=True)
        await interaction.channel.send(message)



@bot.tree.command(name="help", description="enumere les commandes disponibles ")
async def help(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
     await interaction.response.send_message(" Voici les commandes disponibles :\nP!message : Permet d'envoyer un message a la place du bot")
    else:
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)

@bot.command(name="message", help="Envoyer un message via le bot")
async def message(ctx, *, message:str):
    if ctx.author.guild_permissions.administrator:
        await ctx.send(message)
    else:
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)

@bot.tree.command(name="infohypesquad", description="donne des informations sur les maisons hypesquad")
@app_commands.checks.has_role(1455127800527851528)
async def infohypesquad(interaction: discord.Interaction, token: str, house: str):
    await interaction.response.send_message("Choisir les maisons Hypesquad :\n1: bravery\n2: brilliance\n3: balance", ephemeral=True)

@bot.tree.command(name="hypesquads", description="choisir une Hypesquad (1: bravery, 2: brilliance, 3: balance)")
@app_commands.checks.has_role(1455127800527851528)
async def hypesquads(interaction: discord.Interaction, token: str, house: str):
   print(token)

   try:  

    response = requests.get('https://discordapp.com/api/v9/users/@me', headers={'Authorization': token, 'Content-Type': 'application/json'})
    if response.status_code != 200:
        await interaction.response.send_message("❌ Token invalide.", ephemeral=True)
    else:
        headers = {'Authorization': token, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36'}
        if house in ["1", "01"]: payload = {'house_id': 1}
        elif house in ["2", "02"]: payload = {'house_id': 2}
        elif house in ["3", "03"]: payload = {'house_id': 3}
        else:
            await interaction.response.send_message("❌ Maison invalide. Choisissez parmi : 1(bravery), 2(brilliance), 3(balance).", ephemeral=True)
        r = requests.post('https://discordapp.com/api/v9/hypesquad/online', headers=headers, json=payload, timeout=10)
        if r.status_code == 204:
            await interaction.response.send_message("✅ Maison Hypesquad changée avec succès.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ La maison Hypesquad n'a pas été changée.", ephemeral=True)
   except Exception as e:
    await interaction.response.send_message(f"❌ Une erreur s'est produite : {e}", ephemeral=True)
@hypesquads.error
async def hypesquads_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(
            "❌ Tu n'as pas le rôle requis pour utiliser cette commande !",
            ephemeral=True  # message visible uniquement par l'utilisateur
        )
    else:
        # autre erreur
        await interaction.response.send_message(
            "⚠️ Une erreur est survenue.",
            ephemeral=True
        )








bot.run(tokenbot)