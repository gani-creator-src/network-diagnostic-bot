import os
import re
import time
import asyncio
import locale
import subprocess
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("TOKEN")

HOST_RE = re.compile(r"^[a-zA-Z0-9.\-]{1,253}$")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    raw = r.stdout or r.stderr
    for enc in ("utf-8", "cp866", "cp1251", locale.getpreferredencoding()):
        try:
            return raw.decode(enc).strip() or "Нәтиже бос."
        except UnicodeDecodeError:
            continue
    return raw.decode("cp866", errors="replace").strip() or "Нәтиже бос."


def explain(command_name, result):
    prompt = (
        f"Мына {command_name} нәтижесін қарапайым қазақ тілінде түсіндір: "
        f"желі жақсы ма, ақау бар ма? 3-4 сөйлемнен аспасын.\n\n{result}"
    )
    last_error = None
    for model in MODELS:
        for attempt in range(2):
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                return resp.text
            except Exception as e:
                last_error = e
                if "503" in str(e) or "429" in str(e):
                    time.sleep(2)
                    continue
                break
    raise last_error


def simple_explain(command_name, out):
    low = out.lower()
    if "100% потерь" in low or "100% loss" in low:
        return "Ақау бар: барлық пакет жоғалды, хост қолжетімсіз."
    if "превышен интервал" in low or "timed out" in low:
        return "Ақау бар: сұраныс жауапсыз қалды, кейбір түйіндер жауап бермейді."
    if command_name == "ping" and ("0% потерь" in low or "0% loss" in low):
        return "Желі жақсы: пакеттер жоғалған жоқ."
    if command_name == "traceroute" and "трассировка завершена" in low:
        return "Маршрут сәтті аяқталды: пакет межелі жерге жетті."
    if command_name == "dns" and "address" in low:
        return "DNS жұмыс істейді: домен IP-мекенжайға айналды."
    return "Нәтиже келді, бірақ автоматты түсіндіру мүмкін болмады."


async def send_result(update: Update, command_name, out):
    await update.message.reply_text(out[-3500:])
    try:
        answer = await asyncio.to_thread(explain, command_name, out)
        await update.message.reply_text("🤖 Түсіндірме (ЖИ):\n" + answer)
    except Exception as e:
        print("ЖИ қатесі:", e)
        await update.message.reply_text(
            "ℹ️ Түсіндірме (ЖИ уақытша қолжетімсіз):\n" + simple_explain(command_name, out)
        )


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Сәлем! Командалар:\n/ping google.com\n/trace google.com\n/dns google.com"
    )


async def ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    host = ctx.args[0] if ctx.args else ""
    if not HOST_RE.match(host):
        await update.message.reply_text("Хост атауын дұрыс жаз. Мысалы: /ping google.com")
        return
    out = await asyncio.to_thread(run, ["ping", "-n", "4", host])
    await send_result(update, "ping", out)


async def trace(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    host = ctx.args[0] if ctx.args else ""
    if not HOST_RE.match(host):
        await update.message.reply_text("Хост атауын дұрыс жаз")
        return
    out = await asyncio.to_thread(run, ["tracert", host])
    await send_result(update, "traceroute", out)


async def dns(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    host = ctx.args[0] if ctx.args else ""
    if not HOST_RE.match(host):
        await update.message.reply_text("Хост атауын дұрыс жаз")
        return
    r = await asyncio.to_thread(
        subprocess.run, ["nslookup", host], capture_output=True, timeout=30
    )
    out = r.stdout.decode("cp1251", errors="replace")
    await send_result(update, "dns", out)


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("trace", trace))
app.add_handler(CommandHandler("dns", dns))
print("Бот жұмыс істеп тұр...")
app.run_polling()