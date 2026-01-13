from datetime import datetime
from typing import List, Optional

import pytz

from cauciones_bot.config import Config
from cauciones_bot.models import DatosCaucion, PuntoHistorial


class HistorialService:
    def __init__(self, max_points: int = Config.MAX_HISTORY_POINTS) -> None:
        self._historial: List[PuntoHistorial] = []
        self._max_points = max_points

    def agregar_punto(
        self, datos: List[DatosCaucion], timestamp: Optional[datetime] = None
    ) -> None:
        tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")
        ahora = timestamp or datetime.now(tz_ar)

        if self._historial:
            ultimo = self._historial[-1]
            if (ahora - ultimo.hora).total_seconds() < Config.HISTORY_MIN_INTERVAL_SECONDS:
                return

        mapa_tasas = {}
        for dato in datos:
            if dato.dias not in mapa_tasas or dato.tasa > mapa_tasas[dato.dias]:
                mapa_tasas[dato.dias] = dato.tasa

        if not mapa_tasas:
            return

        punto = PuntoHistorial(hora=ahora, tasas_por_plazo=mapa_tasas)
        self._historial.append(punto)

        if len(self._historial) > self._max_points:
            self._historial.pop(0)

    def obtener_historial(self) -> List[PuntoHistorial]:
        return self._historial.copy()

    def tiene_datos_suficientes(self, minimo: int = 2) -> bool:
        return len(self._historial) >= minimo
