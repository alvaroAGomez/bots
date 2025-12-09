import os
import logging
from io import StringIO

import requests
import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)
from telegram.error import InvalidToken

# === CONFIGURACIÓN ===

# Token leído desde variable de entorno (Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# URL de IOL
URL_IOL_WEB = "https://iol.invertironline.com/mercado/cotizaciones/argentina/cauciones"

# Estado global dinámico
configuracion = {
    "TNA_OBJETIVO": 25.0,  # Valor inicial por defecto
    "CHAT_ID": None,       # Se guarda cuando hables con el bot
}

# Logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# === 1. LÓGICA DE SCRAPING ===

def obtener_oportunidades(tasa_minima: float):
    """
    Scrapea IOL y devuelve una lista de textos con las oportunidades
    que superan la tasa_minima y con plazo <= 30 días.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(URL_IOL_WEB, headers=headers, timeout=10)
        response.raise_for_status()

        html_data = StringIO(response.text)
        tablas = pd.read_html(html_data)

        if not tablas:
            return []

        df = tablas[0]
        df.columns = df.columns.str.lower()

        col_tasa = "tasa tomadora"
        col_plazo = "plazo"
        col_monto = "monto contado"

        if col_tasa not in df.columns or col_plazo not in df.columns:
            logging.error("Cambió la estructura de la tabla en IOL")
            return []

        oportunidades = []

        for _, row in df.iterrows():
            try:
                # Tasa
                raw_tasa = str(row[col_tasa])
                tasa_str = (
                    raw_tasa.replace("%", "")
                    .replace(".", "")
                    .replace(",", ".")
                    .strip()
                )
                tasa = float(tasa_str)

                # Plazo
                raw_plazo = (
                    str(row[col_plazo])
                    .lower()
                    .replace("días", "")
                    .replace("dias", "")
                    .replace("d", "")
                    .strip()
                )
                try:
                    dias = int(float(raw_plazo))
                except Exception:
                    dias = raw_plazo

                # Filtro: TNA mínima + plazo máximo 30 días
                if isinstance(dias, int) and tasa >= tasa_minima and dias <= 30:
                    oportunidades.append(
                        f"✅ *{dias} DÍAS* | Tasa: *{tasa}%*"
                    )

            except Exception:
                continue

        return oportunidades

    except Exception as e:
        logging.error(f"Error scraping IOL: {e}")
        return []


# === 2. COMANDOS DEL BOT ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    configuracion["CHAT_ID"] = chat_id

    await update.message.reply_text(
        (
            f"¡Hola {user.first_name}! 🤖\n"
            f"Soy tu bot de Cauciones IOL.\n\n"
            f"📊 Tasa objetivo actual: *{configuracion['TNA_OBJETIVO']}%*\n\n"
            f"Comandos:\n"
            f"/set 30  -> Cambia la alerta a 30%\n"
            f"/ahora   -> Revisa el mercado ya\n"
            f"/auto    -> Escaneo automático (cada 5 min)\n"
        ),
        parse_mode="Markdown",
    )


async def set_tna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /set <valor>"""
    try:
        nuevo_valor = float(context.args[0])
        configuracion["TNA_OBJETIVO"] = nuevo_valor
        await update.message.reply_text(
            f"✅ Alerta actualizada a *{nuevo_valor}%* TNA.",
            parse_mode="Markdown",
        )
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Uso: `/set 28.5`", parse_mode="Markdown")


async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ahora"""
    tasa_actual = configuracion["TNA_OBJETIVO"]
    await update.message.reply_text(
        f"🔎 Buscando cauciones >= {tasa_actual}% con período de hasta 30 días..."
    )

    ops = obtener_oportunidades(tasa_actual)

    if ops:
        msg = f"💰 *ALERTA MANUAL* (> {tasa_actual}%)\n\n" + "\n".join(ops)
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"📉 Nada supera el {tasa_actual}% ahora.")


# === 3. TAREAS AUTOMÁTICAS (JOB QUEUE) ===

async def auto_scan(context: ContextTypes.DEFAULT_TYPE):
    """Tarea periódica: revisa el mercado y manda alerta si hay oportunidades."""
    chat_id = configuracion["CHAT_ID"]
    tasa_actual = configuracion["TNA_OBJETIVO"]

    if not chat_id:
        return

    ops = obtener_oportunidades(tasa_actual)

    if ops:
        msg = f"🔔 *ALERTA AUTOMÁTICA* (> {tasa_actual}%)\n\n" + "\n".join(ops)
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")


async def activar_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /auto: activa el escaneo cada 5 minutos."""
    chat_id = update.effective_chat.id
    configuracion["CHAT_ID"] = chat_id

    job_queue = context.job_queue
    if not job_queue:
        await update.message.reply_text(
            "❌ No se pudo acceder a JobQueue. Revisa la instalación del bot."
        )
        return

    # Limpiar jobs anteriores
    for job in job_queue.jobs():
        job.schedule_removal()

    # 300 segundos = 5 minutos
    job_queue.run_repeating(auto_scan, interval=300, first=10)

    await update.message.reply_text("✅ Alerta automática activada (cada 5 min).")


# === 4. MAIN ===

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError(
            "La variable de entorno TELEGRAM_TOKEN no está configurada."
        )

    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("set", set_tna))
        application.add_handler(CommandHandler("ahora", check_now))
        application.add_handler(CommandHandler("auto", activar_auto))

        logging.info("🤖 Bot iniciado, escuchando comandos...")
        application.run_polling()

    except InvalidToken:
        logging.error("El token de Telegram es inválido.")
        raise
    except Exception as e:
        logging.error(f"Error inesperado al iniciar el bot: {e}")
        raise


if __name__ == "__main__":
    main()
