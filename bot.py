import discord
from discord.ext import commands
import os
import random
import asyncio
from discord.ext.commands import CheckFailure
from dotenv import load_dotenv
import os


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


# CONFIGURACION
CARPETA_CUENTAS = 'cuentas'
ROL_SendAccount = 'SendAccount'
DUEÑO_ID = 453802243234201600  # Reemplaza con tu ID de Discord
VOUCH_CHANNEL_ID = 1373798620591165503  # Reemplaza con el ID de tu canal de vouches

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Decorador para restringir comandos a moderadores
def solo_SendAccount():
    async def predicate(ctx):
        return any(rol.name == ROL_SendAccount for rol in ctx.author.roles)
    return commands.check(predicate)

# Manejo de errores por permisos
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # no mostrar nada si el comando no existe

    if isinstance(error, CheckFailure):
        await ctx.send("🚫 No tienes permisos para usar este comando.")
    else:
        raise error


# Comando STOCK
@bot.command()
@solo_enviadores()
async def stock(ctx):
    try:
        if not os.path.exists(CARPETA_CUENTAS):
            os.makedirs(CARPETA_CUENTAS)
            await ctx.send("⚠️ No se encontraron archivos de cuentas. Se creó la carpeta vacía.")
            return

        servicios = []
        for archivo in os.listdir(CARPETA_CUENTAS):
            if archivo.endswith(".txt"):
                ruta = os.path.join(CARPETA_CUENTAS, archivo)
                with open(ruta, "r") as f:
                    lineas = f.readlines()
                    cantidad = len([l for l in lineas if l.strip() != ""])
                    nombre = archivo.replace(".txt", "").capitalize()
                    servicios.append(f"• {nombre}: {cantidad} cuenta{'s' if cantidad != 1 else ''}")

        if servicios:
            mensaje = "📦 **Stock actual:**\n\n" + "\n".join(servicios)
        else:
            mensaje = "🚫 No se encontraron archivos de cuentas."

        await ctx.send(mensaje)

    except Exception as e:
        await ctx.send("⚠️ Hubo un error al verificar el stock.")
        print(f"[ERROR en !stock]: {e}")

# ENVIO DE CUENTA
async def enviar_cuenta(servicio, ctx, usuario_objetivo):
    archivo = f"{CARPETA_CUENTAS}/{servicio}.txt"

    # Crear carpeta y archivo si no existen
    os.makedirs(CARPETA_CUENTAS, exist_ok=True)
    if not os.path.exists(archivo):
        with open(archivo, 'w') as f:
            pass  # crea archivo vacío
        await ctx.send(f"⚠️ Archivo de `{servicio}` no existía y fue creado. Aún no contiene cuentas.")
        return

    with open(archivo, 'r') as f:
        cuentas = f.readlines()

    if not cuentas:
        await ctx.send(f"🚫 No quedan cuentas disponibles para `{servicio}`.")
        return

    cuenta_linea = random.choice(cuentas)
    cuenta = cuenta_linea.strip()
    cuentas.remove(cuenta_linea)

    with open(archivo, 'w') as f:
        f.writelines(cuentas)

    nombre_formateado = servicio.capitalize()

    try:
        mensaje_enviado = await usuario_objetivo.send(
            f"✅ Legit ACC - {nombre_formateado} | Lifetime ✅\n\n||{cuenta}||"
        )
        await mensaje_enviado.add_reaction("✅")
        await mensaje_enviado.add_reaction("❌")

        await ctx.send(
            f"✅ Cuenta de {nombre_formateado} enviada por DM a {usuario_objetivo.mention}."
        )

        dueño = await bot.fetch_user(DUEÑO_ID)
        await dueño.send(
            f"📦 **Cuenta enviada:** {nombre_formateado}\n"
            f"👤 **Cliente:** {usuario_objetivo.mention}\n"
            f"🛠️ **Enviada por:** {ctx.author.mention}\n"
            f"🔑 **Cuenta:** ||{cuenta}||"
        )

        await esperar_reaccion_vouch(bot, mensaje_enviado, usuario_objetivo, ctx.channel, ctx.author, cuenta, servicio)

    except discord.Forbidden:
        await ctx.send(
            f"❗ {usuario_objetivo.mention} no fue posible contactarte por DM. "
            f"Procederé a enviarte la cuenta por este canal."
        )

        mensaje_enviado = await ctx.send(
            f"✅ Legit ACC - {nombre_formateado} | Lifetime ✅\n\n||{cuenta}||"
        )
        await mensaje_enviado.add_reaction("✅")
        await mensaje_enviado.add_reaction("❌")

        dueño = await bot.fetch_user(DUEÑO_ID)
        await dueño.send(
            f"⚠️ *DM fallido: cuenta enviada en canal público.*\n"
            f"📦 **Cuenta enviada:** {nombre_formateado}\n"
            f"👤 **Cliente:** {usuario_objetivo.mention}\n"
            f"🛠️ **Enviada por:** {ctx.author.mention}\n"
            f"🔑 **Cuenta:** ||{cuenta}||"
        )

        await esperar_reaccion_vouch(bot, mensaje_enviado, usuario_objetivo, ctx.channel, ctx.author, cuenta, servicio)

