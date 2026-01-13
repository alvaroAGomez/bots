from io import StringIO
from typing import List

import pandas as pd
import requests

from cauciones_bot.models import DatosCaucion
from cauciones_bot.services.logger import TelegramLogger


class ScraperIOLWeb:
    def __init__(self, url: str, logger: TelegramLogger) -> None:
        self._url = url
        self._logger = logger

    def obtener_datos(self) -> List[DatosCaucion]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            response = requests.get(self._url, headers=headers, timeout=10)
            response.raise_for_status()
            html_data = StringIO(response.text)
            tablas = pd.read_html(html_data)
            if not tablas:
                return []

            df = tablas[0]
            df.columns = df.columns.str.lower()
            return self._parsear_dataframe(df)
        except Exception as exc:
            self._logger.error(f"Error scraping IOL: {exc}")
            return []

    def _parsear_dataframe(self, df: pd.DataFrame) -> List[DatosCaucion]:
        col_tasa, col_plazo = "tasa tomadora", "plazo"
        if col_tasa not in df.columns or col_plazo not in df.columns:
            return []

        resultados: List[DatosCaucion] = []
        for _, row in df.iterrows():
            try:
                raw_tasa = str(row[col_tasa])
                tasa = float(
                    raw_tasa.replace("%", "").replace(".", "").replace(",", ".").strip()
                )
                raw_plazo = (
                    str(row[col_plazo])
                    .lower()
                    .replace("días", "")
                    .replace("dias", "")
                    .replace("d", "")
                    .strip()
                )
                dias = int(float(raw_plazo))
                resultados.append(DatosCaucion(dias=dias, tasa=tasa, raw_tasa=raw_tasa))
            except Exception:
                continue
        return resultados
