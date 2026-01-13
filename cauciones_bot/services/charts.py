import logging
from io import BytesIO
from typing import List, Optional

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pytz

from cauciones_bot.models import PuntoHistorial

matplotlib.use("Agg")


class GeneradorGraficos:
    @staticmethod
    def _configurar_ejes(ax, titulo: str) -> None:
        tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")

        ax.set_title(titulo)
        ax.set_xlabel("Hora (Argentina)")
        ax.set_ylabel("Tasa TNA (%)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=tz_ar))

    @staticmethod
    def generar_tendencia_general(historial: List[PuntoHistorial]) -> Optional[BytesIO]:
        if not historial or len(historial) < 2:
            return None
        try:
            x = [punto.hora for punto in historial]
            y_corto, y_medio, y_largo = [], [], []

            for punto in historial:
                tasas = punto.tasas_por_plazo
                tc = [t for d, t in tasas.items() if 1 <= d <= 7]
                y_corto.append(max(tc) if tc else None)
                tm = [t for d, t in tasas.items() if 8 <= d <= 30]
                y_medio.append(max(tm) if tm else None)
                tl = [t for d, t in tasas.items() if d > 30]
                y_largo.append(max(tl) if tl else None)

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(
                x,
                y_corto,
                marker="o",
                markersize=4,
                linestyle="-",
                color="#2ca02c",
                label="Corto (1-7d)",
            )
            ax.plot(
                x,
                y_medio,
                marker="s",
                markersize=4,
                linestyle="--",
                color="#1f77b4",
                label="Medio (8-30d)",
            )
            ax.plot(
                x,
                y_largo,
                marker="^",
                markersize=4,
                linestyle=":",
                color="#ff7f0e",
                label="Largo (>30d)",
            )

            GeneradorGraficos._configurar_ejes(ax, "Tendencia de Mercado (3 Plazos)")
            fig.autofmt_xdate()
            ax.legend(loc="best")

            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as exc:
            logging.error("Error gráfico general: %s", exc)
            return None

    @staticmethod
    def generar_tendencia_custom(
        historial: List[PuntoHistorial], dias_objetivo: int
    ) -> Optional[BytesIO]:
        if not historial or len(historial) < 2:
            return None
        try:
            x, y = [], []
            for punto in historial:
                x.append(punto.hora)
                val = punto.tasas_por_plazo.get(dias_objetivo, None)
                y.append(val)

            if all(v is None for v in y):
                return None

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(
                x,
                y,
                marker="*",
                markersize=6,
                linestyle="-",
                color="#9467bd",
                label=f"Plazo {dias_objetivo}d",
            )

            GeneradorGraficos._configurar_ejes(
                ax, f"Tendencia Personalizada: {dias_objetivo} Días"
            )
            fig.autofmt_xdate()
            ax.legend()

            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            plt.close(fig)
            return buf
        except Exception as exc:
            logging.error("Error gráfico custom: %s", exc)
            return None
