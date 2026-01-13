from typing import List

from cauciones_bot.config import Config
from cauciones_bot.models import DatosCaucion, ResultadoAnalisis


class AnalizadorMercado:
    @staticmethod
    def analizar(datos: List[DatosCaucion], tasa_objetivo: float) -> ResultadoAnalisis:
        if not datos:
            return ResultadoAnalisis([], [], False)

        datos_top = [dato for dato in datos if dato.dias <= Config.MAX_DIAS_TOP3]
        top_3 = sorted(datos_top, key=lambda item: item.tasa, reverse=True)[:3]

        oportunidades = sorted(
            [
                dato
                for dato in datos
                if dato.tasa >= tasa_objetivo
                and Config.MIN_DIAS_OPORTUNIDADES <= dato.dias <= Config.MAX_DIAS_OPORTUNIDADES
            ],
            key=lambda item: item.dias,
        )

        hay_alerta = any(dato.tasa >= 100 for dato in datos)
        tasa_max = max(dato.tasa for dato in datos)

        return ResultadoAnalisis(oportunidades, top_3, hay_alerta, tasa_max)
