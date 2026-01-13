import logging

from telegram import Update
from telegram.ext import Application, ContextTypes

from cauciones_bot.models import ConfiguracionUsuario
from cauciones_bot.services.cauciones import ServicioCauciones
from cauciones_bot.services.charts import GeneradorGraficos
from cauciones_bot.services.formatter import FormateadorMensajes


class BotHandlers:
    def __init__(self, servicio: ServicioCauciones, formateador: FormateadorMensajes) -> None:
        self._servicio = servicio
        self._formateador = formateador

    async def recoleccion_global(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            datos = self._servicio.obtener_datos_mercado()
            if datos:
                logging.info("🔄 Global: %s registros.", len(datos))
            else:
                logging.info("💤 Global: Sin datos.")
        except Exception as exc:
            logging.error("❌ Error global: %s", exc)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if "config" not in context.user_data:
            context.user_data["config"] = ConfiguracionUsuario()
        config = context.user_data["config"]

        await update.message.reply_text(
            (
                f"👋 ¡Hola {update.effective_user.first_name}!\n\n"
                "📊 *Configuración Actual:*\n"
                f"• Alerta Tasa: *{config.tna_objetivo}%*\n"
                f"• Intervalo Alerta: *{config.intervalo_minutos} min*\n"
                f"• Gráfico Custom: *{config.dias_grafico_custom} días*\n\n"
                "🛠 *Comandos Nuevos:*\n"
                "/tendencia → Ver las 3 líneas (Corto/Medio/Largo)\n"
                "/set_tendencia 7 → Configurar gráfico de 7 días\n"
                "/mitendencia → Ver TU gráfico personalizado\n"
                "/set 30 → Configurar alerta de tasa\n"
                "/stop → Detener alertas"
            ),
            parse_mode="Markdown",
        )
        self._actualizar_job_usuario(chat_id, context)

    async def cmd_set_tendencia(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            dias = int(context.args[0])
            if dias < 1:
                raise ValueError
            config = context.user_data.get("config", ConfiguracionUsuario())
            config.dias_grafico_custom = dias
            context.user_data["config"] = config
            await update.message.reply_text(
                f"✅ Gráfico personalizado: *{dias} Días*.", parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text("❌ Uso: `/set_tendencia 7`")

    async def cmd_tendencia_general(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not self._servicio.tiene_datos_para_grafico():
            await update.message.reply_text("📉 Recolectando datos...")
            return
        await update.message.reply_text("🎨 Generando gráfico general...")
        historial = self._servicio.obtener_historial()
        img = GeneradorGraficos.generar_tendencia_general(historial)
        if img:
            await update.message.reply_photo(
                photo=img, caption="📊 *Tendencia Mercado*", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Error generando gráfico.")

    async def cmd_tendencia_custom(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not self._servicio.tiene_datos_para_grafico():
            await update.message.reply_text("📉 Recolectando datos...")
            return
        config = context.user_data.get("config", ConfiguracionUsuario())
        dias = config.dias_grafico_custom
        await update.message.reply_text(
            f"🎨 Generando gráfico de *{dias} días*...", parse_mode="Markdown"
        )
        historial = self._servicio.obtener_historial()
        img = GeneradorGraficos.generar_tendencia_custom(historial, dias)
        if img:
            await update.message.reply_photo(
                photo=img,
                caption=f"📊 *Tu Tendencia ({dias}d)*",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"⚠️ Sin datos recientes para {dias} días."
            )

    async def cmd_set_tna(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            val = float(context.args[0])
            config = context.user_data.get("config", ConfiguracionUsuario())
            config.tna_objetivo = val
            context.user_data["config"] = config
            self._actualizar_job_usuario(update.effective_chat.id, context)
            await update.message.reply_text(
                f"✅ Alerta TNA > {val}%", parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text("❌ Uso: `/set 30`")

    async def cmd_set_tiempo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            val = int(context.args[0])
            if val < 1:
                raise ValueError
            config = context.user_data.get("config", ConfiguracionUsuario())
            config.intervalo_minutos = val
            context.user_data["config"] = config
            self._actualizar_job_usuario(update.effective_chat.id, context)
            await update.message.reply_text(
                f"⏱️ Intervalo: {val} min", parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text("❌ Uso: `/tiempo 10`")

    async def cmd_ahora(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        config = context.user_data.get("config", ConfiguracionUsuario())
        res = self._servicio.analizar_mercado(config.tna_objetivo)
        if not res.top_3:
            await update.message.reply_text("📉 Sin datos ahora.")
            return
        await update.message.reply_text(
            self._formateador.formatear_reporte_manual(res, config.tna_objetivo),
            parse_mode="Markdown",
        )

    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        for job in context.job_queue.get_jobs_by_name(str(chat_id)):
            job.schedule_removal()
        await update.message.reply_text("🛑 Detenido.")

    async def tarea_escaneo(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        job = context.job
        config = job.data
        res = self._servicio.analizar_mercado(config.tna_objetivo)
        if not res.top_3:
            return
        if res.oportunidades or res.hay_alerta_critica:
            try:
                msg = self._formateador.formatear_reporte_completo(
                    res, config.tna_objetivo
                )
                await context.bot.send_message(job.chat_id, msg, parse_mode="Markdown")
            except Exception as exc:
                if "Forbidden" in str(exc):
                    job.schedule_removal()

    def _actualizar_job_usuario(
        self, chat_id: int, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        for job in context.job_queue.get_jobs_by_name(str(chat_id)):
            job.schedule_removal()
        config = context.user_data.get("config", ConfiguracionUsuario())
        context.job_queue.run_repeating(
            self.tarea_escaneo,
            interval=config.intervalo_minutos * 60,
            first=5,
            chat_id=chat_id,
            name=str(chat_id),
            data=config,
        )

    async def restaurar_tareas(self, application: Application) -> None:
        if not application.user_data:
            return
        count = 0
        for chat_id, data in application.user_data.items():
            if "config" in data:
                config = data["config"]
                application.job_queue.run_repeating(
                    self.tarea_escaneo,
                    interval=config.intervalo_minutos * 60,
                    first=10 + (count * 2),
                    chat_id=chat_id,
                    name=str(chat_id),
                    data=config,
                )
                count += 1
        logging.info("🔄 Tareas restauradas para %s usuarios.", count)
