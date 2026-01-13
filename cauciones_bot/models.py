from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from cauciones_bot.config import Config


@dataclass
class DatosCaucion:
    dias: int
    tasa: float
    raw_tasa: str = ""

    def __post_init__(self) -> None:
        if self.dias < 0:
            raise ValueError("Los días no pueden ser negativos")
        if self.tasa < 0:
            raise ValueError("La tasa no puede ser negativa")


@dataclass
class PuntoHistorial:
    hora: datetime
    tasas_por_plazo: Dict[int, float] = field(default_factory=dict)


@dataclass
class ConfiguracionUsuario:
    tna_objetivo: float = Config.DEFAULT_TNA_OBJETIVO
    intervalo_minutos: int = Config.DEFAULT_INTERVALO_MINUTOS
    dias_grafico_custom: int = Config.DEFAULT_DIAS_GRAFICO

    def validar(self) -> bool:
        return (
            self.tna_objetivo >= 0
            and self.intervalo_minutos >= 1
            and self.dias_grafico_custom >= 1
        )


@dataclass
class ResultadoAnalisis:
    oportunidades: List[DatosCaucion]
    top_3: List[DatosCaucion]
    hay_alerta_critica: bool
    tasa_maxima: Optional[float] = None
