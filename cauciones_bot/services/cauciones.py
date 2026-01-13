from typing import List

from cauciones_bot.models import DatosCaucion, PuntoHistorial, ResultadoAnalisis
from cauciones_bot.services.analytics import AnalizadorMercado
from cauciones_bot.services.cache import CacheService
from cauciones_bot.services.history import HistorialService
from cauciones_bot.services.logger import TelegramLogger
from cauciones_bot.services.scraper import ScraperIOLWeb


class ServicioCauciones:
    def __init__(
        self,
        scraper: ScraperIOLWeb,
        cache: CacheService,
        historial: HistorialService,
        analizador: AnalizadorMercado,
        logger: TelegramLogger,
    ) -> None:
        self._scraper = scraper
        self._cache = cache
        self._historial = historial
        self._analizador = analizador
        self._logger = logger

    def obtener_datos_mercado(self) -> List[DatosCaucion]:
        datos_cache = self._cache.get()
        if datos_cache:
            return datos_cache

        datos = self._scraper.obtener_datos()
        if datos:
            self._cache.set(datos)
            self._historial.agregar_punto(datos)
        return datos

    def analizar_mercado(self, tasa_objetivo: float) -> ResultadoAnalisis:
        datos = self.obtener_datos_mercado()
        return self._analizador.analizar(datos, tasa_objetivo)

    def obtener_historial(self) -> List[PuntoHistorial]:
        return self._historial.obtener_historial()

    def tiene_datos_para_grafico(self) -> bool:
        return self._historial.tiene_datos_suficientes()
