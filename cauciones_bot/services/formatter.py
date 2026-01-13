from cauciones_bot.models import ResultadoAnalisis


class FormateadorMensajes:
    @staticmethod
    def formatear_reporte_completo(analisis: ResultadoAnalisis, tasa_objetivo: float) -> str:
        mensajes = []
        if analisis.hay_alerta_critica:
            mensajes.append(f"🚨🚨 *SUPER ALERTA: {analisis.tasa_maxima}% TNA* 🚨🚨")

        msg_top = "*🏆 Top 3 Mercado (hasta 60 días):*\n\n"
        for item in analisis.top_3:
            msg_top += f"✅ *{item.tasa}%* a {item.dias} DÍAS\n"
        mensajes.append(msg_top)

        if analisis.oportunidades:
            msg_ops = f"\n🔔 *Tus Oportunidades (> {tasa_objetivo}%):*\n\n"
            for item in analisis.oportunidades[:5]:
                msg_ops += f"✅ *{item.dias} DÍAS* | Tasa: {item.tasa}%\n"
            mensajes.append(msg_ops)

        return "\n".join(mensajes)

    @staticmethod
    def formatear_reporte_manual(analisis: ResultadoAnalisis, tasa_objetivo: float) -> str:
        msg = (
            f"🔎 *REPORTE MANUAL* (Obj: {tasa_objetivo}%)\n\n"
            "*🏆 Top 3 Global:*\n\n"
        )
        for item in analisis.top_3:
            msg += f"• {item.tasa}% ({item.dias} DÍAS)\n"

        msg += "\n*✅ Oportunidades:*\n\n"

        if analisis.oportunidades:
            for item in analisis.oportunidades[:5]:
                msg += f"• {item.tasa}% ({item.dias} DÍAS)\n"
        else:
            msg += "Nada supera tu objetivo hoy."

        return msg
