import discord
from discord.ext import commands
import requests
import asyncio
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1411093722426507366
GROUP_ID = 13766

LINKS_FILE = "links.json"

RANK_MAP = {
    "jade": "Jade",
    "topaz": "Red Topaz",
    "sapphire": "Sapphire",
    "emerald": "Emerald",
    "ruby": "Ruby",
    "diamond": "Diamond",
    "dragonstone": "Dragonstone",
    "onyx": "Onyx",
    "zenyte": "Zenyte",
    "hellcat": "Hellcat",
    "destroyer": "Destroyer",
    "beast": "Beast"
}

# =========================
# STORAGE
# =========================

def load_links():
    if not os.path.exists(LINKS_FILE):
        return {}
    with open(LINKS_FILE, "r") as f:
        return json.load(f)

def save_links(data):
    with open(LINKS_FILE, "w") as f:
        json.dump(data, f, indent=4)

links = load_links()

# =========================
# WOM API
# =========================

def get_group_members():
    url = f"https://api.wiseoldman.net/v2/groups/{GROUP_ID}"
    res = requests.get(url)

    try:
        data = res.json()
    except:
        print("API decode error")
        return []

    group = data.get("group", data)
    return group.get("memberships", [])

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# COMMANDS
# =========================

@bot.command()
async def link(ctx, *, username):
    links[str(ctx.author.id)] = username
    save_links(links)
    await ctx.send(f"✅ Linked to {username}")
    await update_once()

@bot.command()
async def sync(ctx):
    await ctx.send("🔄 Syncing ranks...")
    await update_once()
    await ctx.send("✅ Done")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

# =========================
# CORE UPDATE FUNCTION (FIXED)
# =========================

async def update_once():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        return

    members = get_group_members()
    if not members:
        return

    wom_members = {}

    for m in members:
        try:
            name = m["player"]["username"].lower()
            wom_members[name] = m
        except:
            continue

    for user_id, rsn in links.items():
        member = guild.get_member(int(user_id))
        if not member:
            continue

        wom_member = wom_members.get(rsn.lower())
        if not wom_member:
            continue

        role_key = wom_member.get("role")
        if not role_key:
            continue

        role_name = RANK_MAP.get(role_key.lower())
        if not role_name:
            continue

        new_role = discord.utils.get(guild.roles, name=role_name)
        if not new_role:
            continue

        current_rank = None
        for r in member.roles:
            if r.name in RANK_MAP.values():
                current_rank = r.name
                break

        if current_rank == role_name:
            continue

        if current_rank:
            old_role = discord.utils.get(guild.roles, name=current_rank)
            if old_role:
                await member.remove_roles(old_role)

        await member.add_roles(new_role)
        print(f"{rsn}: {current_rank} → {role_name}")

# =========================
# LOOP
# =========================

async def update_loop():
    await bot.wait_until_ready()

    while True:
        try:
            await update_once()
        except Exception as e:
            print("Loop error:", e)

        await asyncio.sleep(3600)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(update_loop())

# =========================
# RUN
# =========================

bot.run(TOKEN)