# REACCIONES Y VOUCH/RECLAMOS
async def esperar_reaccion_vouch(bot, mensaje, usuario, canal_origen, SendAccount, cuenta, servicio):
    def check_reaccion(reaction, user):
        return (
            user == usuario
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == mensaje.id
        )

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=300.0, check=check_reaccion)

        if str(reaction.emoji) == "✅":
            canal_vouch = bot.get_channel(VOUCH_CHANNEL_ID)
            if canal_vouch:
                await canal_vouch.send(f"✅ Vouch {usuario.mention} Legit")

        elif str(reaction.emoji) == "❌":
            await canal_origen.send(
                f"❗ {usuario.mention} ha marcado que hay un problema con la cuenta de **{servicio.capitalize()}**.\n"
                f"📩 Por favor, escribe aquí el problema que estás presentando."
            )

            def check_mensaje(m):
                return m.author == usuario and m.channel == canal_origen

            try:
                mensaje_problema = await bot.wait_for("message", timeout=300.0, check=check_mensaje)

                await canal_origen.send(
                    f"📣 {SendAccount.mention}, {usuario.mention} reportó un problema con su cuenta de **{servicio.capitalize()}**:\n"
                    f"📝 \"{mensaje_problema.content}\"\n"
                    f"🔑 Cuenta entregada: ||{cuenta}||"
                )

            except asyncio.TimeoutError:
                await canal_origen.send(
                    f"⌛ {usuario.mention}, no se recibió ninguna descripción del problema en 5 minutos."
                )

    except asyncio.TimeoutError:
        pass

# COMANDOS DE ENVIO
@bot.command()
@solo_SendAccount()
async def senddisney(ctx, usuario: discord.Member):
    await enviar_cuenta('disney', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendhbo(ctx, usuario: discord.Member):
    await enviar_cuenta('hbo', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendsteam(ctx, usuario: discord.Member):
    await enviar_cuenta('steam', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendrockstar(ctx, usuario: discord.Member):
    await enviar_cuenta('rockstar', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendtunnelbear(ctx, usuario: discord.Member):
    await enviar_cuenta('tunnelbear', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendcapcut(ctx, usuario: discord.Member):
    await enviar_cuenta('capcut', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendduolingo(ctx, usuario: discord.Member):
    await enviar_cuenta('duolingo', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendvodafone(ctx, usuario: discord.Member):
    await enviar_cuenta('vodafone', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendparamount(ctx, usuario: discord.Member):
    await enviar_cuenta('paramount', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendamazon(ctx, usuario: discord.Member):
    await enviar_cuenta('amazon', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def senddazn(ctx, usuario: discord.Member):
    await enviar_cuenta('dazn', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def sendcrunchyroll(ctx, usuario: discord.Member):
    await enviar_cuenta('crunchyroll', ctx, usuario)

@bot.command()
@solo_SendAccount()
async def restock(ctx, servicio: str):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send(f"📩 {ctx.author.mention}, envía ahora las cuentas de `{servicio}` (una por línea). Tienes 2 minutos.")

    try:
        mensaje = await bot.wait_for("message", timeout=120.0, check=check)
        nuevas_cuentas = [linea.strip() for linea in mensaje.content.split("\n") if ":" in linea]

        if not nuevas_cuentas:
            await ctx.send("⚠️ No se detectaron cuentas válidas (formato `usuario:clave`).")
            return

        archivo = f"{CARPETA_CUENTAS}/{servicio.lower()}.txt"

        if not os.path.exists(archivo):
            await ctx.send(f"❌ El servicio `{servicio}` no existe. Verifica el nombre.")
            return

        with open(archivo, "r") as f:
            existentes = set(linea.strip() for linea in f if ":" in linea)

        nuevas_unicas = [c for c in nuevas_cuentas if c not in existentes]

        with open(archivo, "a") as f:
            for cuenta in nuevas_unicas:
                f.write(cuenta + "\n")

        await ctx.send(
            f"✅ {len(nuevas_unicas)} cuenta(s) nuevas agregadas al stock de `{servicio.capitalize()}`. "
            f"{len(nuevas_cuentas) - len(nuevas_unicas)} duplicadas fueron ignoradas."
        )

    except asyncio.TimeoutError:
        await ctx.send("⌛ Tiempo agotado. No se recibió ningún mensaje con cuentas.")


bot.run(TOKEN)
