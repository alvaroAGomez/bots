import logging

from telegram import BotCommand
from telegram.ext import Application, ApplicationBuilder, CommandHandler, PicklePersistence

from cauciones_bot.config import Config
from cauciones_bot.handlers import BotHandlers
from cauciones_bot.services.analytics import AnalizadorMercado
from cauciones_bot.services.cache import CacheService
from cauciones_bot.services.cauciones import ServicioCauciones
from cauciones_bot.services.formatter import FormateadorMensajes
from cauciones_bot.services.history import HistorialService
from cauciones_bot.services.logger import TelegramLogger
from cauciones_bot.services.scraper import ScraperIOLWeb


def build_application() -> Application:
    logger = TelegramLogger()
    cache = CacheService()
    historial = HistorialService()
    scraper = ScraperIOLWeb(Config.IOL_URL, logger)
    analizador = AnalizadorMercado()
    formateador = FormateadorMensajes()

    servicio = ServicioCauciones(scraper, cache, historial, analizador, logger)
    handlers = BotHandlers(servicio, formateador)

    async def post_init(application: Application) -> None:
        comandos = [
            BotCommand("start", "Inicio"),
            BotCommand("ahora", "Ver Manual"),
            BotCommand("tendencia", "Grafico General"),
            BotCommand("mitendencia", "Grafico Custom"),
            BotCommand("set", "Set Alerta"),
            BotCommand("set_tendencia", "Set Dias Grafico"),
            BotCommand("stop", "Parar"),
        ]
        await application.bot.set_my_commands(comandos)
        await handlers.restaurar_tareas(application)

    persistence = PicklePersistence(filepath=Config.PERSISTENCE_FILE)
    app = (
        ApplicationBuilder()
        .token(Config.TELEGRAM_TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", handlers.cmd_start))
    app.add_handler(CommandHandler("set", handlers.cmd_set_tna))
    app.add_handler(CommandHandler("tiempo", handlers.cmd_set_tiempo))
    app.add_handler(CommandHandler("ahora", handlers.cmd_ahora))
    app.add_handler(CommandHandler("stop", handlers.cmd_stop))
    app.add_handler(CommandHandler("tendencia", handlers.cmd_tendencia_general))
    app.add_handler(CommandHandler("set_tendencia", handlers.cmd_set_tendencia))
    app.add_handler(CommandHandler("mitendencia", handlers.cmd_tendencia_custom))

    app.job_queue.run_repeating(
        handlers.recoleccion_global,
        interval=Config.HISTORY_MIN_INTERVAL_SECONDS,
        first=10,
        name="global_scraper",
    )

    logging.info("🤖 Bot V2.1 Iniciado (Hora Fix)")
    return app


def main() -> None:
    app = build_application()
    app.run_polling()
