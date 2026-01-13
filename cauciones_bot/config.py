import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ ERROR: No se encontró el token en el archivo .env")

    IOL_URL: str = "https://iol.invertironline.com/mercado/cotizaciones/argentina/cauciones"
    CACHE_TTL_SECONDS: int = 60
    MAX_HISTORY_POINTS: int = 288
    HISTORY_MIN_INTERVAL_SECONDS: int = 300
    DEFAULT_TNA_OBJETIVO: float = 25.0
    DEFAULT_INTERVALO_MINUTOS: int = 5
    DEFAULT_DIAS_GRAFICO: int = 1
    MAX_DIAS_TOP3: int = 60
    MAX_DIAS_OPORTUNIDADES: int = 30
    MIN_DIAS_OPORTUNIDADES: int = 1
    PERSISTENCE_FILE: str = "bot_datos_usuarios_v2.pickle"
