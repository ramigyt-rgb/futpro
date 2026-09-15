from __future__ import annotations

import os
import json
import math
import time
import uuid
import sqlite3
import random
import hashlib
import traceback
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, Iterable
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    import ccxt
except Exception:
    ccxt = None

# ============================================================
# CONFIG
# ============================================================
APP_NAME = "FUTURES COMMAND CENTER PRO"
APP_VERSION = "1.2.1"
BUILD = "2026.09.15"
DB_PATH = os.getenv("FUTURES_CC_DB", "futures_command_center.db")
DEFAULT_TZ = os.getenv("APP_TIMEZONE", "America/Argentina/Salta")
DEFAULT_EXCHANGE = os.getenv("DEFAULT_EXCHANGE", "binanceusdm")
DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "BTC/USDT:USDT")
SUPPORTED_EXCHANGES = {
    "binanceusdm": "Binance USD-M Futures",
    "bybit": "Bybit Perpetuals",
    "okx": "OKX Perpetuals",
}
TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "1w"]
DEFAULT_MTF = ["5m", "15m", "1h", "4h", "1d"]
ORDER_STATES = ["DRAFT", "VALIDATED", "READY", "SUBMITTED", "PARTIALLY_FILLED", "FILLED", "PROTECTED", "CLOSING", "CLOSED", "CANCELLED", "REJECTED", "ERROR"]
SEVERITIES = ["INFO", "WATCH", "WARNING", "DANGER", "CRITICAL"]

st.set_page_config(page_title=APP_NAME, page_icon="⚡", layout="wide", initial_sidebar_state="expanded")


# ============================================================
# INTERNATIONALIZATION (ES / EN)
# ============================================================
LANGUAGES = {"es": "🇦🇷 Español", "en": "🇺🇸 English"}
ES = {
    "Language": "Idioma", "OPERATING MODE": "MODO OPERATIVO", "Exchange": "Exchange", "Contract": "Contrato",
    "Primary timeframe": "Temporalidad principal", "Navigation": "Navegación", "Debug diagnostics": "Diagnóstico técnico",
    "ANALYSIS ONLY": "SOLO ANÁLISIS", "PAPER": "PAPER · SIMULACIÓN", "LIVE": "LIVE · REAL",
    "LIVE · REAL ORDERS": "LIVE · ÓRDENES REALES", "PAPER · SIMULATION": "PAPER · SIMULACIÓN",
    "Command Center": "Centro de Comando", "Market / Analysis": "Mercado / Análisis", "Scanner": "Scanner",
    "Trade Builder": "Constructor de Trade", "Positions / Execution": "Posiciones / Ejecución", "Risk Center": "Centro de Riesgo",
    "Journal / Analytics": "Journal / Analítica", "Backtest": "Backtest", "Playbook / Alerts": "Playbook / Alertas",
    "Data Quality / Health": "Calidad de Datos / Salud", "Configuration": "Configuración",
    "Market intelligence · Risk control · Execution discipline": "Inteligencia de mercado · Control de riesgo · Disciplina de ejecución",
    "CAPITAL PROTECTION → RISK → DECISION QUALITY → EXECUTION": "PROTECCIÓN DE CAPITAL → RIESGO → CALIDAD DE DECISIÓN → EJECUCIÓN",
    "## Command Center": "## Centro de Comando", "## Market / Analysis": "## Mercado / Análisis",
    "## Futures Scanner": "## Scanner de Futuros", "## Trade Builder / Execution Gate": "## Constructor de Trade / Gate de Ejecución",
    "## Positions / Execution": "## Posiciones / Ejecución", "## Risk Center / Portfolio Risk": "## Centro de Riesgo / Riesgo de Portfolio",
    "## Journal / Analytics": "## Journal / Analítica", "## Backtest / Walk-Forward": "## Backtest / Walk-Forward",
    "## Playbook / Alerts": "## Playbook / Alertas", "## Data Quality / System Health": "## Calidad de Datos / Salud del Sistema",
    "## Configuration / Setup / Deployment": "## Configuración / Setup / Despliegue",
    "Chart & Structure": "Gráfico y Estructura", "Multi-Timeframe": "Multi-Temporalidad", "Derivatives & Flow": "Derivados y Flujo",
    "Scenarios": "Escenarios", "Universe": "Universo", "Journal": "Journal", "Performance": "Rendimiento", "Reviews": "Revisiones",
    "Monte Carlo": "Monte Carlo", "Capital Flows": "Movimientos de Capital", "Playbook": "Playbook", "Alerts": "Alertas",
    "Overtrading / FOMO": "Sobreoperación / FOMO", "Risk Limits": "Límites de Riesgo", "Trading Safety": "Seguridad Operativa",
    "API & Secrets": "API y Secrets", "Deployment": "Despliegue", "Architecture": "Arquitectura",
    "PRICE": "PRECIO", "SESSION": "SESIÓN", "SPREAD": "SPREAD", "24H VOLUME": "VOLUMEN 24H", "RISK ENVIRONMENT": "ENTORNO DE RIESGO",
    "DATA HEALTH": "SALUD DE DATOS", "MARKET REGIME": "RÉGIMEN DE MERCADO", "VOLATILITY": "VOLATILIDAD", "VOLUME": "VOLUMEN",
    "FUNDING": "FUNDING", "OPEN INTEREST": "OPEN INTEREST", "DATA CONFIDENCE": "CONFIANZA DE DATOS",
    "LONG SCORE": "SCORE LONG", "SHORT SCORE": "SCORE SHORT", "DECISION MATRIX": "MATRIZ DE DECISIÓN",
    "WHY IT MATTERS": "POR QUÉ IMPORTA", "Evidence": "Evidencia", "Contradictions / risks": "Contradicciones / riesgos",
    "STRUCTURE": "ESTRUCTURA", "CHOCH": "CHOCH", "COMPRESSION": "COMPRESIÓN", "EXPANSION": "EXPANSIÓN",
    "#### Support / Resistance": "#### Soportes / Resistencias", "#### Liquidity map": "#### Mapa de liquidez", "#### Indicator state": "#### Estado de indicadores",
    "Timeframes": "Temporalidades", "Run multi-timeframe engine": "Ejecutar motor multi-temporal", "Load recent trade flow": "Cargar flujo reciente",
    "#### Optional external context": "#### Contexto externo opcional", "Contracts to scan": "Contratos a escanear", "Scanner timeframe": "Temporalidad del scanner",
    "Min 24h quote volume": "Volumen cotizado mínimo 24h", "Run scanner": "Ejecutar scanner", "Direction filter": "Filtro de dirección",
    "Direction": "Dirección", "Order type": "Tipo de orden", "Entry": "Entrada", "Leverage": "Apalancamiento", "Stop loss": "Stop Loss",
    "Capital / equity (USDT)": "Capital / equity (USDT)", "Max risk %": "Riesgo máximo %", "Setup": "Setup",
    "Maker fee %": "Fee maker %", "Taker fee %": "Fee taker %", "Expected slippage % / side": "Slippage esperado % / lado",
    "Expected funding cost %": "Costo esperado de funding %", "Trade thesis / notes": "Tesis del trade / notas",
    "Calculate & validate": "Calcular y validar", "#### Take-profit ladder": "#### Escalera de Take Profit", "#### Stop alternatives": "#### Alternativas de Stop",
    "#### Psychology check": "#### Check psicológico", "Revenge urge": "Impulso de revancha", "Fatigue": "Fatiga", "Impulsivity": "Impulsividad",
    "Submit PAPER trade": "Enviar trade PAPER", "Double confirmation required": "Se requiere doble confirmación",
    "Generate one-time execution code": "Generar código único de ejecución", "Enter one-time code": "Ingresar código único",
    "EXECUTE LIVE ORDER": "EJECUTAR ORDEN LIVE", "Refresh & process PAPER positions": "Actualizar y procesar posiciones PAPER",
    "Load private account positions": "Cargar posiciones privadas de la cuenta", "Activate kill switch": "Activar Kill Switch",
    "Deactivate kill switch": "Desactivar Kill Switch", "Type CANCEL PENDING ORDERS": "Escribí CANCEL PENDING ORDERS",
    "Cancel all pending LIVE orders": "Cancelar todas las órdenes LIVE pendientes", "Reference account equity (USDT)": "Equity de referencia (USDT)",
    "Fetch LIVE portfolio risk": "Cargar riesgo LIVE del portfolio", "Portfolio net directional notional for stress test": "Nocional direccional neto para stress test",
    "#### Add / review trade": "#### Agregar / revisar trade", "Symbol": "Símbolo", "Side": "Lado", "Stop": "Stop", "PnL gross": "PnL bruto",
    "Fees": "Fees", "Funding": "Funding", "MFE price units": "MFE en unidades de precio", "MAE price units": "MAE en unidades de precio",
    "Planned risk USDT": "Riesgo planificado USDT", "Reason / plan": "Razón / plan", "Lesson": "Aprendizaje", "Mistake / rule broken": "Error / regla incumplida",
    "Notes": "Notas", "Respected plan": "Respetó el plan", "Did NOT widen stop": "NO amplió el stop", "Did NOT chase": "NO persiguió precio",
    "Risk stayed within limit": "Riesgo dentro del límite", "Save journal trade": "Guardar trade en journal", "Simulations": "Simulaciones",
    "Trades per simulation": "Trades por simulación", "Risk % per future trade": "Riesgo % por trade futuro", "Type": "Tipo", "Amount": "Monto",
    "Add capital flow": "Agregar movimiento de capital", "Timeframe": "Temporalidad", "Strategy": "Estrategia", "Bars": "Velas", "Risk %": "Riesgo %",
    "Stop ATR": "Stop ATR", "Target R": "Objetivo R", "Fee % / side": "Fee % / lado", "Slippage % / side": "Slippage % / lado",
    "Run backtest": "Ejecutar backtest", "Setup name": "Nombre del setup", "Minimum R:R": "R:R mínimo", "Allowed volatility": "Volatilidad permitida",
    "Session": "Sesión", "Conditions": "Condiciones", "Invalidation": "Invalidación", "Checklist": "Checklist", "Save setup": "Guardar setup",
    "Alert": "Alerta", "Operator": "Operador", "Threshold": "Umbral", "Severity": "Severidad", "Note": "Nota", "Add alert": "Agregar alerta",
    "Run internal calculation tests": "Ejecutar tests internos de cálculo", "SELF-CHECKS": "AUTO-CHEQUEOS", "AUDIT LOG": "LOG DE AUDITORÍA",
    "ACTIVE ALERT EVALUATION": "EVALUACIÓN DE ALERTAS ACTIVAS", "APP VERSION": "VERSIÓN APP", "MODE": "MODO", "EXCHANGE": "EXCHANGE", "LAST REFRESH": "ÚLTIMA ACTUALIZACIÓN",
    "Max Risk / Trade %": "Riesgo máx. / trade %", "Max Daily Loss %": "Pérdida diaria máx. %", "Max Weekly Loss %": "Pérdida semanal máx. %",
    "Max Monthly Loss %": "Pérdida mensual máx. %", "Max Open Risk %": "Riesgo abierto máx. %", "Max Portfolio Exposure %": "Exposición máx. portfolio %",
    "Max Margin Usage %": "Uso máx. de margen %", "Max Leverage": "Apalancamiento máximo", "Max Drawdown %": "Drawdown máximo %",
    "Max Concurrent Trades": "Trades simultáneos máx.", "Max Correlated Trades": "Trades correlacionados máx.", "Save risk policy": "Guardar política de riesgo",
    "### Safety hierarchy": "### Jerarquía de seguridad", "### Local": "### Local", "### Streamlit Cloud": "### Streamlit Cloud",
    "### Internal one-file architecture": "### Arquitectura interna de un solo archivo",
    "price change": "cambio de precio", "exchange ticker / candles": "ticker / velas del exchange", "UTC session windows": "ventanas de sesión UTC",
    "market context": "contexto de mercado", "quote volume if reported": "volumen cotizado si está disponible", "BTC/ETH + volatility context": "contexto BTC/ETH + volatilidad",
    "No current BOS": "Sin BOS actual", "noise-filtered swing model": "modelo de swings filtrado de ruido", "rolling range percentile": "percentil móvil del rango",
    "No levels detected.": "No se detectaron niveles.", "No clustered liquidity inference available.": "No hay inferencias de liquidez agrupada disponibles.",
    "Run the engine to avoid unnecessary API calls.": "Ejecutá el motor para evitar llamadas innecesarias a la API.",
    "No open paper positions.": "No hay posiciones PAPER abiertas.", "No open positions returned by the exchange.": "El exchange no devolvió posiciones abiertas.",
    "No trades yet.": "Todavía no hay trades.", "No completed trades yet.": "Todavía no hay trades completados.", "No review data.": "No hay datos para revisar.",
    "No trade history to inspect.": "No hay historial de trades para analizar.", "Audit log is empty.": "El log de auditoría está vacío.",
    "Trade saved.": "Trade guardado.", "Setup saved.": "Setup guardado.", "Cancel request completed.": "Solicitud de cancelación completada.",
    "Risk policy saved locally.": "Política de riesgo guardada localmente.", "All internal calculation self-checks passed.": "Todos los auto-chequeos internos de cálculo pasaron correctamente.",
    "ANALYSIS ONLY: order execution is disabled by design.": "SOLO ANÁLISIS: la ejecución de órdenes está deshabilitada por diseño.",
    "LIVE MODE — REAL MONEY / REAL ORDERS": "MODO LIVE — DINERO REAL / ÓRDENES REALES",
    "Market data is unavailable. The terminal remains operational in degraded mode.": "Los datos de mercado no están disponibles. La terminal continúa operativa en modo degradado.",
    "Technical diagnostics": "Diagnóstico técnico", "Loading live public market data…": "Cargando datos públicos de mercado…",
    "Scanning liquid perpetual contracts with rate-limit-aware sequential requests…": "Escaneando contratos líquidos con solicitudes secuenciales controladas…",
    "Analyzing selected timeframes…": "Analizando temporalidades seleccionadas…", "Loading historical candles and simulating conservatively…": "Cargando velas históricas y simulando de forma conservadora…",
    "Submitting protected LIVE order…": "Enviando orden LIVE protegida…",
    "Manual": "Manual", "Trend Pullback": "Pullback en Tendencia", "Breakout Retest": "Retesteo de Breakout", "Range Reversal": "Reversión de Rango",
    "Liquidity Sweep": "Barrido de Liquidez", "Momentum Continuation": "Continuación de Momentum", "MARKET": "MARKET", "LIMIT": "LIMIT",
    "BOTH": "AMBOS", "ANY": "CUALQUIERA", "ASIA": "ASIA", "LONDON": "LONDRES", "NEW YORK": "NUEVA YORK", "OVERLAPS": "SOLAPAMIENTOS",
    "NO TRADE": "NO OPERAR", "WAIT": "ESPERAR", "LONG BIAS": "SESGO LONG", "SHORT BIAS": "SESGO SHORT",
    "YES": "SÍ", "NO": "NO", "NONE": "NINGUNO", "UNAVAILABLE": "NO DISPONIBLE", "CONNECTED": "CONECTADO", "STALE": "DESACTUALIZADO",
    "ERROR": "ERROR", "WARNING": "ADVERTENCIA", "INFO": "INFO", "CRITICAL": "CRÍTICO", "DANGER": "PELIGRO",
    "Signal strength": "Fuerza de señal", "Data confidence": "Confianza de datos", "No-trade score": "Score no-trade",
    "Capital protection → Risk → Decision quality → Execution → Results": "Protección de capital → Riesgo → Calidad de decisión → Ejecución → Resultados",
}

# Extended interface copy. Technical market enums stay in their canonical form when that is safer.
ES.update({
    "### requirements.txt": "### requirements.txt", "### GitHub": "### GitHub",
    "**Evidence**": "**Evidencia**", "**Contradictions / risks**": "**Contradicciones / riesgos**", "**Double confirmation required**": "**Se requiere doble confirmación**",
    "DATA ROUTER · Price/candles/order book: official Binance Vision public market data (Spot proxy) · Funding/OI: real Binance Futures only when reachable · No synthetic financial values.": "DATA ROUTER · Precio/velas/order book: datos públicos oficiales de Binance Vision (proxy Spot) · Funding/OI: Binance Futures real sólo cuando es accesible · Sin valores financieros inventados.",
    "Source: Binance Vision public Spot market data for technical analysis/order book. Futures-only derivatives remain real-only and may show UNAVAILABLE if Binance Futures rejects the Streamlit host region.": "Fuente: datos públicos Spot de Binance Vision para análisis técnico/order book. Los derivados exclusivos de Futures se muestran sólo con datos reales y pueden figurar NO DISPONIBLE si Binance Futures rechaza la región del servidor de Streamlit.",
    "Selected symbol data unavailable. Change exchange/symbol or retry.": "No hay datos disponibles para el símbolo seleccionado. Cambiá exchange/símbolo o reintentá.",
    "Levels are observed; the interpretation as stop/liquidity clusters is explicitly inferential.": "Los niveles son observados; su interpretación como clusters de stops/liquidez es explícitamente inferencial.",
    "Aggressive buy/sell interpretation is only shown when the exchange's recent-trade feed includes a usable side. No synthetic CVD is presented as real order flow.": "La interpretación de compras/ventas agresivas sólo aparece cuando el feed de trades recientes incluye un lado utilizable. No se presenta CVD sintético como order flow real.",
    "Scenario scores are relative rule-based scores, not calibrated probabilities unless separately validated on historical out-of-sample data.": "Los scores de escenario son relativos y basados en reglas; no son probabilidades calibradas salvo validación separada con datos históricos out-of-sample.",
    "BTC dominance / TOTAL / TOTAL2 / TOTAL3 and economic calendar remain disabled unless a real external data source is explicitly integrated. The app does not invent these values.": "BTC dominance / TOTAL / TOTAL2 / TOTAL3 y el calendario económico permanecen deshabilitados hasta integrar una fuente externa real. La app no inventa esos valores.",
    "Run the scanner. It intentionally does not refetch on every widget change.": "Ejecutá el scanner. Intencionalmente no vuelve a consultar la API ante cada cambio de control.",
    "Opportunity components are visible. This scanner ranks conditions; it does not assert that top-ranked trades will be profitable.": "Los componentes de oportunidad son visibles. El scanner ordena condiciones; no afirma que los trades mejor rankeados vayan a ser rentables.",
    "Liquidation is an indicative isolated-linear estimate only. For existing LIVE positions, exchange-reported liquidation price takes precedence.": "La liquidación es sólo una estimación indicativa lineal/aislada. En posiciones LIVE existentes prevalece el precio de liquidación informado por el exchange.",
    "Behavioral gate: strong impulsive-risk signal. Consider NO TRADE until the checklist normalizes.": "Gate conductual: señal fuerte de riesgo impulsivo. Considerá NO OPERAR hasta que el checklist se normalice.",
    "Behavioral warning: elevated FOMO/revenge/fatigue/impulsivity.": "Advertencia conductual: FOMO/revancha/fatiga/impulsividad elevados.",
    "Behavioral checklist: no high-intensity signal recorded.": "Checklist conductual: no se registraron señales de alta intensidad.",
    "Paper order blocked by critical validation errors. Fix the plan first.": "Orden PAPER bloqueada por errores críticos de validación. Corregí primero el plan.",
    "Server-level ENABLE_LIVE_TRADING is OFF. Set it explicitly in Streamlit secrets/environment to permit live execution.": "ENABLE_LIVE_TRADING está OFF a nivel servidor. Debe habilitarse explícitamente en Secrets/Environment para permitir ejecución LIVE.",
    "LIVE order blocked by the trade gate.": "Orden LIVE bloqueada por el trade gate.",
    "I confirm this is a real leveraged futures order and I reviewed the stop, size, leverage and maximum planned loss.": "Confirmo que ésta es una orden real de futuros apalancados y revisé stop, tamaño, apalancamiento y pérdida máxima planificada.",
    "Duplicate-order protection: this exact preview was already submitted in this session.": "Protección contra órdenes duplicadas: este preview exacto ya fue enviado en esta sesión.",
    "Entry stop is attached, but one or more TP ladder actions need review.": "El stop de entrada quedó adjunto, pero una o más acciones de la escalera de TP requieren revisión.",
    "Paper engine uses conservative same-candle ordering: if SL and TP are both touched, SL is processed first.": "El motor PAPER usa una regla conservadora dentro de la misma vela: si SL y TP son tocados, procesa primero el SL.",
    "Private data is loaded only on request; public analysis does not require API credentials.": "Los datos privados se cargan sólo bajo pedido; el análisis público no requiere credenciales API.",
    "For LIVE positions, exchange-reported liquidation price is shown when available and supersedes local estimates.": "En posiciones LIVE, se muestra el precio de liquidación informado por el exchange cuando está disponible y reemplaza las estimaciones locales.",
    "KILL SWITCH ACTIVE — NEW ORDERS BLOCKED": "KILL SWITCH ACTIVO — NUEVAS ÓRDENES BLOQUEADAS",
    "Optional destructive action: cancel pending orders only. Closing positions is intentionally not automatic.": "Acción destructiva opcional: sólo cancelar órdenes pendientes. El cierre de posiciones no es automático intencionalmente.",
    "DAILY RISK LIMIT REACHED — new trades should remain blocked.": "LÍMITE DIARIO DE RIESGO ALCANZADO — los nuevos trades deben permanecer bloqueados.",
    "MAX DRAWDOWN LIMIT REACHED.": "LÍMITE MÁXIMO DE DRAWDOWN ALCANZADO.",
    "Portfolio-level live exposure appears here when private positions are loaded. PAPER positions remain visible in Positions.": "La exposición LIVE del portfolio aparece aquí al cargar posiciones privadas. Las posiciones PAPER siguen visibles en Posiciones.",
    "Stress test is linear and hypothetical; gaps, nonlinear liquidation mechanics, correlation breakdown and slippage can worsen outcomes.": "El stress test es lineal e hipotético; gaps, mecánicas no lineales de liquidación, ruptura de correlaciones y slippage pueden empeorar el resultado.",
    "Discipline is separate from economic outcome.": "La disciplina se evalúa por separado del resultado económico.",
    "Sample-size guard: strategy health remains INSUFFICIENT DATA below 10 trades. Positive PnL alone is not treated as proven edge.": "Control de tamaño de muestra: la salud de la estrategia permanece DATOS INSUFICIENTES con menos de 10 trades. Un PnL positivo por sí solo no se considera edge demostrado.",
    "At least 3 R-results are required; 20+ is preferable.": "Se requieren al menos 3 resultados en R; es preferible contar con 20 o más.",
    "Monte Carlo is a bootstrap of observed R outcomes, not a forecast; regime changes and non-stationarity can invalidate the distribution.": "Monte Carlo es un bootstrap de resultados R observados, no un pronóstico; cambios de régimen y no estacionariedad pueden invalidar la distribución.",
    "Backtest uses only available exchange OHLCV. Intrabar collisions are resolved conservatively in favor of the stop.": "El backtest usa sólo OHLCV disponible del exchange. Las colisiones intrabar se resuelven conservadoramente a favor del stop.",
    "No trades generated by this rule set in the selected sample.": "Este conjunto de reglas no generó trades en la muestra seleccionada.",
    "Parameters are not optimized separately on validation/OOS here; this deliberately reduces the temptation to overfit a small sample.": "Los parámetros no se optimizan por separado sobre validación/OOS; esto reduce deliberadamente el riesgo de sobreajustar una muestra pequeña.",
    "Alert rule saved. This single-file app evaluates rules when the relevant page/app reruns; it is not a background daemon.": "Regla de alerta guardada. Esta app de un solo archivo evalúa reglas cuando la página/app se vuelve a ejecutar; no es un proceso en segundo plano.",
    "No simple overtrading/risk-escalation flag detected from stored journal data.": "No se detectó una señal simple de sobreoperación/escalada de riesgo en el journal guardado.",
    "FOMO/late-entry checks are behavioral/rule-based alerts, not psychological diagnoses.": "Los checks de FOMO/entrada tardía son alertas conductuales basadas en reglas, no diagnósticos psicológicos.",
    "No saved alert rule is currently triggered for this symbol.": "Ninguna regla de alerta guardada está activada actualmente para este símbolo.",
    "No validation issues detected by the current rule set.": "El conjunto actual de reglas no detectó problemas de validación.",
    "One or more self-checks failed. Do not use LIVE mode until resolved.": "Falló uno o más auto-chequeos. No uses modo LIVE hasta resolverlo.",
    "The app uses retry with exponential backoff, API timeouts and Streamlit caches. A failing data source degrades its module instead of fabricating replacement market data.": "La app usa reintentos con backoff exponencial, timeouts de API y caché de Streamlit. Si falla una fuente de datos, el módulo se degrada en lugar de fabricar datos de reemplazo.",
    "LIVE is OFF by default and additionally requires the server secret `ENABLE_LIVE_TRADING=true`, configured credentials, an approved/conditional gate, an attached-stop capability, a typed phrase and a one-time code.": "LIVE está OFF por defecto y además requiere `ENABLE_LIVE_TRADING=true` en el servidor, credenciales configuradas, gate aprobado/condicional, capacidad de stop adjunto, frase escrita y código de un solo uso.",
    "Use exchange API keys with withdrawals disabled and only the minimum futures permissions required. IP restrictions are recommended where the exchange/account supports them.": "Usá API keys con retiros deshabilitados y sólo los permisos mínimos de Futures necesarios. Se recomiendan restricciones por IP cuando el exchange/cuenta las soporte.",
    "The emergency kill switch blocks new orders. Cancel-all requires a separate typed confirmation. It never closes positions automatically.": "El Kill Switch de emergencia bloquea nuevas órdenes. Cancelar todas requiere una confirmación escrita separada. Nunca cierra posiciones automáticamente.",
    "Secrets are read from environment variables first, then `st.secrets`. They are never rendered, logged or included in the audit payload.": "Los secrets se leen primero desde variables de entorno y luego desde `st.secrets`. Nunca se muestran, registran ni incluyen en el payload de auditoría.",
    "SQLite on Streamlit Community Cloud should be treated as ephemeral local persistence. For durable multi-device history, migrate the persistence functions to a durable external store while keeping the adapter inside this same `app.py` if the one-file constraint remains.": "SQLite en Streamlit Community Cloud debe tratarse como persistencia local efímera. Para historial durable entre dispositivos, migrá la persistencia a un almacenamiento externo manteniendo el adapter dentro de este mismo `app.py` si continúa la restricción de un solo archivo.",
    "All financial scores are rule-based and explainable. Data confidence is distinct from signal strength. Missing data remains missing instead of being invented.": "Todos los scores financieros son explicables y basados en reglas. La confianza de datos es distinta de la fuerza de señal. Los datos faltantes permanecen faltantes; no se inventan.",
    "Exchange blocked from this app server region. The app is online; the data endpoint is refusing the host.": "El exchange bloqueó la región del servidor de esta app. La app está online; el endpoint de datos está rechazando al host.",
    "📡 Public data: Binance Vision (Spot proxy). Funding/OI: Binance Futures only when reachable. LIVE stays fail-closed and revalidates on the real futures API.": "📡 Datos públicos: Binance Vision (proxy Spot). Funding/OI: Binance Futures sólo cuando sea accesible. LIVE permanece fail-closed y revalida contra la API Futures real.",
    "CCXT is not installed. Install requirements before using market data.": "CCXT no está instalado. Instalá los requirements antes de usar datos de mercado.",
    "FOMO": "FOMO",
    "No trades in period.": "No hubo trades en el período.",
    "Capital flow recorded. Deposits/withdrawals are kept separate from trading PnL.": "Movimiento de capital registrado. Depósitos y retiros se mantienen separados del PnL de trading.",
})

def tr(text: Any) -> Any:
    """Translate fixed UI copy without changing internal trading enums or calculations."""
    if not isinstance(text, str):
        return text
    return ES.get(text, text) if st.session_state.get("language", "es") == "es" else text

def tr_list(items: Iterable[str]) -> List[str]:
    return [tr(x) for x in items]

CSS = r"""
<style>
:root{--bg:#070a0f;--panel:#0d121b;--panel2:#111925;--line:#202a38;--text:#e7edf7;--muted:#8290a3;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;--blue:#38bdf8;--purple:#a78bfa;}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
.stApp{background:radial-gradient(circle at 15% 0%,#0e1724 0,#070a0f 32%,#05070b 100%);color:var(--text);}
/* Full-screen terminal */
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],#MainMenu,footer{display:none!important;}
header[data-testid="stHeader"]{height:0!important;min-height:0!important;}
.stApp>header{display:none!important;}
[data-testid="stAppViewContainer"]>.main{padding-top:0!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#080c12,#0a0f17);border-right:1px solid var(--line);}
.block-container{padding-top:.45rem;padding-bottom:4rem;max-width:1800px;}
.pro-card{background:linear-gradient(180deg,rgba(17,25,37,.97),rgba(10,15,23,.97));border:1px solid #1d2938;border-radius:16px;padding:14px 16px;box-shadow:0 10px 30px rgba(0,0,0,.18);margin-bottom:10px;}
.pro-card.tight{padding:10px 12px}
.pro-title{font-weight:800;letter-spacing:.06em;font-size:.78rem;color:#aebed2;text-transform:uppercase}
.pro-value{font-size:clamp(1.15rem,2vw,1.55rem);font-weight:850;margin-top:5px;color:#f4f7fb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.18}
.pro-sub{font-size:.77rem;color:#91a0b4;margin-top:5px;line-height:1.45;overflow-wrap:anywhere}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px}.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;border:1px solid #263244;background:#101722;font-size:.74rem;font-weight:800;margin:2px 4px 2px 0}.good{color:#73e6a0}.bad{color:#ff7d7d}.warn{color:#ffc45c}.info{color:#7dd3fc}.muted{color:#94a3b8}
.big-loss{border:1px solid rgba(239,68,68,.48);background:linear-gradient(135deg,rgba(127,29,29,.28),rgba(17,24,39,.95));border-radius:18px;padding:20px;text-align:center}.big-loss .n{font-size:2rem;font-weight:900;color:#ff7777}.mode-live{border:1px solid #ef4444!important;box-shadow:0 0 0 1px rgba(239,68,68,.25),0 0 24px rgba(239,68,68,.12)}.mode-paper{border:1px solid #f59e0b!important}.mode-analysis{border:1px solid #38bdf8!important}
.section-label{font-size:.72rem;color:#7f8da1;font-weight:900;letter-spacing:.11em;text-transform:uppercase;margin:16px 0 8px}.decision{font-size:1.4rem;font-weight:900;letter-spacing:.04em}.divider{height:1px;background:#1d2735;margin:8px 0 12px}.tiny{font-size:.72rem;color:#7f8da1}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.stButton>button{border-radius:10px;border:1px solid #263244;background:#111827;color:#e5eefb;font-weight:750}.stButton>button:hover{border-color:#38bdf8;color:white}.stTabs [data-baseweb="tab-list"]{gap:6px}.stTabs [data-baseweb="tab"]{background:#0d131d;border:1px solid #1c2735;border-radius:10px;padding:8px 12px}.stDataFrame{border:1px solid #1d2938;border-radius:12px;overflow:hidden}
@media(max-width:900px){.block-container{padding-left:.7rem;padding-right:.7rem}.pro-value{font-size:1.25rem}}

/* iPad/sidebar legibility */
[data-testid="stSidebar"] *{color:#dce6f3;}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span{color:#dce6f3!important;}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#111925!important;border-color:#2a3748!important;color:#f4f7fb!important;}
[data-testid="stSidebar"] [data-baseweb="select"] svg{fill:#dce6f3!important;}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:10px;padding:.34rem .45rem;margin:.08rem 0;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#111925;}
[data-testid="stSidebar"] hr{border-color:#1d2938!important;}
[data-testid="stSidebar"] .stAlert{background:#0d1826!important;}
@media (min-width:701px) and (max-width:1180px){
 .block-container{padding-left:.8rem!important;padding-right:.8rem!important;}
 [data-testid="stHorizontalBlock"]{gap:.65rem!important;}
 .pro-card{padding:12px 13px;}
 .pro-title{font-size:.70rem;}
 .pro-sub{font-size:.70rem;}
}
@media(max-width:700px){
 .block-container{padding-left:.65rem!important;padding-right:.65rem!important;}
 .pro-value{font-size:1.18rem;}
}

</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================
# DATA MODELS
# ============================================================
@dataclass
class ValidationIssue:
    severity: str
    code: str
    message: str

@dataclass
class RiskLimits:
    max_risk_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_weekly_loss_pct: float = 6.0
    max_monthly_loss_pct: float = 10.0
    max_open_risk_pct: float = 4.0
    max_portfolio_exposure_pct: float = 250.0
    max_margin_usage_pct: float = 45.0
    max_leverage: float = 10.0
    max_drawdown_pct: float = 15.0
    max_concurrent_trades: int = 5
    max_correlated_trades: int = 3
    min_rr: float = 1.5

@dataclass
class TradePlan:
    exchange: str
    symbol: str
    side: str
    order_type: str
    entry: float
    stop: float
    tps: List[float]
    tp_allocations: List[float]
    capital: float
    risk_pct: float
    leverage: float
    maker_fee_pct: float
    taker_fee_pct: float
    slippage_pct: float
    expected_funding_pct: float
    setup: str = "Manual"
    notes: str = ""

@dataclass
class TradeCalc:
    risk_budget: float
    stop_distance: float
    stop_distance_pct: float
    per_unit_worst_loss: float
    quantity: float  # base-asset quantity represented by the position
    order_amount: float  # exchange amount / contracts sent to CCXT
    contract_size: float
    notional: float
    margin: float
    effective_leverage: float
    planned_loss: float
    expected_fees: float
    expected_slippage: float
    expected_funding: float
    worst_planned_loss: float
    rr_weighted: float
    gross_tp_pnl: float
    net_tp_pnl: float
    breakeven_price: float
    liquidation_estimate: Optional[float]
    liquidation_distance_pct: Optional[float]
    min_required_leverage: float
    safe_leverage_high: float
    tp_rows: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class EngineResult:
    status: str
    score: float
    confidence: float
    factors: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

# ============================================================
# UTILITIES
# ============================================================
def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def iso_now() -> str:
    return utc_now().isoformat()

def safe_float(x: Any, default: float = np.nan) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default

def finite(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def pct_change(a: float, b: float) -> float:
    if not finite(a) or not finite(b) or b == 0:
        return np.nan
    return (a / b - 1.0) * 100.0

def fmt_num(x: Any, digits: int = 2) -> str:
    if not finite(x): return "—"
    x = float(x)
    if abs(x) >= 1_000_000_000: return f"{x/1e9:.{digits}f}B"
    if abs(x) >= 1_000_000: return f"{x/1e6:.{digits}f}M"
    if abs(x) >= 1_000: return f"{x/1e3:.{digits}f}K"
    return f"{x:,.{digits}f}"

def fmt_pct(x: Any, digits: int = 2) -> str:
    return "—" if not finite(x) else f"{float(x):.{digits}f}%"

def price_fmt(x: Any) -> str:
    if not finite(x): return "—"
    x = float(x)
    if x >= 1000: return f"{x:,.2f}"
    if x >= 1: return f"{x:,.4f}"
    return f"{x:,.8f}"

def hash_payload(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:20]

def to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)

def retry_call(fn, *args, retries: int = 3, base_delay: float = 0.45, **kwargs):
    last = None
    for i in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last = e
            if i < retries - 1:
                time.sleep(base_delay * (2 ** i) + random.random() * 0.15)
    raise last



def classify_exchange_error(err: Any) -> Dict[str, str]:
    """Convert low-level CCXT/network errors into safe, user-facing diagnostics."""
    text = str(err or "")
    low = text.lower()
    if "451" in low or "restricted location" in low or "eligibility" in low:
        return {
            "code": "HOST_REGION_RESTRICTED",
            "severity": "CRITICAL",
            "message": "The selected exchange rejected requests from the server hosting this app because of the server region.",
            "action": "This is not caused by your device or API key. Streamlit Community Cloud is hosted in the United States and its region is not configurable. Use an exchange/data source that serves that host region, run the app locally, or deploy the same app on infrastructure located in a jurisdiction supported by your exchange.",
        }
    if "429" in low or "rate limit" in low or "too many requests" in low:
        return {"code":"RATE_LIMITED","severity":"WARNING","message":"The exchange rate-limited the request.","action":"Wait briefly and retry. The app cache/backoff will reduce repeated requests."}
    if "timed out" in low or "timeout" in low:
        return {"code":"NETWORK_TIMEOUT","severity":"WARNING","message":"The market-data request timed out.","action":"Retry after checking connectivity or exchange status."}
    if "authentication" in low or "invalid api" in low or "api key" in low or "signature" in low:
        return {"code":"AUTH_ERROR","severity":"CRITICAL","message":"Private exchange authentication failed.","action":"Review API permissions and secrets. Never paste secrets into the app UI."}
    if "symbol" in low and ("not found" in low or "invalid" in low or "does not have market" in low):
        return {"code":"INVALID_SYMBOL","severity":"WARNING","message":"The selected contract is unavailable on this exchange.","action":"Refresh the market list and select an active perpetual/futures contract."}
    return {"code":type(err).__name__ if isinstance(err, Exception) else "EXCHANGE_ERROR","severity":"WARNING","message":"The exchange request failed.","action":"Retry or inspect Data Quality / Health for diagnostics."}

def safe_exchange_error(label: str, err: Any) -> str:
    info = classify_exchange_error(err)
    return f"{label}: {info['code']} — {info['message']}"

def round_down_step(value: float, step: Optional[float]) -> float:
    if not finite(value) or value < 0: return 0.0
    if not step or not finite(step) or step <= 0: return float(value)
    try:
        d, s = Decimal(str(value)), Decimal(str(step))
        return float((d / s).to_integral_value(rounding=ROUND_DOWN) * s)
    except (InvalidOperation, ValueError):
        return float(value)

def get_secret(name: str, default: Any = None) -> Any:
    env = os.getenv(name)
    if env is not None:
        return env
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

def truthy(v: Any) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "on", "y"}

def html_badge(text: str, tone: str = "info") -> str:
    return f'<span class="badge {tone}">{text}</span>'

def render_card(title: str, value: str, sub: str = "", tone: str = ""):
    st.markdown(f'<div class="pro-card {tone}"><div class="pro-title">{tr(title)}</div><div class="pro-value">{tr(value)}</div><div class="pro-sub">{tr(sub)}</div></div>', unsafe_allow_html=True)

def section_label(text: str):
    st.markdown(f'<div class="section-label">{tr(text)}</div>', unsafe_allow_html=True)

def error_box(title: str, exc: Exception):
    st.error(f"{title}: {type(exc).__name__}: {exc}")
    if st.session_state.get("debug_mode"):
        st.code(traceback.format_exc())

# ============================================================
# PERSISTENCE / SQLITE
# ============================================================
def db_connect():
    con = sqlite3.connect(DB_PATH, timeout=8, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db_connect() as con:
        con.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS journal(
          id TEXT PRIMARY KEY, opened_at TEXT, closed_at TEXT, exchange TEXT, symbol TEXT, side TEXT,
          setup TEXT, entry REAL, stop REAL, tps_json TEXT, risk_pct REAL, risk_usdt REAL, quantity REAL,
          leverage REAL, market_regime TEXT, long_score REAL, short_score REAL, data_confidence REAL,
          reason TEXT, outcome TEXT, pnl REAL, pnl_net REAL, r_result REAL, mfe REAL, mae REAL,
          duration_min REAL, fees REAL, funding REAL, emotion_json TEXT, discipline_json TEXT,
          screenshot TEXT, notes TEXT, mistake TEXT, lesson TEXT, source TEXT DEFAULT 'manual'
        );
        CREATE TABLE IF NOT EXISTS audit(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, event TEXT, severity TEXT, payload_json TEXT
        );
        CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS capital_flows(
          id TEXT PRIMARY KEY, ts TEXT, kind TEXT, amount REAL, note TEXT
        );
        CREATE TABLE IF NOT EXISTS playbook(
          id TEXT PRIMARY KEY, name TEXT UNIQUE, side TEXT, timeframes TEXT, min_rr REAL,
          volatility TEXT, session TEXT, conditions TEXT, invalidation TEXT, checklist TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts(
          id TEXT PRIMARY KEY, created_at TEXT, enabled INTEGER, severity TEXT, exchange TEXT, symbol TEXT,
          kind TEXT, operator TEXT, threshold REAL, note TEXT, last_triggered TEXT
        );
        CREATE TABLE IF NOT EXISTS paper_positions(
          id TEXT PRIMARY KEY, opened_at TEXT, exchange TEXT, symbol TEXT, side TEXT, entry REAL, qty REAL,
          remaining_qty REAL, leverage REAL, stop REAL, tps_json TEXT, alloc_json TEXT, fees REAL,
          funding REAL, realized_pnl REAL, mfe REAL, mae REAL, status TEXT, meta_json TEXT
        );
        CREATE TABLE IF NOT EXISTS paper_orders(
          id TEXT PRIMARY KEY, created_at TEXT, filled_at TEXT, position_id TEXT, exchange TEXT, symbol TEXT,
          side TEXT, kind TEXT, order_type TEXT, price REAL, qty REAL, state TEXT, meta_json TEXT
        );
        """)

def audit(event: str, payload: Dict[str, Any], severity: str = "INFO"):
    try:
        clean = {k: v for k, v in payload.items() if "secret" not in k.lower() and "key" not in k.lower() and "password" not in k.lower()}
        with db_connect() as con:
            con.execute("INSERT INTO audit(ts,event,severity,payload_json) VALUES(?,?,?,?)", (iso_now(), event, severity, json.dumps(clean, default=str)))
    except Exception:
        pass

def load_settings() -> Dict[str, Any]:
    try:
        with db_connect() as con:
            rows = con.execute("SELECT k,v FROM settings").fetchall()
        return {r["k"]: json.loads(r["v"]) for r in rows}
    except Exception:
        return {}

def save_setting(k: str, v: Any):
    with db_connect() as con:
        con.execute("INSERT INTO settings(k,v,updated_at) VALUES(?,?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v,updated_at=excluded.updated_at", (k, json.dumps(v), iso_now()))
    audit("SETTING_CHANGED", {"setting": k, "value": v})

def read_table(name: str) -> pd.DataFrame:
    allowed = {"journal", "audit", "capital_flows", "playbook", "alerts", "paper_positions", "paper_orders"}
    if name not in allowed: raise ValueError("Invalid table")
    try:
        with db_connect() as con:
            return pd.read_sql_query(f"SELECT * FROM {name}", con)
    except Exception:
        return pd.DataFrame()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "mode": "ANALYSIS ONLY", "exchange_id": DEFAULT_EXCHANGE, "symbol": DEFAULT_SYMBOL,
        "timeframe": "15m", "debug_mode": False, "kill_switch": False, "live_confirm_code": None,
        "live_confirm_hash": None, "last_order_hash": None, "api_errors": [], "api_health": {},
        "selected_nav": "Command Center", "paper_start_balance": 10000.0, "language": "es",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

# ============================================================
# EXCHANGE ADAPTERS
# ============================================================
class ExchangeAdapter:
    def __init__(self, exchange_id: str, private: bool = False, sandbox: bool = False):
        if ccxt is None:
            raise RuntimeError("ccxt is not installed")
        if exchange_id not in SUPPORTED_EXCHANGES:
            raise ValueError("Unsupported exchange")
        self.exchange_id = exchange_id
        self.private = private
        self.sandbox = sandbox
        cfg: Dict[str, Any] = {"enableRateLimit": True, "timeout": 12000}
        if exchange_id == "binanceusdm":
            cls = ccxt.binanceusdm
            cfg["options"] = {"defaultType": "future", "adjustForTimeDifference": True}
        elif exchange_id == "bybit":
            cls = ccxt.bybit
            cfg["options"] = {"defaultType": "swap", "adjustForTimeDifference": True}
        else:
            cls = ccxt.okx
            cfg["options"] = {"defaultType": "swap", "adjustForTimeDifference": True}
        if private:
            prefix = exchange_id.upper().replace("BINANCEUSDM", "BINANCE")
            api_key = get_secret(f"{prefix}_API_KEY")
            secret = get_secret(f"{prefix}_API_SECRET")
            password = get_secret(f"{prefix}_API_PASSWORD") or get_secret(f"{prefix}_PASSPHRASE")
            if not api_key or not secret:
                raise RuntimeError(f"Missing {prefix}_API_KEY / {prefix}_API_SECRET")
            cfg.update({"apiKey": api_key, "secret": secret})
            if exchange_id == "okx":
                if not password: raise RuntimeError("Missing OKX_API_PASSWORD / OKX_PASSPHRASE")
                cfg["password"] = password
        self.ex = cls(cfg)
        if sandbox:
            try: self.ex.set_sandbox_mode(True)
            except Exception as e: raise RuntimeError(f"Sandbox not supported/configured: {e}")
        t0 = time.perf_counter()
        retry_call(self.ex.load_markets)
        self.latency_ms = (time.perf_counter() - t0) * 1000

    def feature(self, symbol: str, path: str) -> Any:
        try:
            node = self.ex.features
            market = self.ex.market(symbol)
            mtype = market.get("type") or "swap"
            for p in path.split("."):
                node = node[p]
            return node
        except Exception:
            try:
                parts = path.split(".")
                return self.ex.feature_value(symbol, parts[0], ".".join(parts[1:])) if len(parts) > 1 else None
            except Exception:
                return None

    def contract_markets(self) -> List[Dict[str, Any]]:
        out = []
        for m in self.ex.markets.values():
            if not m.get("active", True): continue
            if not (m.get("swap") or m.get("future") or m.get("contract")): continue
            if m.get("linear") is False and self.exchange_id == "binanceusdm": continue
            if m.get("quote") not in {"USDT", "USDC", "USD"}: continue
            out.append(m)
        return sorted(out, key=lambda x: x.get("symbol", ""))

    def market_meta(self, symbol: str) -> Dict[str, Any]:
        m = self.ex.market(symbol)
        limits, precision = m.get("limits", {}), m.get("precision", {})
        return {
            "symbol": symbol, "id": m.get("id"), "active": m.get("active"), "type": m.get("type"),
            "linear": m.get("linear"), "inverse": m.get("inverse"), "contractSize": m.get("contractSize", 1.0),
            "tickSize": precision.get("price"), "stepSize": precision.get("amount"),
            "minQty": (limits.get("amount") or {}).get("min"), "maxQty": (limits.get("amount") or {}).get("max"),
            "minNotional": (limits.get("cost") or {}).get("min"), "maxNotional": (limits.get("cost") or {}).get("max"),
            "minLeverage": (limits.get("leverage") or {}).get("min"), "maxLeverage": (limits.get("leverage") or {}).get("max"),
            "precision": precision, "limits": limits,
        }

    def price_to_precision(self, symbol: str, value: float) -> float:
        return float(self.ex.price_to_precision(symbol, value))

    def amount_to_precision(self, symbol: str, value: float) -> float:
        return float(self.ex.amount_to_precision(symbol, value))

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        return retry_call(self.ex.fetch_ticker, symbol)

    def fetch_order_book(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        return retry_call(self.ex.fetch_order_book, symbol, limit)

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500, since: Optional[int] = None) -> pd.DataFrame:
        rows = retry_call(self.ex.fetch_ohlcv, symbol, timeframe, since, limit)
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        if df.empty: return df
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df.set_index("datetime").sort_index()

    def fetch_funding(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            if self.ex.has.get("fetchFundingRate"):
                return retry_call(self.ex.fetch_funding_rate, symbol)
        except Exception:
            pass
        return None

    def fetch_funding_history(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        if not self.ex.has.get("fetchFundingRateHistory"): return pd.DataFrame()
        try:
            data = retry_call(self.ex.fetch_funding_rate_history, symbol, None, limit)
            df = pd.DataFrame(data)
            if not df.empty and "timestamp" in df: df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df
        except Exception:
            return pd.DataFrame()

    def fetch_open_interest(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            if self.ex.has.get("fetchOpenInterest"):
                return retry_call(self.ex.fetch_open_interest, symbol)
        except Exception:
            pass
        return None

    def fetch_oi_history(self, symbol: str, timeframe: str = "5m", limit: int = 100) -> pd.DataFrame:
        if not self.ex.has.get("fetchOpenInterestHistory"): return pd.DataFrame()
        try:
            data = retry_call(self.ex.fetch_open_interest_history, symbol, timeframe, None, limit)
            df = pd.DataFrame(data)
            if not df.empty and "timestamp" in df: df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df
        except Exception:
            return pd.DataFrame()

    def fetch_recent_trades(self, symbol: str, limit: int = 500) -> pd.DataFrame:
        try:
            data = retry_call(self.ex.fetch_trades, symbol, None, limit)
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    def fetch_balance(self) -> Dict[str, Any]:
        return retry_call(self.ex.fetch_balance)

    def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not self.ex.has.get("fetchPositions"): return []
        return retry_call(self.ex.fetch_positions, symbols)

    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        return retry_call(self.ex.fetch_open_orders, symbol)

    def set_leverage(self, leverage: int, symbol: str, margin_mode: str = "isolated") -> Any:
        params = {"marginMode": margin_mode}
        try: return retry_call(self.ex.set_leverage, leverage, symbol, params)
        except Exception: return retry_call(self.ex.set_leverage, leverage, symbol)

    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float], params: Dict[str, Any]):
        return retry_call(self.ex.create_order, symbol, order_type, side, amount, price, params, retries=2)

    def cancel_all_orders(self, symbol: Optional[str] = None):
        if self.ex.has.get("cancelAllOrders"):
            return retry_call(self.ex.cancel_all_orders, symbol)
        orders = self.fetch_open_orders(symbol)
        out = []
        for o in orders:
            try: out.append(retry_call(self.ex.cancel_order, o["id"], o.get("symbol") or symbol))
            except Exception: pass
        return out

    def close(self):
        try: self.ex.close()
        except Exception: pass

# ============================================================
# PUBLIC MARKET DATA ROUTER
# Binance on Streamlit Community Cloud can reject futures REST
# requests from the hosting region. For ANALYSIS/PAPER, Binance
# public price/candle/order-book data therefore uses Binance's
# official market-data-only endpoint (data-api.binance.vision).
# Futures-only metrics remain real-only: if Binance Futures public
# endpoints are unavailable, funding/OI stay UNAVAILABLE.
# LIVE execution always re-validates against the actual futures
# exchange adapter and is never routed through the spot proxy.
# ============================================================
BINANCE_VISION_BASE = "https://data-api.binance.vision"
BINANCE_FAPI_BASE = "https://fapi.binance.com"
PUBLIC_HTTP_UA = f"{APP_NAME.replace(' ', '-')}/{APP_VERSION}"


def _http_json(base: str, path: str, params: Optional[Dict[str, Any]] = None, timeout: float = 8.0) -> Any:
    query = urlencode({k: v for k, v in (params or {}).items() if v is not None}, doseq=True)
    url = f"{base.rstrip('/')}/{path.lstrip('/')}" + (f"?{query}" if query else "")
    req = Request(url, headers={"User-Agent": PUBLIC_HTTP_UA, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = ""
        raise RuntimeError(f"HTTP {e.code} from {base}: {detail or e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"Network error from {base}: {getattr(e, 'reason', e)}") from e


def _binance_raw_symbol(symbol: str) -> str:
    text = str(symbol or "").strip().upper()
    if "/" in text:
        base, rest = text.split("/", 1)
        quote = rest.split(":", 1)[0]
        return f"{base}{quote}".replace("-", "")
    return text.replace(":USDT", "").replace("/", "").replace("-", "")


def _binance_ccxt_symbol(raw_symbol: str, quote: str = "USDT") -> str:
    raw = str(raw_symbol or "").upper()
    quote = str(quote or "USDT").upper()
    if raw.endswith(quote) and len(raw) > len(quote):
        base = raw[:-len(quote)]
        return f"{base}/{quote}:{quote}"
    return raw


def _filter_value(filters: Iterable[Dict[str, Any]], filter_type: str, key: str, default: Any = None) -> Any:
    for f in filters or []:
        if str(f.get("filterType")) == filter_type:
            return f.get(key, default)
    return default


@st.cache_data(ttl=1800, show_spinner=False)
def _vision_exchange_info() -> Dict[str, Any]:
    data = _http_json(BINANCE_VISION_BASE, "/api/v3/exchangeInfo", timeout=10)
    return data if isinstance(data, dict) else {}


def _vision_symbols() -> List[str]:
    info = _vision_exchange_info()
    out: List[str] = []
    for m in info.get("symbols", []) or []:
        try:
            if m.get("status") != "TRADING":
                continue
            if m.get("quoteAsset") != "USDT":
                continue
            if m.get("isSpotTradingAllowed") is False:
                continue
            out.append(_binance_ccxt_symbol(m.get("symbol"), "USDT"))
        except Exception:
            continue
    return sorted(set(out))


def _vision_market_meta(symbol: str) -> Dict[str, Any]:
    raw = _binance_raw_symbol(symbol)
    info = _vision_exchange_info()
    item = next((m for m in info.get("symbols", []) or [] if m.get("symbol") == raw), None)
    if not item:
        raise ValueError(f"{raw} is not available on Binance Vision spot market data")
    filters = item.get("filters", []) or []
    tick = safe_float(_filter_value(filters, "PRICE_FILTER", "tickSize"))
    step = safe_float(_filter_value(filters, "LOT_SIZE", "stepSize"))
    min_not = safe_float(_filter_value(filters, "NOTIONAL", "minNotional"))
    if not finite(min_not):
        min_not = safe_float(_filter_value(filters, "MIN_NOTIONAL", "minNotional"))
    # Spot filters are deliberately NOT treated as futures contract limits.
    # LIVE execution re-loads real futures market metadata through CCXT.
    return {
        "symbol": symbol,
        "id": raw,
        "active": item.get("status") == "TRADING",
        "type": "analysis-proxy",
        "linear": True,
        "inverse": False,
        "contractSize": 1.0,
        "tickSize": tick if finite(tick) else None,
        "stepSize": step if finite(step) else None,
        "minQty": None,
        "maxQty": None,
        "minNotional": None,
        "maxNotional": None,
        "minLeverage": None,
        "maxLeverage": None,
        "precision": {"price": tick if finite(tick) else None, "amount": step if finite(step) else None},
        "limits": {},
        "proxy_spot_min_notional": min_not if finite(min_not) else None,
        "data_source": "BINANCE_VISION_SPOT_PUBLIC_PROXY",
        "futures_spec_status": "REVALIDATE_ON_LIVE",
        "note": "Price/candle precision proxy only. Futures filters/leverage are intentionally not inferred from Spot.",
    }


def _vision_ticker(symbol: str) -> Dict[str, Any]:
    raw = _binance_raw_symbol(symbol)
    data = _http_json(BINANCE_VISION_BASE, "/api/v3/ticker/24hr", {"symbol": raw})
    book = {}
    try:
        book = _http_json(BINANCE_VISION_BASE, "/api/v3/ticker/bookTicker", {"symbol": raw})
    except Exception:
        pass
    ts = int(data.get("closeTime") or int(time.time() * 1000)) if isinstance(data, dict) else int(time.time() * 1000)
    return {
        "symbol": symbol,
        "last": safe_float(data.get("lastPrice")),
        "open": safe_float(data.get("openPrice")),
        "high": safe_float(data.get("highPrice")),
        "low": safe_float(data.get("lowPrice")),
        "bid": safe_float(book.get("bidPrice")),
        "ask": safe_float(book.get("askPrice")),
        "baseVolume": safe_float(data.get("volume")),
        "quoteVolume": safe_float(data.get("quoteVolume")),
        "percentage": safe_float(data.get("priceChangePercent")),
        "timestamp": ts,
        "datetime": pd.to_datetime(ts, unit="ms", utc=True).isoformat(),
        "info": data,
        "data_source": "BINANCE_VISION_SPOT_PUBLIC_PROXY",
    }


def _vision_orderbook(symbol: str, limit: int = 50) -> Dict[str, Any]:
    raw = _binance_raw_symbol(symbol)
    valid_limits = [5, 10, 20, 50, 100, 500, 1000, 5000]
    use_limit = min(valid_limits, key=lambda x: abs(x - max(5, min(int(limit or 50), 5000))))
    data = _http_json(BINANCE_VISION_BASE, "/api/v3/depth", {"symbol": raw, "limit": use_limit})
    return {
        "symbol": symbol,
        "bids": [[safe_float(p), safe_float(q)] for p, q, *_ in (data.get("bids", []) or [])],
        "asks": [[safe_float(p), safe_float(q)] for p, q, *_ in (data.get("asks", []) or [])],
        "timestamp": int(time.time() * 1000),
        "nonce": data.get("lastUpdateId"),
        "data_source": "BINANCE_VISION_SPOT_PUBLIC_PROXY",
    }


def _vision_ohlcv(symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    raw = _binance_raw_symbol(symbol)
    use_limit = max(30, min(int(limit or 500), 1000))
    rows = _http_json(BINANCE_VISION_BASE, "/api/v3/klines", {"symbol": raw, "interval": timeframe, "limit": use_limit}, timeout=10)
    parsed = []
    for r in rows or []:
        if not isinstance(r, list) or len(r) < 6:
            continue
        parsed.append([int(r[0]), safe_float(r[1]), safe_float(r[2]), safe_float(r[3]), safe_float(r[4]), safe_float(r[5])])
    df = pd.DataFrame(parsed, columns=["timestamp", "open", "high", "low", "close", "volume"])
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("datetime").sort_index()
    df.attrs["data_source"] = "BINANCE_VISION_SPOT_PUBLIC_PROXY"
    return df


def _vision_recent_trades(symbol: str, limit: int = 500) -> pd.DataFrame:
    raw = _binance_raw_symbol(symbol)
    use_limit = max(1, min(int(limit or 500), 1000))
    rows = _http_json(BINANCE_VISION_BASE, "/api/v3/aggTrades", {"symbol": raw, "limit": use_limit})
    data = []
    for r in rows or []:
        price = safe_float(r.get("p")); amount = safe_float(r.get("q")); ts = int(r.get("T") or 0)
        # Binance m=True => buyer is maker, therefore the aggressive/taker side is SELL.
        side = "sell" if bool(r.get("m")) else "buy"
        data.append({"id": r.get("a"), "timestamp": ts, "datetime": pd.to_datetime(ts, unit="ms", utc=True) if ts else pd.NaT,
                     "symbol": symbol, "side": side, "price": price, "amount": amount, "cost": price * amount,
                     "info": r, "data_source": "BINANCE_VISION_SPOT_PUBLIC_PROXY"})
    return pd.DataFrame(data)


@st.cache_data(ttl=20, show_spinner=False)
def _vision_all_tickers() -> List[Dict[str, Any]]:
    data = _http_json(BINANCE_VISION_BASE, "/api/v3/ticker/24hr", timeout=12)
    return data if isinstance(data, list) else []


def _fapi_direct_current(symbol: str) -> Dict[str, Any]:
    """Best-effort REAL Binance Futures derivatives data. Never fabricates fallbacks."""
    raw = _binance_raw_symbol(symbol)
    out: Dict[str, Any] = {"funding": None, "oi": None, "errors": [], "source": "BINANCE_FUTURES_PUBLIC"}
    try:
        p = _http_json(BINANCE_FAPI_BASE, "/fapi/v1/premiumIndex", {"symbol": raw}, timeout=5)
        if isinstance(p, dict):
            out["funding"] = {
                "symbol": symbol,
                "fundingRate": safe_float(p.get("lastFundingRate")),
                "markPrice": safe_float(p.get("markPrice")),
                "indexPrice": safe_float(p.get("indexPrice")),
                "timestamp": int(p.get("time") or int(time.time() * 1000)),
                "info": p,
                "data_source": "BINANCE_FUTURES_PUBLIC",
            }
    except Exception as e:
        out["errors"].append(f"funding: {type(e).__name__}: {e}")
    try:
        o = _http_json(BINANCE_FAPI_BASE, "/fapi/v1/openInterest", {"symbol": raw}, timeout=5)
        if isinstance(o, dict):
            out["oi"] = {"symbol": symbol, "openInterestAmount": safe_float(o.get("openInterest")),
                         "timestamp": int(o.get("time") or int(time.time() * 1000)), "info": o,
                         "data_source": "BINANCE_FUTURES_PUBLIC"}
    except Exception as e:
        out["errors"].append(f"oi: {type(e).__name__}: {e}")
    return out


def _fapi_direct_history(symbol: str) -> Dict[str, pd.DataFrame]:
    """Best-effort REAL futures history. Empty frames mean unavailable, never synthetic."""
    raw = _binance_raw_symbol(symbol)
    oi_df = pd.DataFrame(); funding_df = pd.DataFrame()
    try:
        rows = _http_json(BINANCE_FAPI_BASE, "/futures/data/openInterestHist", {"symbol": raw, "period": "5m", "limit": 100}, timeout=5)
        mapped = []
        for r in rows or []:
            mapped.append({"symbol": symbol, "timestamp": int(r.get("timestamp") or 0),
                           "openInterestAmount": safe_float(r.get("sumOpenInterest")),
                           "openInterestValue": safe_float(r.get("sumOpenInterestValue")), "info": r})
        oi_df = pd.DataFrame(mapped)
        if not oi_df.empty:
            oi_df["datetime"] = pd.to_datetime(oi_df["timestamp"], unit="ms", utc=True)
    except Exception:
        pass
    try:
        rows = _http_json(BINANCE_FAPI_BASE, "/fapi/v1/fundingRate", {"symbol": raw, "limit": 100}, timeout=5)
        mapped = []
        for r in rows or []:
            mapped.append({"symbol": symbol, "timestamp": int(r.get("fundingTime") or 0),
                           "fundingRate": safe_float(r.get("fundingRate")), "info": r})
        funding_df = pd.DataFrame(mapped)
        if not funding_df.empty:
            funding_df["datetime"] = pd.to_datetime(funding_df["timestamp"], unit="ms", utc=True)
    except Exception:
        pass
    return {"oi_history": oi_df, "funding_history": funding_df}


def public_data_source_label(exchange_id: str) -> str:
    return "Binance Vision · public Spot proxy" if exchange_id == "binanceusdm" else f"{SUPPORTED_EXCHANGES.get(exchange_id, exchange_id)} · CCXT"


@st.cache_data(ttl=1800, show_spinner=False)
def cached_market_symbols(exchange_id: str) -> List[str]:
    if exchange_id == "binanceusdm":
        return _vision_symbols()
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return [m["symbol"] for m in ad.contract_markets()]
    finally:
        ad.close()


@st.cache_data(ttl=300, show_spinner=False)
def cached_market_meta(exchange_id: str, symbol: str) -> Dict[str, Any]:
    if exchange_id == "binanceusdm":
        return _vision_market_meta(symbol)
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return ad.market_meta(symbol)
    finally:
        ad.close()


@st.cache_data(ttl=12, show_spinner=False)
def cached_ticker(exchange_id: str, symbol: str) -> Dict[str, Any]:
    if exchange_id == "binanceusdm":
        return _vision_ticker(symbol)
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return ad.fetch_ticker(symbol)
    finally:
        ad.close()


@st.cache_data(ttl=15, show_spinner=False)
def cached_orderbook(exchange_id: str, symbol: str, limit: int = 50) -> Dict[str, Any]:
    if exchange_id == "binanceusdm":
        return _vision_orderbook(symbol, limit)
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return ad.fetch_order_book(symbol, limit)
    finally:
        ad.close()


@st.cache_data(ttl=30, show_spinner=False)
def cached_ohlcv(exchange_id: str, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    if exchange_id == "binanceusdm":
        return _vision_ohlcv(symbol, timeframe, limit)
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return ad.fetch_ohlcv(symbol, timeframe, limit)
    finally:
        ad.close()


@st.cache_data(ttl=60, show_spinner=False)
def cached_derivatives(exchange_id: str, symbol: str) -> Dict[str, Any]:
    if exchange_id == "binanceusdm":
        return _fapi_direct_current(symbol)
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return {"funding": ad.fetch_funding(symbol), "oi": ad.fetch_open_interest(symbol), "source": "CCXT_FUTURES", "errors": []}
    finally:
        ad.close()


@st.cache_data(ttl=90, show_spinner=False)
def cached_derivatives_history(exchange_id: str, symbol: str) -> Dict[str, pd.DataFrame]:
    if exchange_id == "binanceusdm":
        return _fapi_direct_history(symbol)
    ad = ExchangeAdapter(exchange_id, private=False)
    try:
        return {"oi_history": ad.fetch_oi_history(symbol, "5m", 100), "funding_history": ad.fetch_funding_history(symbol, 100)}
    finally:
        ad.close()

# ============================================================
# INDICATORS / MARKET ENGINES
# ============================================================
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or len(df) < 30:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    x = df.copy()
    c, h, l, v = x["close"], x["high"], x["low"], x["volume"]
    x["ema20"] = c.ewm(span=20, adjust=False).mean()
    x["ema50"] = c.ewm(span=50, adjust=False).mean()
    x["ema200"] = c.ewm(span=200, adjust=False).mean()
    x["sma20"] = c.rolling(20).mean()
    x["sma50"] = c.rolling(50).mean()
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    x["rsi"] = 100 - 100 / (1 + rs)
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    x["macd"] = ema12 - ema26
    x["macd_signal"] = x["macd"].ewm(span=9, adjust=False).mean()
    x["macd_hist"] = x["macd"] - x["macd_signal"]
    prev_close = c.shift(1)
    tr = pd.concat([(h-l).abs(), (h-prev_close).abs(), (l-prev_close).abs()], axis=1).max(axis=1)
    x["atr"] = tr.ewm(alpha=1/14, adjust=False).mean()
    x["atr_pct"] = x["atr"] / c.replace(0, np.nan) * 100
    plus_dm = h.diff().where((h.diff() > -l.diff()) & (h.diff() > 0), 0.0)
    minus_dm = (-l.diff()).where((-l.diff() > h.diff()) & (-l.diff() > 0), 0.0)
    atr14 = tr.ewm(alpha=1/14, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr14.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr14.replace(0, np.nan)
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    x["adx"] = dx.ewm(alpha=1/14, adjust=False).mean()
    x["plus_di"], x["minus_di"] = plus_di, minus_di
    std20 = c.rolling(20).std(ddof=0)
    x["bb_mid"] = x["sma20"]
    x["bb_upper"] = x["bb_mid"] + 2 * std20
    x["bb_lower"] = x["bb_mid"] - 2 * std20
    x["bb_width"] = (x["bb_upper"] - x["bb_lower"]) / x["bb_mid"].replace(0, np.nan) * 100
    x["donchian_high"] = h.rolling(20).max()
    x["donchian_low"] = l.rolling(20).min()
    typical = (h+l+c)/3
    session_key = pd.Series(x.index.date, index=x.index)
    x["vwap"] = ((typical*v).groupby(session_key).cumsum() / v.groupby(session_key).cumsum().replace(0, np.nan))
    ret = np.log(c / c.shift(1))
    x["hist_vol"] = ret.rolling(30).std(ddof=0) * np.sqrt(365) * 100
    x["rvol"] = v / v.rolling(20).mean().replace(0, np.nan)
    x["vol_z"] = (v - v.rolling(50).mean()) / v.rolling(50).std(ddof=0).replace(0, np.nan)
    # Supertrend (10,3)
    hl2 = (h+l)/2
    upper = hl2 + 3*x["atr"]
    lower = hl2 - 3*x["atr"]
    final_u, final_l = upper.copy(), lower.copy()
    st_dir = pd.Series(index=x.index, dtype=float)
    supertrend = pd.Series(index=x.index, dtype=float)
    for i in range(1, len(x)):
        pi, ci = x.index[i-1], x.index[i]
        final_u.loc[ci] = upper.loc[ci] if (upper.loc[ci] < final_u.loc[pi] or c.loc[pi] > final_u.loc[pi]) else final_u.loc[pi]
        final_l.loc[ci] = lower.loc[ci] if (lower.loc[ci] > final_l.loc[pi] or c.loc[pi] < final_l.loc[pi]) else final_l.loc[pi]
        prev_dir = st_dir.loc[pi] if finite(st_dir.loc[pi]) else 1.0
        if prev_dir > 0:
            st_dir.loc[ci] = -1.0 if c.loc[ci] < final_l.loc[ci] else 1.0
        else:
            st_dir.loc[ci] = 1.0 if c.loc[ci] > final_u.loc[ci] else -1.0
        supertrend.loc[ci] = final_l.loc[ci] if st_dir.loc[ci] > 0 else final_u.loc[ci]
    x["supertrend"] = supertrend
    x["supertrend_dir"] = st_dir
    return x

def swing_structure(df: pd.DataFrame, left: int = 3, right: int = 3) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    if df.empty or len(df) < left + right + 5:
        return pd.DataFrame(), {"trend":"UNKNOWN", "bos":None, "choch":None, "compression":False, "expansion":False}
    x = df.copy()
    h, l = x["high"], x["low"]
    win = left + right + 1
    sh = h.eq(h.rolling(win, center=True).max())
    sl = l.eq(l.rolling(win, center=True).min())
    swings = []
    last_high = last_low = None
    for ts in x.index:
        if bool(sh.loc[ts]):
            p = float(h.loc[ts]); label = "SH" if last_high is None else ("HH" if p > last_high else "LH")
            swings.append({"time":ts,"kind":"HIGH","price":p,"label":label}); last_high = p
        if bool(sl.loc[ts]):
            p = float(l.loc[ts]); label = "SL" if last_low is None else ("HL" if p > last_low else "LL")
            swings.append({"time":ts,"kind":"LOW","price":p,"label":label}); last_low = p
    sdf = pd.DataFrame(swings)
    highs = sdf[sdf["kind"]=="HIGH"].tail(3) if not sdf.empty else pd.DataFrame()
    lows = sdf[sdf["kind"]=="LOW"].tail(3) if not sdf.empty else pd.DataFrame()
    trend = "RANGE"
    if len(highs)>=2 and len(lows)>=2:
        hu = highs.iloc[-1]["price"] > highs.iloc[-2]["price"]
        lu = lows.iloc[-1]["price"] > lows.iloc[-2]["price"]
        hd = highs.iloc[-1]["price"] < highs.iloc[-2]["price"]
        ld = lows.iloc[-1]["price"] < lows.iloc[-2]["price"]
        if hu and lu: trend = "UPTREND"
        elif hd and ld: trend = "DOWNTREND"
        else: trend = "TRANSITION"
    last_close = float(x["close"].iloc[-1])
    bos = None
    if len(highs)>=1 and last_close > float(highs.iloc[-1]["price"]): bos = "BULLISH BOS"
    if len(lows)>=1 and last_close < float(lows.iloc[-1]["price"]): bos = "BEARISH BOS"
    choch = None
    if trend == "UPTREND" and len(lows)>=1 and last_close < float(lows.iloc[-1]["price"]): choch = "BEARISH CHOCH"
    if trend == "DOWNTREND" and len(highs)>=1 and last_close > float(highs.iloc[-1]["price"]): choch = "BULLISH CHOCH"
    recent_range = (x["high"].rolling(20).max()-x["low"].rolling(20).min()) / x["close"] * 100
    rr = recent_range.iloc[-1] if finite(recent_range.iloc[-1]) else np.nan
    rr_hist = recent_range.dropna().tail(150)
    compression = bool(len(rr_hist)>20 and rr <= rr_hist.quantile(.2))
    expansion = bool(len(rr_hist)>20 and rr >= rr_hist.quantile(.8))
    return sdf, {"trend":trend,"bos":bos,"choch":choch,"compression":compression,"expansion":expansion}

def support_resistance(df: pd.DataFrame, swings: pd.DataFrame, max_levels: int = 12) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    last = float(df["close"].iloc[-1]); atr = safe_float(df.get("atr", pd.Series([np.nan])).iloc[-1], last*0.01)
    tol = max(atr*0.25, last*0.0005)
    candidates: List[Tuple[str,float,str]] = []
    if not swings.empty:
        for _, r in swings.tail(40).iterrows(): candidates.append((r["label"], float(r["price"]), "OBSERVED_SWING"))
    if len(df) >= 2:
        prev_day = df[df.index.date < df.index[-1].date()]
        if not prev_day.empty:
            d = prev_day[prev_day.index.date == prev_day.index[-1].date()]
            candidates += [("PDH", float(d.high.max()), "OBSERVED_REFERENCE"), ("PDL", float(d.low.min()), "OBSERVED_REFERENCE")]
    weekly = df.tail(min(len(df), 7*24*12))
    if not weekly.empty:
        candidates += [("RECENT_HIGH", float(weekly.high.max()), "OBSERVED_REFERENCE"),("RECENT_LOW", float(weekly.low.min()), "OBSERVED_REFERENCE")]
    clusters: List[Dict[str,Any]] = []
    for typ, price, source in candidates:
        found = None
        for c in clusters:
            if abs(c["price"]-price) <= tol:
                found = c; break
        if found:
            found["prices"].append(price); found["price"] = float(np.mean(found["prices"])); found["tests"] += 1; found["types"].add(typ)
        else:
            clusters.append({"price":price,"prices":[price],"tests":1,"types":{typ},"source":source})
    rows=[]
    for c in clusters:
        dist=(c["price"]/last-1)*100
        rows.append({"level":c["price"],"type":"/".join(sorted(c["types"])),"tests":c["tests"],"distance_pct":dist,
                     "strength":clamp(35+c["tests"]*12+max(0,20-abs(dist)*2),0,100),"state":"ABOVE" if c["price"]>last else "BELOW","source":c["source"]})
    return pd.DataFrame(rows).sort_values("strength",ascending=False).head(max_levels) if rows else pd.DataFrame()

def liquidity_zones(df: pd.DataFrame, swings: pd.DataFrame) -> pd.DataFrame:
    if df.empty or swings.empty: return pd.DataFrame()
    last=float(df.close.iloc[-1]); atr=safe_float(df.get("atr",pd.Series([np.nan])).iloc[-1],last*.01); tol=max(atr*.18,last*.0004)
    rows=[]
    for kind,label in [("HIGH","EQUAL HIGHS"),("LOW","EQUAL LOWS")]:
        arr=swings[swings.kind==kind].tail(20)
        for i in range(len(arr)):
            near=arr[(arr.price-arr.iloc[i].price).abs()<=tol]
            if len(near)>=2:
                p=float(near.price.mean())
                rows.append({"zone":label,"price":p,"touches":len(near),"distance_pct":(p/last-1)*100,"evidence":"OBSERVED swings; stop-cluster interpretation is INFERRED"})
    rows += [{"zone":"SWING HIGH LIQUIDITY","price":float(r.price),"touches":1,"distance_pct":(float(r.price)/last-1)*100,"evidence":"OBSERVED level; liquidity is INFERRED"} for _,r in swings[swings.kind=="HIGH"].tail(3).iterrows()]
    rows += [{"zone":"SWING LOW LIQUIDITY","price":float(r.price),"touches":1,"distance_pct":(float(r.price)/last-1)*100,"evidence":"OBSERVED level; liquidity is INFERRED"} for _,r in swings[swings.kind=="LOW"].tail(3).iterrows()]
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["zone","price"]).sort_values("distance_pct",key=lambda s:s.abs()).head(12)

def volume_engine(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or len(df)<25: return {"status":"UNAVAILABLE"}
    r=df.iloc[-1]; prev=df.iloc[-2]
    rvol=safe_float(r.get("rvol")); z=safe_float(r.get("vol_z")); close=float(r.close)
    status="NORMAL"
    if finite(rvol) and rvol>=2: status="SPIKE"
    elif finite(rvol) and rvol<.6: status="CONTRACTION"
    elif finite(rvol) and rvol>1.25: status="EXPANSION"
    pv_div="NONE"
    if close>float(prev.close) and float(r.volume)<float(prev.volume)*.7: pv_div="PRICE UP / VOLUME WEAK"
    if close<float(prev.close) and float(r.volume)<float(prev.volume)*.7: pv_div="PRICE DOWN / VOLUME WEAK"
    return {"status":status,"rvol":rvol,"zscore":z,"divergence":pv_div,"volume":float(r.volume)}

def order_flow_from_trades(trades: pd.DataFrame) -> Dict[str, Any]:
    if trades.empty or "side" not in trades.columns or "amount" not in trades.columns:
        return {"status":"UNAVAILABLE","reason":"Exchange recent trades do not expose usable taker side."}
    t=trades.copy(); t["amount"]=pd.to_numeric(t["amount"],errors="coerce"); t=t.dropna(subset=["amount"])
    buys=float(t.loc[t.side.astype(str).str.lower()=="buy","amount"].sum()); sells=float(t.loc[t.side.astype(str).str.lower()=="sell","amount"].sum())
    if buys+sells<=0: return {"status":"UNAVAILABLE","reason":"No classified trade volume."}
    delta=buys-sells
    return {"status":"OBSERVED","buy_volume":buys,"sell_volume":sells,"delta":delta,"imbalance":delta/(buys+sells)*100,"note":"Based only on recent trades returned by the selected exchange."}

def volatility_regime(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or "atr_pct" not in df: return {"regime":"UNKNOWN","percentile":np.nan}
    s=df["atr_pct"].dropna().tail(250)
    if len(s)<20: return {"regime":"UNKNOWN","percentile":np.nan}
    cur=float(s.iloc[-1]); pct=float((s<=cur).mean()*100)
    regime="LOW" if pct<25 else "NORMAL" if pct<70 else "HIGH" if pct<90 else "EXTREME"
    return {"regime":regime,"percentile":pct,"atr_pct":cur,"bb_width":safe_float(df.bb_width.iloc[-1])}

def trend_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or len(df)<30: return {"trend":"UNKNOWN","strength":0,"momentum":"UNKNOWN"}
    r=df.iloc[-1]; c=float(r.close); e20=safe_float(r.ema20); e50=safe_float(r.ema50); e200=safe_float(r.ema200); adx=safe_float(r.adx,0); rsi=safe_float(r.rsi,50)
    bull=sum([c>e20 if finite(e20) else False,e20>e50 if finite(e20) and finite(e50) else False,e50>e200 if finite(e50) and finite(e200) else False])
    bear=sum([c<e20 if finite(e20) else False,e20<e50 if finite(e20) and finite(e50) else False,e50<e200 if finite(e50) and finite(e200) else False])
    trend="UP" if bull>=2 else "DOWN" if bear>=2 else "MIXED"
    strength=clamp(adx,0,50)*2
    momentum="BULLISH" if rsi>55 and safe_float(r.macd_hist,0)>0 else "BEARISH" if rsi<45 and safe_float(r.macd_hist,0)<0 else "NEUTRAL"
    return {"trend":trend,"strength":strength,"momentum":momentum,"rsi":rsi,"adx":adx}

def market_regime(df: pd.DataFrame, structure: Dict[str,Any]) -> EngineResult:
    if df.empty or len(df)<50: return EngineResult("UNKNOWN",0,0,["Insufficient candle history"],[])
    t=trend_snapshot(df); v=volatility_regime(df); r=df.iloc[-1]
    factors=[]; conflicts=[]; score=50.0
    if t["trend"]=="UP": score+=18; factors.append("Price/EMA stack supports upside")
    elif t["trend"]=="DOWN": score-=18; factors.append("Price/EMA stack supports downside")
    else: conflicts.append("EMA trend alignment is mixed")
    if structure.get("trend")=="UPTREND": score+=14; factors.append("Swing structure: HH/HL")
    elif structure.get("trend")=="DOWNTREND": score-=14; factors.append("Swing structure: LH/LL")
    elif structure.get("trend")=="TRANSITION": conflicts.append("Swing structure is transitional")
    adx=t.get("adx",0)
    if adx<18: conflicts.append("ADX indicates weak trend strength")
    elif adx>28: factors.append(f"ADX trend strength {adx:.1f}")
    if structure.get("compression"): factors.append("Range compression detected")
    if structure.get("expansion"): factors.append("Range expansion detected")
    direction = "UPTREND" if score>=60 else "DOWNTREND" if score<=40 else "RANGE/TRANSITION"
    intensity="STRONG " if adx>=32 and direction!="RANGE/TRANSITION" else "WEAK " if adx<20 and direction!="RANGE/TRANSITION" else ""
    status=(intensity+direction).strip()
    if structure.get("compression"): status += " + COMPRESSION"
    elif structure.get("expansion"): status += " + EXPANSION"
    conf=clamp(45+abs(score-50)*1.2+min(adx,40)*.5-len(conflicts)*6,10,95)
    return EngineResult(status,score,conf,factors,conflicts,{"volatility":v,"trend":t})

def mtf_analysis(exchange_id: str, symbol: str, timeframes: List[str]) -> pd.DataFrame:
    rows=[]
    for tf in timeframes:
        try:
            df=add_indicators(cached_ohlcv(exchange_id,symbol,tf,350))
            _,s=swing_structure(df)
            t=trend_snapshot(df); v=volatility_regime(df); reg=market_regime(df,s)
            r=df.iloc[-1]
            rows.append({"TF":tf,"Trend":t["trend"],"Structure":s["trend"],"Regime":reg.status,"Confidence":reg.confidence,"RSI":safe_float(r.rsi),"MACD Hist":safe_float(r.macd_hist),"ADX":safe_float(r.adx),"ATR%":safe_float(r.atr_pct),"RVOL":safe_float(r.rvol),"Volatility":v["regime"],"BOS":s.get("bos") or "—"})
        except Exception as e:
            rows.append({"TF":tf,"Trend":"ERROR","Structure":"—","Regime":type(e).__name__,"Confidence":0})
    return pd.DataFrame(rows)

def derivatives_engine(exchange_id: str, symbol: str, df: pd.DataFrame) -> Dict[str,Any]:
    result={"status":"PARTIAL","funding":None,"oi":None,"funding_context":"UNAVAILABLE","oi_context":"UNAVAILABLE"}
    try:
        d=cached_derivatives(exchange_id,symbol); fr=d.get("funding") or {}; oi=d.get("oi") or {}
        result["raw_funding"]=fr
        rate=safe_float(fr.get("fundingRate")); result["funding"]=rate
        if finite(rate):
            bp=rate*100
            result["funding_context"]="CROWDED LONGS RISK" if bp>.05 else "CROWDED SHORTS RISK" if bp<-.05 else "NEUTRAL / NORMAL"
        oi_val=safe_float(oi.get("openInterestAmount",oi.get("openInterestValue"))); result["oi"]=oi_val
        result["status"]="AVAILABLE" if finite(rate) or finite(oi_val) else "UNAVAILABLE"
    except Exception as e: result["error"]=str(e)
    try:
        hist_pack=cached_derivatives_history(exchange_id,symbol); hist=hist_pack.get("oi_history",pd.DataFrame()); fh=hist_pack.get("funding_history",pd.DataFrame())
        if not hist.empty:
            col="openInterestAmount" if "openInterestAmount" in hist.columns else "openInterestValue" if "openInterestValue" in hist.columns else None
            if col:
                s=pd.to_numeric(hist[col],errors="coerce").dropna()
                if len(s)>=2:
                    result["oi_change_5m"]=pct_change(s.iloc[-1],s.iloc[-2]); result["oi_change_1h"]=pct_change(s.iloc[-1],s.iloc[-13] if len(s)>=13 else s.iloc[0]); result["oi_history"]=hist
        if not fh.empty and "fundingRate" in fh:
            fs=pd.to_numeric(fh.fundingRate,errors="coerce").dropna()
            if len(fs):
                cur=result.get("funding"); result["funding_mean"]=float(fs.mean()); result["funding_std"]=float(fs.std(ddof=0)); result["funding_percentile"]=float((fs <= cur).mean()*100) if finite(cur) else np.nan; result["funding_history"]=fh
    except Exception: pass
    if not df.empty and finite(result.get("oi_change_1h")):
        pchg=pct_change(df.close.iloc[-1],df.close.iloc[-min(len(df),13)])
        ochg=result["oi_change_1h"]
        if pchg>0 and ochg>0: result["oi_context"]="PRICE ↑ + OI ↑: new participation supports move"
        elif pchg>0 and ochg<0: result["oi_context"]="PRICE ↑ + OI ↓: short covering / participation falling possible"
        elif pchg<0 and ochg>0: result["oi_context"]="PRICE ↓ + OI ↑: new short participation possible"
        else: result["oi_context"]="PRICE ↓ + OI ↓: deleveraging / long liquidation possible"
    return result

def data_confidence(df: pd.DataFrame, ticker: Dict[str,Any], deriv: Dict[str,Any], orderbook: Optional[Dict[str,Any]]) -> EngineResult:
    score=100; factors=[]; conflicts=[]
    if df.empty: return EngineResult("STALE/NO DATA",0,0,[],["No candles"])
    age=(utc_now()-df.index[-1].to_pydatetime()).total_seconds() if hasattr(df.index[-1],"to_pydatetime") else 9999
    diffs=pd.Series(df.index).diff().dt.total_seconds().dropna()
    tf_seconds=float(diffs.median()) if len(diffs) and finite(diffs.median()) else 60.0
    score -= 45 if age>tf_seconds*3.5 else 20 if age>tf_seconds*1.8 else 0
    if age<tf_seconds*1.8: factors.append("Candles are fresh for their timeframe")
    else: conflicts.append(f"Last candle age {age/60:.1f}m vs timeframe ~{tf_seconds/60:.1f}m")
    if ticker and finite(ticker.get("last")): factors.append("Ticker available")
    else: score-=25; conflicts.append("Ticker unavailable")
    if orderbook and orderbook.get("bids") and orderbook.get("asks"): factors.append("Order book available")
    else: score-=15; conflicts.append("Order book unavailable")
    if deriv.get("status")!="AVAILABLE": score-=10; conflicts.append("Derivatives data partial/unavailable")
    score=clamp(score,0,100); status="HIGH" if score>=85 else "GOOD" if score>=70 else "DEGRADED" if score>=45 else "LOW"
    return EngineResult(status,score,score,factors,conflicts,{"age_seconds":age})

def confluence_engine(df: pd.DataFrame, structure: Dict[str,Any], deriv: Dict[str,Any], levels: pd.DataFrame, orderflow: Dict[str,Any], confidence: EngineResult) -> Dict[str,Any]:
    if df.empty: return {"long":0,"short":0,"no_trade":100,"categories":{},"evidence":[],"conflicts":["No market data"]}
    r=df.iloc[-1]; categories={}; evidence=[]; conflicts=[]
    # scores are directional: -100 short .. +100 long. Weights are explicit.
    t=trend_snapshot(df); categories["TREND"] = 60 if t["trend"]=="UP" else -60 if t["trend"]=="DOWN" else 0
    categories["STRUCTURE"] = 65 if structure.get("trend")=="UPTREND" else -65 if structure.get("trend")=="DOWNTREND" else 0
    rsi=safe_float(r.rsi,50); mh=safe_float(r.macd_hist,0); categories["MOMENTUM"] = clamp((rsi-50)*2 + np.sign(mh)*20,-100,100)
    ve=volume_engine(df); categories["VOLUME"] = 15*np.sign(float(r.close)-float(df.close.iloc[-2])) if ve.get("status") in {"SPIKE","EXPANSION"} else 0
    vr=volatility_regime(df); categories["VOLATILITY"] = 0 if vr["regime"] in {"NORMAL","HIGH"} else -10 if vr["regime"]=="EXTREME" else 5
    fund=deriv.get("funding"); categories["DERIVATIVES"] = clamp(-safe_float(fund,0)*100000,-25,25) if finite(fund) else 0
    oi_context=deriv.get("oi_context",""); categories["POSITIONING"] = 15 if "PRICE ↑ + OI ↑" in oi_context else -15 if "PRICE ↓ + OI ↑" in oi_context else 0
    categories["LIQUIDITY"] = 0
    if not levels.empty:
        below=levels[levels.distance_pct<0].sort_values("distance_pct",ascending=False); above=levels[levels.distance_pct>0].sort_values("distance_pct")
        if len(below) and abs(float(below.iloc[0].distance_pct))<.5: categories["LIQUIDITY"] += 8
        if len(above) and abs(float(above.iloc[0].distance_pct))<.5: categories["LIQUIDITY"] -= 8
    categories["RISK"] = 0 if vr["regime"]!="EXTREME" else -20
    weights={"TREND":.18,"STRUCTURE":.18,"MOMENTUM":.14,"VOLUME":.09,"VOLATILITY":.08,"DERIVATIVES":.10,"LIQUIDITY":.08,"POSITIONING":.08,"RISK":.07}
    directional=sum(categories[k]*weights[k] for k in weights)
    long_score=clamp(50+directional/2,0,100); short_score=clamp(50-directional/2,0,100)
    contradiction=sum(1 for v in categories.values() if np.sign(v)!=0 and np.sign(v)!=np.sign(directional))
    no_trade=clamp(25 + contradiction*8 + (100-confidence.score)*.55 + (20 if vr["regime"]=="EXTREME" else 0) + (15 if t["strength"]<30 else 0),0,100)
    for k,v in categories.items():
        if v>20: evidence.append(f"{k} supports LONG ({v:.0f})")
        elif v<-20: evidence.append(f"{k} supports SHORT ({v:.0f})")
        elif abs(v)<10: conflicts.append(f"{k} is neutral/weak")
    return {"long":long_score,"short":short_score,"no_trade":no_trade,"categories":categories,"weights":weights,"evidence":evidence,"conflicts":conflicts,"signal_strength":max(long_score,short_score),"data_confidence":confidence.score}

def scenario_engine(df: pd.DataFrame, levels: pd.DataFrame, confl: Dict[str,Any]) -> Dict[str,Dict[str,Any]]:
    if df.empty: return {}
    r=df.iloc[-1]; price=float(r.close); atr=safe_float(r.atr,price*.01)
    below=levels[levels.level<price].sort_values("level",ascending=False) if not levels.empty else pd.DataFrame()
    above=levels[levels.level>price].sort_values("level") if not levels.empty else pd.DataFrame()
    long_stop=float(below.iloc[0].level)-.15*atr if len(below) else price-1.5*atr
    short_stop=float(above.iloc[0].level)+.15*atr if len(above) else price+1.5*atr
    long_risk=max(price-long_stop,atr*.3); short_risk=max(short_stop-price,atr*.3)
    return {
      "LONG":{"trigger":f"Acceptance above {price_fmt(price + .2*atr)} or defended pullback","entry":price,"invalidation":long_stop,"stop":long_stop,"tp1":price+long_risk*1.5,"tp2":price+long_risk*2.5,"tp3":price+long_risk*4,"score":confl["long"],"risk":"Avoid chasing if price expands >1 ATR before entry."},
      "SHORT":{"trigger":f"Acceptance below {price_fmt(price - .2*atr)} or failed reclaim","entry":price,"invalidation":short_stop,"stop":short_stop,"tp1":price-short_risk*1.5,"tp2":price-short_risk*2.5,"tp3":price-short_risk*4,"score":confl["short"],"risk":"Avoid chasing if price expands >1 ATR before entry."},
      "NEUTRAL":{"trigger":"No clean activation / conflicting evidence","entry":price,"invalidation":None,"stop":None,"tp1":None,"tp2":None,"tp3":None,"score":confl["no_trade"],"risk":"Capital preservation is the default when evidence is weak."}
    }
# ============================================================
# RISK / TRADE CALCULATION
# ============================================================
def validate_plan_sanity(p: TradePlan) -> List[ValidationIssue]:
    issues=[]
    vals=[p.entry,p.stop,p.capital,p.risk_pct,p.leverage]
    if any(not finite(v) or float(v)<=0 for v in vals): issues.append(ValidationIssue("CRITICAL","INVALID_NUMERIC","Entry, stop, capital, risk and leverage must be positive finite values.")); return issues
    if p.side=="LONG" and p.stop>=p.entry: issues.append(ValidationIssue("CRITICAL","STOP_DIRECTION","LONG stop must be below entry."))
    if p.side=="SHORT" and p.stop<=p.entry: issues.append(ValidationIssue("CRITICAL","STOP_DIRECTION","SHORT stop must be above entry."))
    if not p.tps: issues.append(ValidationIssue("CRITICAL","NO_TP","At least one take-profit is required for execution."))
    for i,tp in enumerate(p.tps,1):
        if not finite(tp) or tp<=0: issues.append(ValidationIssue("CRITICAL",f"TP{i}_INVALID",f"TP{i} is invalid."))
        elif p.side=="LONG" and tp<=p.entry: issues.append(ValidationIssue("CRITICAL",f"TP{i}_DIRECTION",f"TP{i} must be above entry for LONG."))
        elif p.side=="SHORT" and tp>=p.entry: issues.append(ValidationIssue("CRITICAL",f"TP{i}_DIRECTION",f"TP{i} must be below entry for SHORT."))
    if len(p.tps)!=len(p.tp_allocations): issues.append(ValidationIssue("CRITICAL","TP_ALLOC_LENGTH","TP allocations do not match TP count."))
    elif abs(sum(p.tp_allocations)-100)>0.01: issues.append(ValidationIssue("CRITICAL","TP_ALLOC_SUM","TP allocations must sum to 100%."))
    if p.risk_pct<=0 or p.risk_pct>100: issues.append(ValidationIssue("CRITICAL","RISK_RANGE","Risk % must be > 0 and <= 100."))
    if p.leverage<1: issues.append(ValidationIssue("CRITICAL","LEVERAGE_RANGE","Leverage must be at least 1x."))
    return issues

def liquidation_estimate(entry: float, side: str, leverage: float, maintenance_margin_rate: float=.005) -> Optional[float]:
    if not all(finite(v) and v>0 for v in [entry, leverage]): return None
    # Indicative isolated linear estimate only. Real exchange liquidation depends on tier, fees, cross collateral, etc.
    if side=="LONG": return max(0.0, entry*(1 - 1/leverage + maintenance_margin_rate))
    return entry*(1 + 1/leverage - maintenance_margin_rate)

def calculate_trade(p: TradePlan, quantity_precision_fn=None, contract_size: float=1.0) -> TradeCalc:
    issues=validate_plan_sanity(p)
    if any(i.severity=="CRITICAL" for i in issues): raise ValueError("; ".join(i.message for i in issues))
    risk_budget=p.capital*p.risk_pct/100
    stop_distance=abs(p.entry-p.stop); stop_pct=stop_distance/p.entry*100
    # Worst-planned-loss sizing includes stop loss, assumed taker exit fee, entry fee and two-sided slippage budget.
    entry_fee=p.taker_fee_pct/100
    exit_fee=p.taker_fee_pct/100
    slip=p.slippage_pct/100
    funding=abs(p.expected_funding_pct)/100
    per_unit=stop_distance + p.entry*(entry_fee+exit_fee+2*slip+funding)
    if per_unit<=0: raise ValueError("Per-unit risk is zero or invalid")
    contract_size=safe_float(contract_size,1.0)
    if contract_size<=0: contract_size=1.0
    base_qty=risk_budget/per_unit
    order_amount=base_qty/contract_size
    if quantity_precision_fn: order_amount=max(0,float(quantity_precision_fn(order_amount)))
    qty=order_amount*contract_size
    notional=qty*p.entry; margin=notional/p.leverage
    fees=notional*(entry_fee+exit_fee); slippage=notional*(2*slip); funding_cost=notional*funding
    planned_loss=qty*stop_distance; worst=planned_loss+fees+slippage+funding_cost
    tp_rows=[]; gross=0.0; weighted_r=0.0
    for i,(tp,alloc) in enumerate(zip(p.tps,p.tp_allocations),1):
        q=qty*alloc/100
        price_move=(tp-p.entry) if p.side=="LONG" else (p.entry-tp)
        pnl=q*price_move; r=price_move/stop_distance
        gross += pnl; weighted_r += r*alloc/100
        tp_rows.append({"TP":f"TP{i}","Price":tp,"Allocation %":alloc,"Quantity":q,"R":r,"Gross PnL":pnl})
    est_exit_notional=sum(row["Quantity"]*row["Price"] for row in tp_rows)
    net=gross - notional*entry_fee - est_exit_notional*exit_fee - (notional+est_exit_notional)*slip - funding_cost
    side_sign=1 if p.side=="LONG" else -1
    breakeven=p.entry*(1+side_sign*(entry_fee+exit_fee+2*slip+funding))
    liq=liquidation_estimate(p.entry,p.side,p.leverage)
    liq_dist=abs(liq-p.entry)/p.entry*100 if finite(liq) else None
    min_lev=max(1.0,notional/max(p.capital,1e-9))
    # Conservative heuristic, not a promise: keep estimated liquidation at least 2x stop distance away where possible.
    safe_hi=max(1.0,min(20.0,0.5/(stop_distance/p.entry + .005)))
    return TradeCalc(risk_budget,stop_distance,stop_pct,per_unit,qty,order_amount,contract_size,notional,margin,notional/p.capital if p.capital else np.nan,
                     planned_loss,fees,slippage,funding_cost,worst,weighted_r,gross,net,breakeven,liq,liq_dist,min_lev,safe_hi,tp_rows)

def stop_engine(p: TradePlan, calc: TradeCalc, df: pd.DataFrame, structure: Dict[str,Any], levels: pd.DataFrame) -> List[Dict[str,Any]]:
    if df.empty: return []
    price=p.entry; atr=safe_float(df.atr.iloc[-1],price*.01)
    candidates=[]
    candidates.append(("Manual",p.stop,"USER"))
    if p.side=="LONG":
        lows=levels[levels.level<price] if not levels.empty else pd.DataFrame()
        struct=float(lows.sort_values("level",ascending=False).iloc[0].level)-.15*atr if len(lows) else price-1.5*atr
        candidates += [("Structure",struct,"STRUCTURE"),("ATR 1.5x",price-1.5*atr,"VOLATILITY"),("ATR 2x",price-2*atr,"VOLATILITY")]
    else:
        highs=levels[levels.level>price] if not levels.empty else pd.DataFrame()
        struct=float(highs.sort_values("level").iloc[0].level)+.15*atr if len(highs) else price+1.5*atr
        candidates += [("Structure",struct,"STRUCTURE"),("ATR 1.5x",price+1.5*atr,"VOLATILITY"),("ATR 2x",price+2*atr,"VOLATILITY")]
    out=[]
    for name,stop,source in candidates:
        dist=abs(price-stop); d_atr=dist/atr if atr else np.nan; warning="OK"
        if d_atr<.6: warning="STOP INSIDE NORMAL NOISE"
        elif d_atr<.9: warning="STOP TIGHT"
        elif d_atr>3.5: warning="STOP VERY WIDE"
        if not levels.empty and (levels.level-stop).abs().min()<.12*atr: warning += " / NEAR OBVIOUS LEVEL"
        out.append({"Method":name,"Stop":stop,"Distance %":dist/price*100,"ATR multiples":d_atr,"Assessment":warning,"Source":source})
    return out

def risk_gate(p: TradePlan, calc: TradeCalc, limits: RiskLimits, market_meta: Dict[str,Any], market_ctx: Dict[str,Any], account_ctx: Dict[str,Any]) -> List[ValidationIssue]:
    issues=validate_plan_sanity(p)
    if p.risk_pct>limits.max_risk_trade_pct: issues.append(ValidationIssue("CRITICAL","RISK_LIMIT",f"Risk {p.risk_pct:.2f}% exceeds max {limits.max_risk_trade_pct:.2f}%."))
    if p.leverage>limits.max_leverage: issues.append(ValidationIssue("CRITICAL","LEVERAGE_LIMIT",f"Leverage {p.leverage:.1f}x exceeds max {limits.max_leverage:.1f}x."))
    if calc.rr_weighted<limits.min_rr: issues.append(ValidationIssue("WARNING","RR_LOW",f"Weighted R:R {calc.rr_weighted:.2f}R is below policy {limits.min_rr:.2f}R."))
    if calc.margin>p.capital: issues.append(ValidationIssue("CRITICAL","MARGIN","Required margin exceeds capital."))
    min_qty=safe_float(market_meta.get("minQty")); max_qty=safe_float(market_meta.get("maxQty")); min_not=safe_float(market_meta.get("minNotional")); max_lev=safe_float(market_meta.get("maxLeverage"))
    if market_meta.get("data_source") == "BINANCE_VISION_SPOT_PUBLIC_PROXY":
        issues.append(ValidationIssue("INFO","FUTURES_SPEC_REVALIDATION","Binance public analysis uses Binance Vision Spot market data. Actual futures tick/step/min-notional/leverage are revalidated before any LIVE order."))
    if market_meta.get("inverse") is True or market_meta.get("linear") is False: issues.append(ValidationIssue("CRITICAL","INVERSE_CONTRACT","Execution sizing is intentionally blocked for inverse contracts; use a linear USDT/USDC contract so PnL and risk units remain unambiguous."))
    if finite(min_qty) and calc.order_amount<min_qty: issues.append(ValidationIssue("CRITICAL","MIN_QTY",f"Order amount below exchange minimum {min_qty}."))
    if finite(max_qty) and calc.order_amount>max_qty: issues.append(ValidationIssue("CRITICAL","MAX_QTY",f"Order amount exceeds exchange maximum {max_qty}."))
    if finite(min_not) and calc.notional<min_not: issues.append(ValidationIssue("CRITICAL","MIN_NOTIONAL",f"Notional below exchange minimum {min_not}."))
    if finite(max_lev) and p.leverage>max_lev: issues.append(ValidationIssue("CRITICAL","EXCHANGE_LEVERAGE",f"Leverage exceeds exchange market limit {max_lev}x."))
    vr=market_ctx.get("volatility",{}).get("regime")
    if vr=="EXTREME": issues.append(ValidationIssue("WARNING","EXTREME_VOL","Volatility regime is EXTREME; slippage and stop overshoot risk are elevated."))
    dc=safe_float(market_ctx.get("data_confidence"),0)
    if dc<45: issues.append(ValidationIssue("CRITICAL","DATA_CONFIDENCE","Data confidence is too low for critical execution decisions."))
    elif dc<70: issues.append(ValidationIssue("WARNING","DATA_CONFIDENCE","Data confidence is degraded."))
    spread=safe_float(market_ctx.get("spread_pct"))
    if finite(spread) and spread>.15: issues.append(ValidationIssue("WARNING","SPREAD","Spread is elevated."))
    if calc.liquidation_estimate and ((p.side=="LONG" and calc.liquidation_estimate>=p.stop) or (p.side=="SHORT" and calc.liquidation_estimate<=p.stop)):
        issues.append(ValidationIssue("CRITICAL","LIQUIDATION_BEFORE_STOP","Indicative liquidation lies before/inside the stop path."))
    elif calc.liquidation_estimate and abs(calc.liquidation_estimate-p.stop) < calc.stop_distance*0.5:
        issues.append(ValidationIssue("WARNING","LIQUIDATION_BUFFER","Indicative liquidation is close to the planned stop; gap/slippage could erase the intended protection buffer."))
    daily_loss=safe_float(account_ctx.get("daily_loss_pct"),0)
    if daily_loss<=-limits.max_daily_loss_pct: issues.append(ValidationIssue("CRITICAL","DAILY_STOP","Daily risk limit reached."))
    if safe_float(account_ctx.get("weekly_loss_pct"),0)<=-limits.max_weekly_loss_pct: issues.append(ValidationIssue("CRITICAL","WEEKLY_STOP","Weekly loss limit reached."))
    if safe_float(account_ctx.get("monthly_loss_pct"),0)<=-limits.max_monthly_loss_pct: issues.append(ValidationIssue("CRITICAL","MONTHLY_STOP","Monthly loss limit reached."))
    if safe_float(account_ctx.get("gross_exposure_pct"),0)+calc.notional/max(p.capital,1e-9)*100>limits.max_portfolio_exposure_pct: issues.append(ValidationIssue("CRITICAL","EXPOSURE_LIMIT","Planned notional would exceed portfolio exposure policy."))
    if safe_float(account_ctx.get("margin_usage_pct"),0)+calc.margin/max(p.capital,1e-9)*100>limits.max_margin_usage_pct: issues.append(ValidationIssue("CRITICAL","MARGIN_USAGE","Planned margin would exceed margin-usage policy."))
    if int(account_ctx.get("concurrent_trades",0))+1>limits.max_concurrent_trades: issues.append(ValidationIssue("CRITICAL","CONCURRENT_TRADES","Maximum concurrent-trade count would be exceeded."))
    ext=safe_float(market_ctx.get("extension_atr"),0)
    if ext>1.5: issues.append(ValidationIssue("WARNING","LATE_ENTRY","Price is extended >1.5 ATR from EMA20 in the trade direction; chasing risk is elevated."))
    dd=safe_float(account_ctx.get("drawdown_pct"),0)
    if dd>=limits.max_drawdown_pct: issues.append(ValidationIssue("CRITICAL","MAX_DD","Maximum drawdown limit reached."))
    open_risk=safe_float(account_ctx.get("open_risk_pct"),0)
    if open_risk+p.risk_pct>limits.max_open_risk_pct: issues.append(ValidationIssue("CRITICAL","OPEN_RISK","Open risk would exceed portfolio limit."))
    if st.session_state.get("kill_switch"): issues.append(ValidationIssue("CRITICAL","KILL_SWITCH","Kill switch is active; new orders are blocked."))
    return issues

def gate_status(issues: List[ValidationIssue]) -> str:
    if any(i.severity=="CRITICAL" for i in issues): return "TRADE REJECTED"
    if any(i.severity in {"WARNING","DANGER"} for i in issues): return "TRADE CONDITIONAL"
    return "TRADE APPROVED"

# ============================================================
# LIVE EXECUTION ENGINE
# ============================================================
def live_enabled_by_server() -> bool:
    return truthy(get_secret("ENABLE_LIVE_TRADING", False))

def credential_status(exchange_id: str) -> Tuple[bool,str]:
    prefix=exchange_id.upper().replace("BINANCEUSDM","BINANCE")
    k=get_secret(f"{prefix}_API_KEY"); s=get_secret(f"{prefix}_API_SECRET")
    if not k or not s: return False,"API key/secret not configured"
    if exchange_id=="okx" and not (get_secret("OKX_API_PASSWORD") or get_secret("OKX_PASSPHRASE")): return False,"OKX passphrase missing"
    return True,"Credentials present"

def private_account_snapshot(exchange_id: str, symbol: str) -> Dict[str,Any]:
    t0=time.perf_counter(); ad=ExchangeAdapter(exchange_id,private=True,sandbox=truthy(get_secret("USE_EXCHANGE_SANDBOX",False)))
    try:
        bal=ad.fetch_balance(); positions=ad.fetch_positions([symbol])
        usdt=(bal.get("USDT") or {}) if isinstance(bal,dict) else {}
        snap={"ok":True,"free":safe_float(usdt.get("free")),"total":safe_float(usdt.get("total")),"positions":positions,"latency_ms":(time.perf_counter()-t0)*1000,"timestamp":iso_now()}
        return snap
    finally: ad.close()

def live_capabilities(exchange_id: str, symbol: str) -> Dict[str,Any]:
    ad=ExchangeAdapter(exchange_id,private=False)
    try:
        ex=ad.ex
        def fv(feature):
            try: return ex.feature_value(symbol,"createOrder",feature)
            except Exception: return None
        return {"stopLoss":fv("stopLoss"),"takeProfit":fv("takeProfit"),"stopLossPrice":fv("stopLossPrice"),"takeProfitPrice":fv("takeProfitPrice"),"reduceOnly":fv("reduceOnly")}
    finally: ad.close()

def execute_live_entry(p: TradePlan, calc: TradeCalc) -> Dict[str,Any]:
    if not live_enabled_by_server(): raise RuntimeError("ENABLE_LIVE_TRADING is not true in server secrets/environment")
    if st.session_state.get("kill_switch"): raise RuntimeError("Kill switch is active")
    ad=ExchangeAdapter(p.exchange,private=True,sandbox=truthy(get_secret("USE_EXCHANGE_SANDBOX",False)))
    try:
        ad.set_leverage(int(round(p.leverage)),p.symbol,"isolated")
        amount=ad.amount_to_precision(p.symbol,calc.order_amount); price=ad.price_to_precision(p.symbol,p.entry)
        if amount<=0: raise RuntimeError("Rounded amount is zero")
        side="buy" if p.side=="LONG" else "sell"; close_side="sell" if side=="buy" else "buy"
        params={"reduceOnly":False,"clientOrderId":f"fcc-{uuid.uuid4().hex[:20]}"}
        try:
            stop_cap=ad.ex.feature_value(p.symbol,"createOrder","stopLoss")
        except Exception:
            stop_cap=None
        # Capital-protection rule: live entry requires an atomic attached stop declared by CCXT.
        if not stop_cap:
            raise RuntimeError("This exchange/symbol does not declare unified attached stop-loss support via CCXT. Live entry is blocked to avoid an unprotected position.")
        params["stopLoss"]={"triggerPrice":ad.price_to_precision(p.symbol,p.stop)}
        order_type=p.order_type.lower(); order_price=None if order_type=="market" else price
        order=ad.create_order(p.symbol,order_type,side,amount,order_price,params)
        protection={"attached_stop":True,"tp_orders":[],"tp_errors":[]}
        # For MARKET entries only, build the requested reduce-only TP ladder after the protected entry call.
        # A failure to place a TP does not remove the already-attached stop; it is surfaced explicitly.
        if order_type=="market":
            for i,(tp,alloc) in enumerate(zip(p.tps,p.tp_allocations),1):
                q=ad.amount_to_precision(p.symbol,calc.order_amount*alloc/100)
                if q<=0: continue
                try:
                    tp_order=ad.create_order(p.symbol,"limit",close_side,q,ad.price_to_precision(p.symbol,tp),{"reduceOnly":True,"clientOrderId":f"fcc-tp{i}-{uuid.uuid4().hex[:12]}"})
                    protection["tp_orders"].append({"tp":i,"id":tp_order.get("id"),"price":tp,"qty":q})
                except Exception as e:
                    protection["tp_errors"].append({"tp":i,"error":f"{type(e).__name__}: {e}"})
        else:
            protection["tp_errors"].append({"tp":"ladder","error":"LIMIT entry: TP ladder is not pre-submitted to avoid reduce-only race conditions before fill. Attached stop remains mandatory; add TPs after fill confirmation."})
        audit("LIVE_ORDER_SUBMITTED",{"exchange":p.exchange,"symbol":p.symbol,"side":p.side,"order_id":order.get("id"),"qty":amount,"stop":p.stop,"tp_count":len(protection["tp_orders"])},"WARNING")
        return {"entry_order":order,"protection":protection}
    finally: ad.close()

def cancel_pending_live(exchange_id: str, symbol: Optional[str]) -> Any:
    ad=ExchangeAdapter(exchange_id,private=True,sandbox=truthy(get_secret("USE_EXCHANGE_SANDBOX",False)))
    try:
        res=ad.cancel_all_orders(symbol); audit("LIVE_CANCEL_ALL",{"exchange":exchange_id,"symbol":symbol},"WARNING"); return res
    finally: ad.close()

# ============================================================
# PAPER TRADING ENGINE
# ============================================================
def create_paper_position(p: TradePlan, calc: TradeCalc, market_price: float) -> str:
    slip=p.slippage_pct/100
    fill=market_price*(1+slip if p.side=="LONG" else 1-slip) if p.order_type=="MARKET" else p.entry
    pid=uuid.uuid4().hex
    entry_fee=fill*calc.quantity*(p.taker_fee_pct/100 if p.order_type=="MARKET" else p.maker_fee_pct/100)
    with db_connect() as con:
        con.execute("INSERT INTO paper_positions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pid,iso_now(),p.exchange,p.symbol,p.side,fill,calc.quantity,calc.quantity,p.leverage,p.stop,json.dumps(p.tps),json.dumps(p.tp_allocations),entry_fee,0.0,0.0,0.0,0.0,"OPEN",json.dumps({"plan":asdict(p)},default=str)))
    audit("PAPER_POSITION_OPENED",{"position_id":pid,"symbol":p.symbol,"side":p.side,"entry":fill,"qty":calc.quantity})
    return pid

def process_paper_positions(exchange_id: str, symbol: Optional[str]=None) -> List[str]:
    dfp=read_table("paper_positions")
    if dfp.empty: return []
    dfp=dfp[(dfp.status=="OPEN") & (dfp.exchange==exchange_id)]
    if symbol: dfp=dfp[dfp.symbol==symbol]
    events=[]
    for _,pos in dfp.iterrows():
        try:
            candles=cached_ohlcv(exchange_id,pos.symbol,"1m",3)
            if candles.empty: continue
            c=candles.iloc[-1]; high=float(c.high); low=float(c.low); mark=float(c.close); entry=float(pos.entry); side=pos.side
            remaining=float(pos.remaining_qty); realized=float(pos.realized_pnl); fees=float(pos.fees); mfe=float(pos.mfe); mae=float(pos.mae)
            favorable=(high-entry) if side=="LONG" else (entry-low); adverse=(entry-low) if side=="LONG" else (high-entry)
            mfe=max(mfe,favorable); mae=max(mae,adverse)
            tps=json.loads(pos.tps_json); alloc=json.loads(pos.alloc_json); meta=json.loads(pos.meta_json or "{}")
            hit_indices=set(meta.get("hit_tps",[])); stop=float(pos.stop)
            # Approximate paper funding accrual using the currently reported rate and an 8h normalization.
            # It is explicitly an estimate because exchanges may use different funding intervals and rates can change.
            funding_total=float(pos.funding); last_accrual=pd.to_datetime(meta.get("last_funding_accrual",pos.opened_at),utc=True,errors="coerce")
            now_ts=pd.Timestamp.now(tz="UTC")
            if pd.notna(last_accrual):
                hours=max(0.0,(now_ts-last_accrual).total_seconds()/3600)
                if hours>0.01 and remaining>0:
                    try:
                        fr=(cached_derivatives(exchange_id,pos.symbol).get("funding") or {}).get("fundingRate")
                        rate=safe_float(fr,0.0); notional=abs(mark*remaining); direction=1 if side=="LONG" else -1
                        funding_total += notional*rate*(hours/8.0)*direction
                        meta["last_funding_accrual"]=now_ts.isoformat()
                    except Exception:
                        pass
            # Conservative same-candle assumption: stop is processed before TP if both were touched.
            stop_hit=(side=="LONG" and low<=stop) or (side=="SHORT" and high>=stop)
            status="OPEN"
            if stop_hit and remaining>0:
                pnl=(stop-entry)*remaining if side=="LONG" else (entry-stop)*remaining
                realized+=pnl; fees+=abs(stop*remaining)*0.0005; remaining=0; status="CLOSED"; events.append(f"{pos.symbol}: STOP hit")
            else:
                for i,tp in enumerate(tps):
                    if i in hit_indices: continue
                    hit=(side=="LONG" and high>=tp) or (side=="SHORT" and low<=tp)
                    if hit and remaining>0:
                        target_qty=float(pos.qty)*float(alloc[i])/100; q=min(remaining,target_qty)
                        pnl=(tp-entry)*q if side=="LONG" else (entry-tp)*q
                        realized+=pnl; fees+=abs(tp*q)*0.0004; remaining-=q; hit_indices.add(i); events.append(f"{pos.symbol}: TP{i+1} hit")
                if remaining<=max(float(pos.qty)*1e-8,1e-12): status="CLOSED"
            meta["hit_tps"]=sorted(hit_indices); meta["mark"]=mark
            with db_connect() as con:
                con.execute("UPDATE paper_positions SET remaining_qty=?, realized_pnl=?, fees=?, funding=?, mfe=?, mae=?, status=?, meta_json=? WHERE id=?",(remaining,realized,fees,funding_total,mfe,mae,status,json.dumps(meta),pos.id))
            if status=="CLOSED":
                risk_per_unit=abs(entry-stop); risk_usdt=risk_per_unit*float(pos.qty); pnl_net=realized-fees-funding_total
                with db_connect() as con:
                    con.execute("INSERT OR REPLACE INTO journal(id,opened_at,closed_at,exchange,symbol,side,setup,entry,stop,tps_json,risk_pct,risk_usdt,quantity,leverage,market_regime,long_score,short_score,data_confidence,reason,outcome,pnl,pnl_net,r_result,mfe,mae,duration_min,fees,funding,emotion_json,discipline_json,screenshot,notes,mistake,lesson,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (pos.id,pos.opened_at,iso_now(),pos.exchange,pos.symbol,pos.side,(meta.get("plan") or {}).get("setup","Paper"),entry,stop,pos.tps_json,(meta.get("plan") or {}).get("risk_pct"),risk_usdt,pos.qty,pos.leverage,"",None,None,None,"paper simulation","WIN" if pnl_net>0 else "LOSS",realized,pnl_net,pnl_net/risk_usdt if risk_usdt else None,mfe,mae,None,fees,funding_total,"{}","{}","","","","","paper"))
        except Exception as e:
            events.append(f"{pos.symbol}: paper processing error {type(e).__name__}")
    return events

# ============================================================
# PORTFOLIO / ANALYTICS
# ============================================================
def portfolio_risk_from_positions(positions: List[Dict[str,Any]], equity: float) -> Dict[str,Any]:
    rows=[]; long_exp=short_exp=margin=0.0
    for p in positions:
        contracts=safe_float(p.get("contracts"),0); mark=safe_float(p.get("markPrice"),safe_float(p.get("entryPrice"),0)); side=str(p.get("side","")).lower(); notional=abs(safe_float(p.get("notional"),contracts*mark)); lev=safe_float(p.get("leverage"),1)
        if notional<=0 or contracts==0: continue
        if side=="long": long_exp+=notional
        elif side=="short": short_exp+=notional
        margin+=safe_float(p.get("initialMargin"),notional/max(lev,1))
        rows.append({"symbol":p.get("symbol"),"side":side.upper(),"notional":notional,"leverage":lev,"entry":p.get("entryPrice"),"mark":p.get("markPrice"),"unrealizedPnl":p.get("unrealizedPnl"),"liquidationPrice":p.get("liquidationPrice")})
    total=long_exp+short_exp
    return {"rows":rows,"long_exposure":long_exp,"short_exposure":short_exp,"net_exposure":long_exp-short_exp,"gross_exposure":total,"portfolio_leverage":total/equity if equity else np.nan,"margin_usage_pct":margin/equity*100 if equity else np.nan}

def correlation_matrix(exchange_id: str, symbols: List[str], timeframe: str="1h", limit: int=200) -> pd.DataFrame:
    series={}
    for sym in symbols[:12]:
        try:
            d=cached_ohlcv(exchange_id,sym,timeframe,limit)
            if not d.empty: series[sym]=d.close.pct_change()
        except Exception: pass
    return pd.DataFrame(series).dropna(how="all").corr() if series else pd.DataFrame()

def journal_metrics(j: pd.DataFrame) -> Dict[str,Any]:
    if j.empty: return {"trades":0}
    x=j.copy(); x["pnl_net"]=pd.to_numeric(x.pnl_net,errors="coerce").fillna(0); x["r_result"]=pd.to_numeric(x.r_result,errors="coerce")
    wins=x[x.pnl_net>0]; losses=x[x.pnl_net<0]; n=len(x); wr=len(wins)/n if n else 0
    avgw=float(wins.pnl_net.mean()) if len(wins) else 0; avgl=abs(float(losses.pnl_net.mean())) if len(losses) else 0
    gross_win=float(wins.pnl_net.sum()); gross_loss=abs(float(losses.pnl_net.sum())); pf=gross_win/gross_loss if gross_loss else np.inf if gross_win>0 else np.nan
    expectancy=wr*avgw-(1-wr)*avgl
    eq=x.sort_values("closed_at").pnl_net.cumsum(); peak=eq.cummax(); dd=eq-peak; maxdd=float(dd.min()) if len(dd) else 0
    r=x.r_result.dropna(); sharpe=(r.mean()/r.std(ddof=1)*np.sqrt(len(r))) if len(r)>2 and r.std(ddof=1)>0 else np.nan
    downside=r[r<0]; sortino=(r.mean()/downside.std(ddof=1)*np.sqrt(len(r))) if len(downside)>1 and downside.std(ddof=1)>0 else np.nan
    return {"trades":n,"win_rate":wr*100,"avg_winner":avgw,"avg_loser":avgl,"profit_factor":pf,"expectancy":expectancy,"net_pnl":float(x.pnl_net.sum()),"max_dd":maxdd,"sharpe":sharpe,"sortino":sortino,"avg_r":float(r.mean()) if len(r) else np.nan}

def equity_drawdown_curve(j: pd.DataFrame, starting_balance: float) -> pd.DataFrame:
    if j.empty: return pd.DataFrame(columns=["time","equity","peak","drawdown_pct"])
    x=j.dropna(subset=["closed_at"]).copy(); x["closed_at"]=pd.to_datetime(x.closed_at,utc=True,errors="coerce"); x["pnl_net"]=pd.to_numeric(x.pnl_net,errors="coerce").fillna(0); x=x.sort_values("closed_at")
    x["equity"]=starting_balance+x.pnl_net.cumsum(); x["peak"]=x.equity.cummax(); x["drawdown_pct"]=(x.equity/x.peak-1)*100
    return x[["closed_at","equity","peak","drawdown_pct"]].rename(columns={"closed_at":"time"})

def risk_of_ruin_estimate(win_rate: float, avg_win_r: float, avg_loss_r: float, risk_pct: float) -> Dict[str,Any]:
    if not (0<win_rate<1) or avg_win_r<=0 or avg_loss_r<=0 or risk_pct<=0: return {"status":"INSUFFICIENT DATA"}
    expectancy=win_rate*avg_win_r-(1-win_rate)*avg_loss_r
    # Heuristic approximation, intentionally labelled; exact ruin depends on sizing path and ruin boundary.
    edge=max(-.99,min(.99,expectancy/(avg_win_r+avg_loss_r)))
    if edge<=0: ruin=1.0
    else:
        units=max(1,100/risk_pct); ruin=((1-edge)/(1+edge))**units
    return {"status":"HEURISTIC ESTIMATE","expectancy_r":expectancy,"risk_of_ruin":clamp(ruin,0,1)*100}

# ============================================================
# BACKTEST / MONTE CARLO
# ============================================================
def strategy_signals(df: pd.DataFrame, strategy: str) -> pd.Series:
    x=add_indicators(df); sig=pd.Series(0,index=x.index,dtype=int)
    if strategy=="Trend Pullback":
        long=(x.close>x.ema50)&(x.ema20>x.ema50)&(x.low<=x.ema20*1.003)&(x.rsi.between(45,65))
        short=(x.close<x.ema50)&(x.ema20<x.ema50)&(x.high>=x.ema20*.997)&(x.rsi.between(35,55))
    elif strategy=="Breakout Retest":
        prevh=x.high.rolling(20).max().shift(1); prevl=x.low.rolling(20).min().shift(1)
        long=(x.close>prevh)&(x.rvol>1.1); short=(x.close<prevl)&(x.rvol>1.1)
    elif strategy=="Range Reversal":
        long=(x.close<=x.bb_lower)&(x.rsi<35)&(x.adx<25); short=(x.close>=x.bb_upper)&(x.rsi>65)&(x.adx<25)
    else: # Momentum Continuation
        long=(x.ema20>x.ema50)&(x.adx>25)&(x.macd_hist>0)&(x.rvol>1); short=(x.ema20<x.ema50)&(x.adx>25)&(x.macd_hist<0)&(x.rvol>1)
    sig[long.fillna(False)]=1; sig[short.fillna(False)]=-1
    return sig

def run_backtest(df: pd.DataFrame, strategy: str, risk_pct: float, stop_atr: float, rr: float, fee_pct: float, slippage_pct: float, starting_balance: float=10000.0) -> Tuple[pd.DataFrame,pd.DataFrame,Dict[str,Any]]:
    x=add_indicators(df).dropna(subset=["atr"]).copy(); sig=strategy_signals(x,strategy); balance=starting_balance; trades=[]; i=1
    while i < len(x)-2:
        s=int(sig.iloc[i])
        if s==0: i+=1; continue
        entry=float(x.open.iloc[i+1]); atr=float(x.atr.iloc[i]); stop=entry-s*stop_atr*atr; risk_dist=abs(entry-stop)
        if risk_dist<=0: i+=1; continue
        risk_budget=balance*risk_pct/100; qty=risk_budget/(risk_dist+entry*(2*fee_pct/100+2*slippage_pct/100)); target=entry+s*rr*risk_dist; exit_price=None; reason=None; mfe=mae=0.0; j=i+1
        for j in range(i+1,len(x)):
            hi=float(x.high.iloc[j]); lo=float(x.low.iloc[j]); mfe=max(mfe,(hi-entry) if s==1 else (entry-lo)); mae=max(mae,(entry-lo) if s==1 else (hi-entry))
            stop_hit=(s==1 and lo<=stop) or (s==-1 and hi>=stop); tp_hit=(s==1 and hi>=target) or (s==-1 and lo<=target)
            if stop_hit: exit_price=stop; reason="SL"; break # conservative intrabar
            if tp_hit: exit_price=target; reason="TP"; break
        if exit_price is None: exit_price=float(x.close.iloc[-1]); reason="EOD"; j=len(x)-1
        gross=(exit_price-entry)*qty*s; fees=(entry+exit_price)*qty*fee_pct/100; slip=(entry+exit_price)*qty*slippage_pct/100; net=gross-fees-slip; rres=net/risk_budget if risk_budget else 0; balance+=net
        trades.append({"entry_time":x.index[i+1],"exit_time":x.index[j],"side":"LONG" if s==1 else "SHORT","entry":entry,"stop":stop,"target":target,"exit":exit_price,"qty":qty,"gross":gross,"fees":fees,"slippage":slip,"pnl_net":net,"R":rres,"reason":reason,"MFE":mfe,"MAE":mae,"balance":balance})
        i=j+1
    t=pd.DataFrame(trades)
    if t.empty: return t,pd.DataFrame(),{"trades":0}
    eq=t[["exit_time","balance"]].copy(); eq["peak"]=eq.balance.cummax(); eq["drawdown_pct"]=(eq.balance/eq.peak-1)*100
    wins=t[t.pnl_net>0]; losses=t[t.pnl_net<0]; pf=wins.pnl_net.sum()/abs(losses.pnl_net.sum()) if len(losses) and abs(losses.pnl_net.sum())>0 else np.inf
    r=t.R; metrics={"trades":len(t),"win_rate":(t.pnl_net>0).mean()*100,"net_pnl":t.pnl_net.sum(),"return_pct":(balance/starting_balance-1)*100,"profit_factor":pf,"avg_r":r.mean(),"max_dd_pct":eq.drawdown_pct.min(),"sharpe":r.mean()/r.std(ddof=1)*np.sqrt(len(r)) if len(r)>2 and r.std(ddof=1)>0 else np.nan,"sortino":r.mean()/r[r<0].std(ddof=1)*np.sqrt(len(r)) if len(r[r<0])>1 and r[r<0].std(ddof=1)>0 else np.nan}
    return t,eq,metrics

def monte_carlo(r_values: Iterable[float], n_sims: int=2000, n_trades: Optional[int]=None, starting_equity: float=100.0, risk_pct: float=1.0, seed: int=42) -> Tuple[pd.DataFrame,Dict[str,Any]]:
    r=np.array([x for x in r_values if finite(x)],dtype=float)
    if len(r)<3: return pd.DataFrame(),{"status":"INSUFFICIENT DATA"}
    n_trades=n_trades or len(r); rng=np.random.default_rng(seed); finals=[]; dds=[]
    for _ in range(n_sims):
        seq=rng.choice(r,size=n_trades,replace=True); eq=starting_equity; peak=eq; maxdd=0
        for rv in seq:
            eq*=max(.0001,1+rv*risk_pct/100); peak=max(peak,eq); maxdd=min(maxdd,eq/peak-1)
        finals.append(eq); dds.append(maxdd*100)
    out=pd.DataFrame({"final_equity":finals,"max_drawdown_pct":dds})
    stats={"status":"BOOTSTRAP ESTIMATE","median_final":float(out.final_equity.median()),"p05_final":float(out.final_equity.quantile(.05)),"p95_final":float(out.final_equity.quantile(.95)),"median_dd":float(out.max_drawdown_pct.median()),"p05_dd":float(out.max_drawdown_pct.quantile(.05))}
    return out,stats

def market_session_label(now: Optional[datetime]=None) -> str:
    now=now or utc_now(); h=now.hour
    sessions=[]
    if 0 <= h < 9: sessions.append("ASIA")
    if 7 <= h < 16: sessions.append("LONDON")
    if 13 <= h < 22: sessions.append("NEW YORK")
    return " + ".join(sessions) if sessions else "OFF-PEAK"

# ============================================================
# SCANNER / MARKET SNAPSHOT
# ============================================================
def ticker_change_from_ohlcv(df: pd.DataFrame, bars_back: int) -> float:
    if df.empty or len(df)<=bars_back: return np.nan
    return pct_change(float(df.close.iloc[-1]),float(df.close.iloc[-1-bars_back]))

def estimate_orderbook_slippage(orderbook: Dict[str,Any], side: str, quote_notional: float) -> Dict[str,Any]:
    levels=(orderbook.get("asks") if side.upper()=="LONG" else orderbook.get("bids")) or []
    if not levels or quote_notional<=0: return {"status":"UNAVAILABLE","slippage_pct":np.nan,"filled_quote":0.0}
    best=float(levels[0][0]); remaining=quote_notional; base=0.0; quote=0.0
    for price,amount,*_ in levels:
        price=float(price); amount=float(amount); level_quote=price*amount; take=min(remaining,level_quote)
        if take<=0: continue
        base += take/price; quote += take; remaining -= take
        if remaining<=1e-9: break
    if base<=0: return {"status":"UNAVAILABLE","slippage_pct":np.nan,"filled_quote":quote}
    vwap=quote/base; slip=((vwap/best)-1)*100 if side.upper()=="LONG" else ((best/vwap)-1)*100
    return {"status":"FULL" if remaining<=1e-9 else "PARTIAL_DEPTH","slippage_pct":max(0.0,slip),"vwap":vwap,"best":best,"filled_quote":quote,"unfilled_quote":max(0.0,remaining)}

def market_snapshot(exchange_id: str, symbol: str, timeframe: str="15m") -> Dict[str,Any]:
    started=time.perf_counter(); errors=[]; error_details=[]; ticker={}; ob={}; df=pd.DataFrame(); deriv={}
    try: ticker=cached_ticker(exchange_id,symbol)
    except Exception as e:
        error_details.append(classify_exchange_error(e)); errors.append(safe_exchange_error("ticker",e))
    try: ob=cached_orderbook(exchange_id,symbol,50)
    except Exception as e:
        error_details.append(classify_exchange_error(e)); errors.append(safe_exchange_error("orderbook",e))
    try: df=add_indicators(cached_ohlcv(exchange_id,symbol,timeframe,500))
    except Exception as e:
        error_details.append(classify_exchange_error(e)); errors.append(safe_exchange_error("ohlcv",e))
    try: deriv=derivatives_engine(exchange_id,symbol,df)
    except Exception as e:
        deriv={"status":"UNAVAILABLE","error":safe_exchange_error("derivatives",e)}; error_details.append(classify_exchange_error(e)); errors.append(safe_exchange_error("derivatives",e))
    if df.empty:
        primary_code = next((x.get("code") for x in error_details if x.get("code")=="HOST_REGION_RESTRICTED"), error_details[0].get("code") if error_details else "NO_DATA")
        return {"symbol":symbol,"ticker":ticker,"orderbook":ob,"df":df,"derivatives":deriv,"errors":errors,"error_details":error_details,"error_code":primary_code,"status":"UNAVAILABLE","latency_ms":(time.perf_counter()-started)*1000}
    swings,structure=swing_structure(df); levels=support_resistance(df,swings); liq=liquidity_zones(df,swings); reg=market_regime(df,structure); conf=data_confidence(df,ticker,deriv,ob)
    flow={"status":"UNAVAILABLE","reason":"Load Analysis page to request recent trades/order-flow."}
    confl=confluence_engine(df,structure,deriv,levels,flow,conf); scenarios=scenario_engine(df,levels,confl); vr=volatility_regime(df); ve=volume_engine(df)
    bid=safe_float((ob.get("bids") or [[np.nan]])[0][0]); ask=safe_float((ob.get("asks") or [[np.nan]])[0][0]); mid=(bid+ask)/2 if finite(bid) and finite(ask) else np.nan; spread=ask-bid if finite(ask) and finite(bid) else np.nan; spread_pct=spread/mid*100 if finite(mid) and mid else np.nan
    last=safe_float(ticker.get("last"),float(df.close.iloc[-1]));
    return {"symbol":symbol,"ticker":ticker,"orderbook":ob,"df":df,"derivatives":deriv,"swings":swings,"structure":structure,"levels":levels,"liquidity":liq,"regime":reg,"confidence":conf,"confluence":confl,"scenarios":scenarios,"volatility":vr,"volume":ve,"last":last,"bid":bid,"ask":ask,"spread":spread,"spread_pct":spread_pct,"errors":errors,"status":"OK","latency_ms":(time.perf_counter()-started)*1000,"updated_at":iso_now()}

def scan_market(exchange_id: str, max_symbols: int=15, timeframe: str="1h", min_quote_volume: float=5_000_000) -> pd.DataFrame:
    rows=[]
    if exchange_id == "binanceusdm":
        # Rank from Binance Vision public market data. These are Spot USDT instruments
        # used as a market-analysis proxy; futures-only fields remain real-only.
        tickers = _vision_all_tickers()
        ranked=[]
        for t in tickers:
            raw=str(t.get("symbol") or "")
            if not raw.endswith("USDT") or raw in {"USDCUSDT","FDUSDUSDT","TUSDUSDT","USDPUSDT","DAIUSDT"}:
                continue
            qv=safe_float(t.get("quoteVolume"),0)
            if qv < min_quote_volume:
                continue
            ranked.append((_binance_ccxt_symbol(raw,"USDT"), qv, t))
        ranked=sorted(ranked,key=lambda z:z[1],reverse=True)[:max_symbols]
        for sym,qv,t in ranked:
            try:
                d=add_indicators(_vision_ohlcv(sym,timeframe,220))
                if d.empty: continue
                sw,ss=swing_structure(d); reg=market_regime(d,ss); vr=volatility_regime(d); tr=trend_snapshot(d); r=d.iloc[-1]
                funding=np.nan; oi=np.nan
                try:
                    real=_fapi_direct_current(sym); fr=real.get("funding") or {}; funding=safe_float(fr.get("fundingRate"))*100
                    o=real.get("oi") or {}; oi=safe_float(o.get("openInterestAmount",o.get("openInterestValue")))
                except Exception: pass
                score_long=clamp(50+(30 if tr["trend"]=="UP" else -20 if tr["trend"]=="DOWN" else 0)+(15 if ss["trend"]=="UPTREND" else -12 if ss["trend"]=="DOWNTREND" else 0)+(safe_float(r.rsi,50)-50)*.5+(8 if safe_float(r.rvol,1)>1.2 else 0),0,100)
                score_short=clamp(100-score_long,0,100); avoid=20+(25 if vr["regime"]=="EXTREME" else 0)+(15 if tr["strength"]<25 else 0)
                rows.append({"Symbol":sym,"Last":safe_float(t.get("lastPrice"),r.close),"24h Vol":qv,"Trend":tr["trend"],"Structure":ss["trend"],"ADX":safe_float(r.adx),"RSI":safe_float(r.rsi),"ATR%":safe_float(r.atr_pct),"RVOL":safe_float(r.rvol),"Vol Regime":vr["regime"],"Funding %":funding,"Open Interest":oi,"Long Score":score_long,"Short Score":score_short,"Avoid Score":clamp(avoid,0,100),"Regime":reg.status,"Data Source":"Binance Vision Spot proxy"})
            except Exception as e:
                rows.append({"Symbol":sym,"Error":type(e).__name__})
        return pd.DataFrame(rows)

    ad=ExchangeAdapter(exchange_id)
    try:
        markets=ad.contract_markets(); symbols=[m["symbol"] for m in markets]; tickers={}
        if ad.ex.has.get("fetchTickers"):
            try: tickers=retry_call(ad.ex.fetch_tickers, symbols[:250], retries=2)
            except Exception: tickers={}
        ranked=[]
        for sym in symbols:
            t=tickers.get(sym,{}) if isinstance(tickers,dict) else {}
            qv=safe_float(t.get("quoteVolume"),safe_float(t.get("baseVolume"),0)*safe_float(t.get("last"),0))
            if qv>=min_quote_volume: ranked.append((sym,qv,t))
        if not ranked: ranked=[(s,0,{}) for s in symbols[:max_symbols]]
        ranked=sorted(ranked,key=lambda z:z[1],reverse=True)[:max_symbols]
        for sym,qv,t in ranked:
            try:
                d=add_indicators(ad.fetch_ohlcv(sym,timeframe,220));
                if d.empty: continue
                sw,ss=swing_structure(d); reg=market_regime(d,ss); vr=volatility_regime(d); tr=trend_snapshot(d); r=d.iloc[-1]
                funding=np.nan; oi=np.nan
                try:
                    fr=ad.fetch_funding(sym) or {}; funding=safe_float(fr.get("fundingRate"))*100
                except Exception: pass
                try:
                    o=ad.fetch_open_interest(sym) or {}; oi=safe_float(o.get("openInterestValue",o.get("openInterestAmount")))
                except Exception: pass
                score_long=clamp(50+(30 if tr["trend"]=="UP" else -20 if tr["trend"]=="DOWN" else 0)+(15 if ss["trend"]=="UPTREND" else -12 if ss["trend"]=="DOWNTREND" else 0)+(safe_float(r.rsi,50)-50)*.5+(8 if safe_float(r.rvol,1)>1.2 else 0),0,100)
                score_short=clamp(100-score_long,0,100); avoid=20+(25 if vr["regime"]=="EXTREME" else 0)+(15 if tr["strength"]<25 else 0)
                rows.append({"Symbol":sym,"Last":safe_float(t.get("last"),r.close),"24h Vol":qv,"Trend":tr["trend"],"Structure":ss["trend"],"ADX":safe_float(r.adx),"RSI":safe_float(r.rsi),"ATR%":safe_float(r.atr_pct),"RVOL":safe_float(r.rvol),"Vol Regime":vr["regime"],"Funding %":funding,"Open Interest":oi,"Long Score":score_long,"Short Score":score_short,"Avoid Score":clamp(avoid,0,100),"Regime":reg.status,"Data Source":"CCXT futures"})
            except Exception as e: rows.append({"Symbol":sym,"Error":type(e).__name__})
        return pd.DataFrame(rows)
    finally: ad.close()

# ============================================================
# CHARTS / UI COMPONENTS
# ============================================================
def candlestick_chart(df: pd.DataFrame, title: str, levels: Optional[pd.DataFrame]=None, plan: Optional[TradePlan]=None, liq: Optional[float]=None) -> go.Figure:
    if df.empty: return go.Figure()
    view=df.tail(260)
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.03,row_heights=[.78,.22])
    fig.add_trace(go.Candlestick(x=view.index,open=view.open,high=view.high,low=view.low,close=view.close,name="Price",increasing_line_color="#22c55e",decreasing_line_color="#ef4444"),row=1,col=1)
    for col,name,color in [("ema20","EMA20","#38bdf8"),("ema50","EMA50","#a78bfa"),("vwap","VWAP","#f59e0b")]:
        if col in view: fig.add_trace(go.Scatter(x=view.index,y=view[col],name=name,mode="lines",line=dict(width=1.2,color=color)),row=1,col=1)
    if "bb_upper" in view:
        fig.add_trace(go.Scatter(x=view.index,y=view.bb_upper,name="BB",mode="lines",line=dict(width=.7,color="#64748b"),opacity=.45),row=1,col=1)
        fig.add_trace(go.Scatter(x=view.index,y=view.bb_lower,name="BB low",mode="lines",line=dict(width=.7,color="#64748b"),opacity=.45,showlegend=False),row=1,col=1)
    fig.add_trace(go.Bar(x=view.index,y=view.volume,name="Volume",marker_color="#334155"),row=2,col=1)
    if levels is not None and not levels.empty:
        for _,r in levels.head(8).iterrows(): fig.add_hline(y=float(r.level),line_width=.7,line_dash="dot",line_color="#64748b",opacity=.5,row=1,col=1)
    if plan:
        fig.add_hline(y=plan.entry,line_width=1.5,line_color="#38bdf8",annotation_text="ENTRY",row=1,col=1)
        fig.add_hline(y=plan.stop,line_width=1.8,line_color="#ef4444",annotation_text="STOP",row=1,col=1)
        for i,tp in enumerate(plan.tps,1): fig.add_hline(y=tp,line_width=1.0,line_dash="dash",line_color="#22c55e",annotation_text=f"TP{i}",row=1,col=1)
        if finite(liq): fig.add_hline(y=liq,line_width=1.0,line_dash="dot",line_color="#f97316",annotation_text="LIQ EST",row=1,col=1)
    fig.update_layout(height=650,template="plotly_dark",title=title,margin=dict(l=10,r=10,t=45,b=10),paper_bgcolor="#0a0f17",plot_bgcolor="#0a0f17",xaxis_rangeslider_visible=False,legend=dict(orientation="h",y=1.02,x=0))
    return fig

def gauge_chart(value: float, title: str, inverse: bool=False) -> go.Figure:
    title = tr(title)
    v=clamp(safe_float(value,0),0,100)
    fig=go.Figure(go.Indicator(mode="gauge+number",value=v,title={"text":title,"font":{"size":14}},gauge={"axis":{"range":[0,100]},"bar":{"color":"#38bdf8"},"bgcolor":"#111827","borderwidth":0,"steps":[{"range":[0,35],"color":"#33131a"},{"range":[35,70],"color":"#33270f"},{"range":[70,100],"color":"#12301f"}]}))
    fig.update_layout(height=190,margin=dict(l=18,r=18,t=35,b=5),paper_bgcolor="#0a0f17",font_color="#e5edf8")
    return fig

def render_issues(issues: List[ValidationIssue]):
    if not issues:
        st.success(tr("No validation issues detected by the current rule set."))
        return
    for sev in ["CRITICAL","DANGER","WARNING","INFO"]:
        group=[i for i in issues if i.severity==sev]
        if group:
            txt="\n".join(f"• **{i.code}** — {i.message}" for i in group)
            if sev in {"CRITICAL","DANGER"}: st.error(f"**{sev}**\n\n{txt}")
            elif sev=="WARNING": st.warning(f"**WARNING**\n\n{txt}")
            else: st.info(f"**INFO**\n\n{txt}")

def render_decision(confl: Dict[str,Any], conf: EngineResult):
    long_s=confl.get("long",0); short_s=confl.get("short",0); nt=confl.get("no_trade",100)
    if conf.score<45 or nt>=70: decision=tr("NO TRADE"); cls="bad"
    elif max(long_s,short_s)<60: decision=tr("WAIT"); cls="warn"
    else: decision=tr("LONG BIAS") if long_s>short_s else tr("SHORT BIAS"); cls="good" if abs(long_s-short_s)>10 else "warn"
    st.markdown(f'<div class="pro-card"><div class="pro-title">{tr("DECISION MATRIX")}</div><div class="decision {cls}">{decision}</div><div class="pro-sub">{tr("Signal strength")} {max(long_s,short_s):.0f}/100 · {tr("Data confidence")} {conf.score:.0f}/100 · {tr("No-trade score")} {nt:.0f}/100</div></div>',unsafe_allow_html=True)

def app_header(mode: str, exchange_id: str, symbol: str):
    tone="mode-live" if mode=="LIVE" else "mode-paper" if mode=="PAPER" else "mode-analysis"
    source_badge = "BINANCE VISION · SPOT PROXY" if exchange_id=="binanceusdm" else "CCXT · FUTURES"
    st.markdown(f'<div class="pro-card {tone}"><div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center"><div><div style="font-size:1.45rem;font-weight:900;letter-spacing:.04em">⚡ {APP_NAME}</div><div class="pro-sub">{tr("Capital protection → Risk → Decision quality → Execution → Results")}</div></div><div>{html_badge(tr(mode),"bad" if mode=="LIVE" else "warn" if mode=="PAPER" else "info")}{html_badge(SUPPORTED_EXCHANGES.get(exchange_id,exchange_id),"muted")}{html_badge(source_badge,"info")}{html_badge(symbol,"info")}</div></div></div>',unsafe_allow_html=True)

def account_context_from_journal(capital: float) -> Dict[str,Any]:
    j=read_table("journal"); now=utc_now(); day=week=month=0.0; dd=0.0
    if not j.empty:
        x=j.copy(); x["closed_dt"]=pd.to_datetime(x.closed_at,utc=True,errors="coerce"); x["pnl_net"]=pd.to_numeric(x.pnl_net,errors="coerce").fillna(0)
        day=x[x.closed_dt.dt.date==now.date()].pnl_net.sum() if x.closed_dt.notna().any() else 0
        week=x[x.closed_dt>=now-timedelta(days=7)].pnl_net.sum()
        month=x[x.closed_dt>=now-timedelta(days=30)].pnl_net.sum()
        curve=equity_drawdown_curve(x,capital); dd=abs(float(curve.drawdown_pct.min())) if not curve.empty else 0
    p=read_table("paper_positions"); open_risk=gross=margin=0.0; concurrent=0
    if not p.empty:
        op=p[p.status=="OPEN"]; concurrent=len(op)
        if len(op):
            open_risk=sum(abs(float(r.entry)-float(r.stop))*float(r.remaining_qty) for _,r in op.iterrows())
            gross=sum(abs(float(r.entry)*float(r.remaining_qty)) for _,r in op.iterrows())
            margin=sum(abs(float(r.entry)*float(r.remaining_qty))/max(float(r.leverage),1) for _,r in op.iterrows())
    return {"daily_loss_pct":day/capital*100 if capital else 0,"weekly_loss_pct":week/capital*100 if capital else 0,"monthly_loss_pct":month/capital*100 if capital else 0,"drawdown_pct":dd,"open_risk_pct":open_risk/capital*100 if capital else 0,"gross_exposure_pct":gross/capital*100 if capital else 0,"margin_usage_pct":margin/capital*100 if capital else 0,"concurrent_trades":concurrent}
# ============================================================
# SETTINGS / SELF-CHECKS
# ============================================================
def get_risk_limits() -> RiskLimits:
    s=load_settings().get("risk_limits",{})
    base=asdict(RiskLimits()); base.update({k:v for k,v in s.items() if k in base})
    return RiskLimits(**base)

def precise_amount(exchange_id: str, symbol: str, qty: float) -> float:
    if exchange_id == "binanceusdm":
        try:
            meta=_vision_market_meta(symbol); step=safe_float(meta.get("stepSize"))
            return round_down_step(qty, step) if finite(step) and step>0 else float(qty)
        except Exception:
            return float(qty)
    ad=ExchangeAdapter(exchange_id)
    try: return ad.amount_to_precision(symbol,qty)
    finally: ad.close()

def self_checks() -> pd.DataFrame:
    tests=[]
    def check(name,fn):
        try: fn(); tests.append({"Test":name,"Status":"PASS","Detail":"OK"})
        except Exception as e: tests.append({"Test":name,"Status":"FAIL","Detail":f"{type(e).__name__}: {e}"})
    def t1():
        p=TradePlan("binanceusdm","BTC/USDT:USDT","LONG","MARKET",100,95,[110],[100],10000,1,2,.02,.05,.02,0)
        c=calculate_trade(p); assert c.quantity>0 and c.worst_planned_loss<=101.0 and abs(c.stop_distance-5)<1e-9
    def t2():
        p=TradePlan("binanceusdm","BTC/USDT:USDT","SHORT","MARKET",100,105,[90],[100],10000,1,2,.02,.05,.02,0)
        c=calculate_trade(p); assert c.rr_weighted>1.9
    def t3():
        assert round_down_step(1.23456,.001)==1.234
    def t4():
        bad=TradePlan("x","x","LONG","MARKET",100,101,[110],[100],10000,1,2,.02,.05,.02,0); assert any(i.code=="STOP_DIRECTION" for i in validate_plan_sanity(bad))
    for n,f in [("Long position sizing",t1),("Short R multiple",t2),("Step rounding",t3),("Sanity inverted stop",t4)]: check(n,f)
    return pd.DataFrame(tests)

# ============================================================
# PAGES
# ============================================================
def page_command_center(exchange_id: str, symbol: str):
    st.markdown(tr("## Command Center"))
    if exchange_id=="binanceusdm": st.caption(tr("DATA ROUTER · Price/candles/order book: official Binance Vision public market data (Spot proxy) · Funding/OI: real Binance Futures only when reachable · No synthetic financial values."))
    try:
        with st.spinner(tr("Loading live public market data…")):
            snap=market_snapshot(exchange_id,symbol,"15m")
        if snap["status"]!="OK":
            if snap.get("error_code")=="HOST_REGION_RESTRICTED":
                st.markdown(tr("<div class='pro-card mode-live'><div class='pro-title'>DEPLOYMENT REGION BLOCKED</div><div class='pro-value' style='font-size:1.25rem'>Exchange market data rejected by the hosting region</div><div class='pro-sub'>The app itself is running correctly. The selected exchange is refusing requests from the server that hosts this Streamlit deployment. Streamlit Community Cloud runs in the United States, so global futures APIs may reject the server even when you personally are located elsewhere.</div></div>"),unsafe_allow_html=True)
                st.info(tr("Safe options: switch to an exchange/data source that serves this host region, run the app locally, or deploy this same app on infrastructure in a jurisdiction supported by the exchange. The app will not attempt to bypass exchange geographic restrictions."))
            else:
                st.error(tr("Market data is unavailable. The terminal remains operational in degraded mode."))
            if snap.get("errors"):
                with st.expander("Technical diagnostics"):
                    for msg in snap["errors"]: st.caption(msg)
            return
        df=snap["df"]; t=snap["ticker"]; d=snap["derivatives"]; r=df.iloc[-1]
        # 1h / 4h changes from 15m candles; 24h exchange ticker where available.
        ch1=ticker_change_from_ohlcv(df,4); ch4=ticker_change_from_ohlcv(df,16); ch24=safe_float(t.get("percentage"),ticker_change_from_ohlcv(df,96))
        vals=[("PRICE",price_fmt(snap["last"]),f"Bid {price_fmt(snap['bid'])} · Ask {price_fmt(snap['ask'])}"),("1H",fmt_pct(ch1),"price change"),("4H",fmt_pct(ch4),"price change"),("24H",fmt_pct(ch24),"exchange ticker / candles"),("ATR",fmt_pct(r.atr_pct),f"{price_fmt(r.atr)}"),("SPREAD",fmt_pct(snap["spread_pct"],3),price_fmt(snap["spread"])),("SESSION",market_session_label(),"UTC session windows") ]
        top_cols=st.columns(4)
        for c,(a,b,sub) in zip(top_cols,vals[:4]):
            with c: render_card(a,b,sub)
        lower_cols=st.columns(3)
        for c,(a,b,sub) in zip(lower_cols,vals[4:]):
            with c: render_card(a,b,sub)
        reg=snap["regime"]; vol=snap["volatility"]; ve=snap["volume"]; conf=snap["confidence"]; confl=snap["confluence"]
        btc_ch=eth_ch=np.nan
        try: btc_ch=safe_float(cached_ticker(exchange_id,"BTC/USDT:USDT").get("percentage"))
        except Exception: pass
        try: eth_ch=safe_float(cached_ticker(exchange_id,"ETH/USDT:USDT").get("percentage"))
        except Exception: pass
        risk_env="RISK-ON" if finite(btc_ch) and finite(eth_ch) and btc_ch>0 and eth_ch>0 and vol.get("regime")!="EXTREME" else "RISK-OFF" if finite(btc_ch) and finite(eth_ch) and btc_ch<0 and eth_ch<0 else "NEUTRAL"
        ctxvals=[
            ("BTC 24H",fmt_pct(btc_ch),"market context"),
            ("ETH 24H",fmt_pct(eth_ch),"market context"),
            ("24H VOLUME",fmt_num(t.get("quoteVolume")),"quote volume if reported"),
            ("RISK ENVIRONMENT",risk_env,"heuristic BTC/ETH + volatility context"),
            ("DATA HEALTH",conf.status,f"{conf.score:.0f}/100"),
        ]
        ctx_top=st.columns(3)
        for c,(a,b,sub) in zip(ctx_top,ctxvals[:3]):
            with c: render_card(a,b,sub)
        ctx_bottom=st.columns(2)
        for c,(a,b,sub) in zip(ctx_bottom,ctxvals[3:]):
            with c: render_card(a,b,sub)

        regimevals=[
            ("MARKET REGIME",reg.status,f"confidence {reg.confidence:.0f}%"),
            ("VOLATILITY",vol["regime"],f"ATR percentile {fmt_num(vol.get('percentile'),0)}"),
            ("VOLUME",ve.get("status","—"),f"RVOL {fmt_num(ve.get('rvol'))}"),
            ("FUNDING",fmt_pct(safe_float(d.get("funding"))*100,4),d.get("funding_context","UNAVAILABLE")),
            ("OPEN INTEREST",fmt_num(d.get("oi")),d.get("oi_context","UNAVAILABLE")),
        ]
        reg_top=st.columns(3)
        for c,(a,b,sub) in zip(reg_top,regimevals[:3]):
            with c: render_card(a,b,sub)
        reg_bottom=st.columns(2)
        for c,(a,b,sub) in zip(reg_bottom,regimevals[3:]):
            with c: render_card(a,b,sub)
        render_decision(confl,conf)
        c1,c2,c3=st.columns([1,1,1])
        with c1: st.plotly_chart(gauge_chart(confl["long"],"LONG SCORE"),use_container_width=True,config={"displayModeBar":False})
        with c2: st.plotly_chart(gauge_chart(confl["short"],"SHORT SCORE"),use_container_width=True,config={"displayModeBar":False})
        with c3: st.plotly_chart(gauge_chart(conf.score,"DATA CONFIDENCE"),use_container_width=True,config={"displayModeBar":False})
        st.plotly_chart(candlestick_chart(df,f"{symbol} · 15m",snap["levels"]),use_container_width=True)
        section_label("WHY IT MATTERS")
        c1,c2=st.columns(2)
        with c1:
            st.markdown(tr("**Evidence**"))
            for x in (reg.factors+confl.get("evidence",[]))[:12]: st.write("•",x)
        with c2:
            st.markdown(tr("**Contradictions / risks**"))
            xs=(reg.conflicts+confl.get("conflicts",[])+conf.conflicts)[:12]
            for x in xs or ["No major contradiction detected by the current rule set."]: st.write("•",x)
        st.caption(f"Updated {snap['updated_at']} · request stack {snap['latency_ms']:.0f} ms · Public exchange data; no invented market values.")
    except Exception as e: error_box("Command Center unavailable",e)

def page_market_analysis(exchange_id: str, symbol: str):
    st.markdown(tr("## Market / Analysis"))
    if exchange_id=="binanceusdm": st.caption(tr("Source: Binance Vision public Spot market data for technical analysis/order book. Futures-only derivatives remain real-only and may show UNAVAILABLE if Binance Futures rejects the Streamlit host region."))
    tabs=st.tabs(tr_list(["Chart & Structure","Multi-Timeframe","Derivatives & Flow","Scenarios","Universe"]))
    try: snap=market_snapshot(exchange_id,symbol,st.session_state.timeframe)
    except Exception as e: snap={"status":"UNAVAILABLE","errors":[str(e)]}
    if snap.get("status")!="OK":
        st.error(tr("Selected symbol data unavailable. Change exchange/symbol or retry.")); return
    df=snap["df"]
    with tabs[0]:
        p1,p2,p3,p4=st.columns(4)
        with p1: render_card("STRUCTURE",snap["structure"]["trend"],snap["structure"].get("bos") or "No current BOS")
        with p2: render_card("CHOCH",snap["structure"].get("choch") or "NONE","noise-filtered swing model")
        with p3: render_card("COMPRESSION","YES" if snap["structure"].get("compression") else "NO","rolling range percentile")
        with p4: render_card("EXPANSION","YES" if snap["structure"].get("expansion") else "NO","rolling range percentile")
        st.plotly_chart(candlestick_chart(df,f"{symbol} · {st.session_state.timeframe}",snap["levels"]),use_container_width=True)
        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown(tr("#### Support / Resistance"))
            if snap["levels"].empty: st.info(tr("No levels detected."))
            else: st.dataframe(snap["levels"],use_container_width=True,hide_index=True)
        with c2:
            st.markdown(tr("#### Liquidity map"))
            st.caption(tr("Levels are observed; the interpretation as stop/liquidity clusters is explicitly inferential."))
            if snap["liquidity"].empty: st.info(tr("No clustered liquidity inference available."))
            else: st.dataframe(snap["liquidity"],use_container_width=True,hide_index=True)
        with c3:
            st.markdown(tr("#### Indicator state"))
            r=df.iloc[-1]
            indicator=pd.DataFrame({"Metric":["RSI","ADX","ATR%","RVOL","MACD Hist","BB Width","VWAP distance %"],"Value":[safe_float(r.rsi),safe_float(r.adx),safe_float(r.atr_pct),safe_float(r.rvol),safe_float(r.macd_hist),safe_float(r.bb_width),pct_change(r.close,r.vwap)]})
            st.dataframe(indicator,use_container_width=True,hide_index=True)
    with tabs[1]:
        chosen=st.multiselect(tr("Timeframes"),TIMEFRAMES,default=DEFAULT_MTF,key="mtf_select")
        if st.button(tr("Run multi-timeframe engine"),key="run_mtf"):
            with st.spinner(tr("Analyzing selected timeframes…")): st.session_state["mtf_df"]=mtf_analysis(exchange_id,symbol,chosen)
        mtf=st.session_state.get("mtf_df",pd.DataFrame())
        if mtf.empty: st.info(tr("Run the engine to avoid unnecessary API calls."))
        else:
            st.dataframe(mtf,use_container_width=True,hide_index=True)
            valid=mtf[mtf.Trend.isin(["UP","DOWN","MIXED"])]
            if len(valid):
                ups=(valid.Trend=="UP").sum(); downs=(valid.Trend=="DOWN").sum(); st.caption(f"Alignment: {ups} UP · {downs} DOWN · {len(valid)-ups-downs} MIXED. Alignment is context, not a prediction.")
    with tabs[2]:
        d=snap["derivatives"]
        c1,c2,c3,c4=st.columns(4)
        with c1: render_card("FUNDING",fmt_pct(safe_float(d.get("funding"))*100,4),d.get("funding_context","UNAVAILABLE"))
        with c2: render_card("OI",fmt_num(d.get("oi")),d.get("oi_context","UNAVAILABLE"))
        with c3: render_card("OI Δ 5m",fmt_pct(d.get("oi_change_5m")),"if exchange history supports it")
        with c4: render_card("OI Δ ~1h",fmt_pct(d.get("oi_change_1h")),"contextual interpretation")
        fr=(d.get("raw_funding") or {}) if isinstance(d.get("raw_funding"),dict) else {}
        c1,c2,c3,c4=st.columns(4)
        with c1: render_card("MARK PRICE",price_fmt(fr.get("markPrice")),"from funding/ticker source when exposed")
        with c2: render_card("INDEX PRICE",price_fmt(fr.get("indexPrice")),"from funding source when exposed")
        with c3: render_card("LONG/SHORT RATIO","UNAVAILABLE","not fabricated when unified/source adapter lacks it")
        with c4: render_card("LIQUIDATIONS","UNAVAILABLE","requires a real liquidation feed/source")
        if st.button(tr("Load recent trade flow"),key="flow_load"):
            try:
                if exchange_id=="binanceusdm": tr=_vision_recent_trades(symbol,500)
                else:
                    ad=ExchangeAdapter(exchange_id); tr=ad.fetch_recent_trades(symbol,500); ad.close()
                st.session_state["flow_result"]=order_flow_from_trades(tr)
            except Exception as e: st.session_state["flow_result"]={"status":"UNAVAILABLE","reason":str(e)}
        flow=st.session_state.get("flow_result",{"status":"NOT LOADED"})
        st.json(flow,expanded=True)
        st.caption(tr("Aggressive buy/sell interpretation is only shown when the exchange's recent-trade feed includes a usable side. No synthetic CVD is presented as real order flow."))
    with tabs[3]:
        render_decision(snap["confluence"],snap["confidence"])
        scenarios=snap["scenarios"]
        cols=st.columns(3)
        for col,name in zip(cols,["LONG","SHORT","NEUTRAL"]):
            s=scenarios.get(name,{})
            with col:
                st.markdown(f"#### {name} · {safe_float(s.get('score'),0):.0f}/100")
                st.write("**Trigger:**",s.get("trigger","—")); st.write("**Invalidation:**",price_fmt(s.get("invalidation"))); st.write("**TP1 / TP2 / TP3:**",price_fmt(s.get("tp1")),"/",price_fmt(s.get("tp2")),"/",price_fmt(s.get("tp3"))); st.write("**Risk:**",s.get("risk","—"))
        st.caption(tr("Scenario scores are relative rule-based scores, not calibrated probabilities unless separately validated on historical out-of-sample data."))
    with tabs[4]:
        try:
            meta=cached_market_meta(exchange_id,symbol); st.json(meta,expanded=False)
            st.caption(tr("Binance ANALYSIS/PAPER uses official Binance Vision public Spot metadata as a price/precision proxy; futures contract limits are not fabricated and are revalidated against the real futures venue before LIVE execution.") if exchange_id=="binanceusdm" else "Contract specifications are loaded from the exchange through CCXT rather than hard-coded.")
        except Exception as e: st.warning(f"Contract metadata unavailable: {e}")
        st.markdown(tr("#### Optional external context"))
        st.info(tr("BTC dominance / TOTAL / TOTAL2 / TOTAL3 and economic calendar remain disabled unless a real external data source is explicitly integrated. The app does not invent these values."))

def page_scanner(exchange_id: str):
    st.markdown(tr("## Futures Scanner"))
    if exchange_id=="binanceusdm":
        st.caption(tr("ANALYSIS ROUTER · Ranking/velas/volumen desde Binance Vision public Spot como proxy de mercado. Funding/OI sólo se muestran cuando el endpoint real de Binance Futures responde; no se inventan valores."))
    c1,c2,c3=st.columns(3)
    max_syms=c1.slider(tr("Contracts to scan"),5,30,12,1); tf=c2.selectbox(tr("Scanner timeframe"),["15m","1h","4h"],index=1); minvol=c3.number_input(tr("Min 24h quote volume"),min_value=0.0,value=5_000_000.0,step=1_000_000.0)
    if st.button(tr("Run scanner"),type="primary"):
        with st.spinner(tr("Scanning liquid perpetual contracts with rate-limit-aware sequential requests…")):
            try: st.session_state["scanner_df"]=scan_market(exchange_id,max_syms,tf,minvol)
            except Exception as e: error_box("Scanner failed",e)
    s=st.session_state.get("scanner_df",pd.DataFrame())
    if s.empty: st.info(tr("Run the scanner. It intentionally does not refetch on every widget change.")); return
    filt=st.multiselect(tr("Direction filter"),["LONG CANDIDATES","SHORT CANDIDATES","AVOID"],default=["LONG CANDIDATES","SHORT CANDIDATES","AVOID"])
    x=s.copy()
    if "Long Score" in x:
        x["Classification"]=np.where(x["Avoid Score"]>=60,"AVOID",np.where(x["Long Score"]>=x["Short Score"],"LONG CANDIDATES","SHORT CANDIDATES"))
        x=x[x.Classification.isin(filt)]
        x=x.sort_values(["Avoid Score","Long Score"],ascending=[True,False])
    st.dataframe(x,use_container_width=True,hide_index=True,height=520)
    st.caption(tr("Opportunity components are visible. This scanner ranks conditions; it does not assert that top-ranked trades will be profitable."))

def build_trade_inputs(exchange_id: str, symbol: str) -> Optional[Tuple[TradePlan,TradeCalc,Dict[str,Any]]]:
    try:
        snap=market_snapshot(exchange_id,symbol,st.session_state.timeframe); current=safe_float(snap.get("last"),0)
        if current<=0: raise RuntimeError("No current market price")
    except Exception as e: st.error(f"Cannot build a trade without valid market data: {e}"); return None
    scenarios=snap.get("scenarios",{}); default_side="LONG" if snap["confluence"]["long"]>=snap["confluence"]["short"] else "SHORT"; sc=scenarios.get(default_side,{})
    with st.form("trade_builder_form"):
        c1,c2,c3,c4=st.columns(4)
        side=c1.selectbox(tr("Direction"),["LONG","SHORT"],index=0 if default_side=="LONG" else 1)
        order_type=c2.selectbox(tr("Order type"),["MARKET","LIMIT"],format_func=tr)
        entry=c3.number_input(tr("Entry"),min_value=0.0,value=float(current),format="%.8f")
        lev=c4.number_input(tr("Leverage"),min_value=1.0,max_value=125.0,value=3.0,step=1.0)
        atr=safe_float(snap["df"].atr.iloc[-1],current*.01)
        default_stop=(entry-1.5*atr) if side=="LONG" else (entry+1.5*atr)
        c1,c2,c3,c4=st.columns(4)
        stop=c1.number_input(tr("Stop loss"),min_value=0.0,value=float(default_stop),format="%.8f")
        capital=c2.number_input(tr("Capital / equity (USDT)"),min_value=1.0,value=10000.0,step=100.0)
        risk_pct=c3.number_input(tr("Max risk %"),min_value=.01,max_value=100.0,value=float(get_risk_limits().max_risk_trade_pct),step=.1)
        setup=c4.selectbox(tr("Setup"),["Manual","Trend Pullback","Breakout Retest","Range Reversal","Liquidity Sweep","Momentum Continuation"],format_func=tr)
        risk_dist=abs(entry-stop) if entry and stop else atr
        default_tps=[entry+(1 if side=="LONG" else -1)*risk_dist*r for r in [1.5,2.5,4.0,5.0]]
        cols=st.columns(4); tps=[]
        for i,col in enumerate(cols): tps.append(col.number_input(f"TP{i+1}",min_value=0.0,value=float(max(1e-12,default_tps[i])),format="%.8f"))
        cols=st.columns(4); alloc=[]
        for i,col in enumerate(cols): alloc.append(col.number_input(f"TP{i+1} allocation %",min_value=0.0,max_value=100.0,value=25.0,step=5.0))
        c1,c2,c3,c4=st.columns(4)
        maker=c1.number_input(tr("Maker fee %"),min_value=0.0,value=.02,step=.005,format="%.4f")
        taker=c2.number_input(tr("Taker fee %"),min_value=0.0,value=.05,step=.005,format="%.4f")
        slip=c3.number_input(tr("Expected slippage % / side"),min_value=0.0,value=.02,step=.01,format="%.4f")
        funding=c4.number_input(tr("Expected funding cost %"),min_value=-5.0,max_value=5.0,value=0.0,step=.01,format="%.4f")
        notes=st.text_area(tr("Trade thesis / notes"),placeholder="Trigger, invalidation, why this trade exists, what would make you stand down…")
        submitted=st.form_submit_button(tr("Calculate & validate"),type="primary")
    if not submitted and "last_trade_plan" not in st.session_state: return None
    if submitted:
        p=TradePlan(exchange_id,symbol,side,order_type,entry,stop,tps,alloc,capital,risk_pct,lev,maker,taker,slip,funding,setup,notes)
        try:
            sanity=validate_plan_sanity(p)
            if any(i.severity=="CRITICAL" for i in sanity):
                render_issues(sanity); return None
            mmeta=cached_market_meta(exchange_id,symbol); contract_size=safe_float(mmeta.get("contractSize"),1.0)
            calc=calculate_trade(p,lambda q: precise_amount(exchange_id,symbol,q),contract_size=contract_size); st.session_state["last_trade_plan"]=p; st.session_state["last_trade_calc"]=calc; st.session_state["last_trade_snap"]=snap
        except Exception as e: st.error(f"Calculation failed: {e}"); return None
    return st.session_state.get("last_trade_plan"),st.session_state.get("last_trade_calc"),st.session_state.get("last_trade_snap",snap)
def page_trade_builder(exchange_id: str, symbol: str, mode: str):
    st.markdown(tr("## Trade Builder / Execution Gate"))
    built=build_trade_inputs(exchange_id,symbol)
    if not built: return
    p,calc,snap=built
    limits=get_risk_limits(); meta={}
    try: meta=cached_market_meta(exchange_id,symbol)
    except Exception: pass
    acct=account_context_from_journal(p.capital)
    rr=snap["df"].iloc[-1]; atr_now=max(safe_float(rr.atr,0),1e-12); extension=((p.entry-safe_float(rr.ema20,p.entry))/atr_now)*(1 if p.side=="LONG" else -1)
    market_ctx={"volatility":snap.get("volatility",{}),"data_confidence":snap.get("confidence",EngineResult("LOW",0,0)).score,"spread_pct":snap.get("spread_pct"),"extension_atr":extension}
    issues=risk_gate(p,calc,limits,meta,market_ctx,acct); status=gate_status(issues)
    section_label("MAXIMUM LOSS PREVIEW")
    c1,c2,c3=st.columns([1.2,1,1])
    with c1: st.markdown(f'<div class="big-loss"><div class="pro-title">MAX PLANNED LOSS</div><div class="n">{calc.worst_planned_loss:,.2f} USDT</div><div class="pro-sub">{calc.worst_planned_loss/p.capital*100:.2f}% of equity · includes modeled stop + fees + slippage + funding</div></div>',unsafe_allow_html=True)
    with c2: render_card("POSITION SIZE",fmt_num(calc.quantity,6),f"notional {fmt_num(calc.notional)} USDT")
    with c3: render_card("MARGIN REQUIRED",f"{calc.margin:,.2f} USDT",f"user leverage {p.leverage:.1f}x")
    cols=st.columns(5)
    metrics=[("STOP DISTANCE",fmt_pct(calc.stop_distance_pct),price_fmt(calc.stop_distance)),("WEIGHTED R:R",f"{calc.rr_weighted:.2f}R",f"net TP PnL {calc.net_tp_pnl:,.2f}"),("FEES",f"{calc.expected_fees:,.2f}","estimated round trip"),("SLIPPAGE",f"{calc.expected_slippage:,.2f}","modeled two-sided"),("LIQUIDATION EST.",price_fmt(calc.liquidation_estimate),f"distance {fmt_pct(calc.liquidation_distance_pct)}")]
    for col,(a,b,c) in zip(cols,metrics):
        with col: render_card(a,b,c)
    depth=estimate_orderbook_slippage(snap.get("orderbook",{}),p.side,calc.notional)
    if depth.get("status")!="UNAVAILABLE":
        st.caption(f"Order-book depth estimate for this notional: {depth.get('status')} · estimated one-way slippage {fmt_pct(depth.get('slippage_pct'),4)} · depth filled {fmt_num(depth.get('filled_quote'))} quote. This is a snapshot, not a fill guarantee.")
    st.caption(tr("Liquidation is an indicative isolated-linear estimate only. For existing LIVE positions, exchange-reported liquidation price takes precedence."))
    c1,c2=st.columns(2)
    with c1:
        st.markdown(tr("#### Take-profit ladder"))
        st.dataframe(pd.DataFrame(calc.tp_rows),use_container_width=True,hide_index=True)
    with c2:
        st.markdown(tr("#### Stop alternatives"))
        st.dataframe(pd.DataFrame(stop_engine(p,calc,snap["df"],snap["structure"],snap["levels"])),use_container_width=True,hide_index=True)
    st.plotly_chart(candlestick_chart(snap["df"],f"Trade Visualizer · {symbol}",snap["levels"],p,calc.liquidation_estimate),use_container_width=True)
    section_label("PRE-TRADE GATE")
    tone="good" if status=="TRADE APPROVED" else "warn" if status=="TRADE CONDITIONAL" else "bad"
    st.markdown(f'<div class="pro-card"><div class="pro-title">GATE STATUS</div><div class="decision {tone}">{status}</div><div class="pro-sub">Critical errors always block execution. Warnings require conscious review.</div></div>',unsafe_allow_html=True)
    render_issues(issues)
    st.markdown(tr("#### Psychology check"))
    pc1,pc2,pc3,pc4=st.columns(4)
    fomo=pc1.slider(tr("FOMO"),0,10,0); revenge=pc2.slider(tr("Revenge urge"),0,10,0); fatigue=pc3.slider(tr("Fatigue"),0,10,0); impulsivity=pc4.slider(tr("Impulsivity"),0,10,0)
    psych=max(fomo,revenge,fatigue,impulsivity)
    if psych>=8: st.error(tr("Behavioral gate: strong impulsive-risk signal. Consider NO TRADE until the checklist normalizes."))
    elif psych>=5: st.warning(tr("Behavioral warning: elevated FOMO/revenge/fatigue/impulsivity."))
    else: st.success(tr("Behavioral checklist: no high-intensity signal recorded."))
    section_label("ORDER PREVIEW")
    preview={"mode":mode,"exchange":p.exchange,"symbol":p.symbol,"side":p.side,"type":p.order_type,"entry":p.entry,"base_quantity":calc.quantity,"order_amount":calc.order_amount,"contract_size":calc.contract_size,"notional":calc.notional,"leverage":p.leverage,"margin":calc.margin,"stop":p.stop,"tps":p.tps,"risk_budget":calc.risk_budget,"worst_planned_loss":calc.worst_planned_loss,"weighted_rr":calc.rr_weighted,"fees_est":calc.expected_fees,"slippage_est":calc.expected_slippage,"liquidation_est":calc.liquidation_estimate}
    st.json(preview,expanded=False)
    if mode=="ANALYSIS ONLY":
        st.info(tr("ANALYSIS ONLY: order execution is disabled by design."))
    elif mode=="PAPER":
        if status=="TRADE REJECTED": st.error(tr("Paper order blocked by critical validation errors. Fix the plan first."))
        elif st.button(tr("Submit PAPER trade"),type="primary",key="paper_submit"):
            pid=create_paper_position(p,calc,snap["last"]); st.success(f"Paper position opened: {pid[:10]}…"); st.session_state.pop("last_trade_plan",None); st.session_state.pop("last_trade_calc",None)
    else:
        st.error(tr("LIVE MODE — REAL MONEY / REAL ORDERS"))
        if not live_enabled_by_server(): st.warning(tr("Server-level ENABLE_LIVE_TRADING is OFF. Set it explicitly in Streamlit secrets/environment to permit live execution."))
        okcred,msg=credential_status(exchange_id); st.caption(f"Credentials: {msg}")
        if status=="TRADE REJECTED" or psych>=8:
            st.error(tr("LIVE order blocked by the trade gate."))
        else:
            st.markdown(tr("**Double confirmation required**"))
            exact=f"ENABLE LIVE {symbol}"
            phrase=st.text_input(f"Type exactly: {exact}",key="live_phrase")
            understand=st.checkbox(tr("I confirm this is a real leveraged futures order and I reviewed the stop, size, leverage and maximum planned loss."),key="live_ack")
            if st.button(tr("Generate one-time execution code"),key="gen_code"):
                st.session_state.live_confirm_code=str(random.randint(100000,999999)); st.session_state.live_confirm_hash=hash_payload(preview)
            if st.session_state.get("live_confirm_code"):
                st.warning(f"One-time code: {st.session_state.live_confirm_code}")
            code=st.text_input(tr("Enter one-time code"),type="password",key="live_code")
            ready=phrase==exact and understand and code==str(st.session_state.get("live_confirm_code")) and st.session_state.get("live_confirm_hash")==hash_payload(preview) and live_enabled_by_server() and okcred
            if st.button(tr("EXECUTE LIVE ORDER"),type="primary",disabled=not ready,key="execute_live"):
                payload_hash=hash_payload(preview)
                if st.session_state.get("last_order_hash")==payload_hash: st.error(tr("Duplicate-order protection: this exact preview was already submitted in this session."))
                else:
                    try:
                        with st.spinner(tr("Submitting protected LIVE order…")):
                            order=execute_live_entry(p,calc)
                        st.session_state.last_order_hash=payload_hash; st.session_state.live_confirm_code=None
                        entry_order=order.get("entry_order",{}); protection=order.get("protection",{})
                        st.success(f"Protected entry submitted. Exchange order ID: {entry_order.get('id','—')}")
                        if protection.get("tp_errors"): st.warning(tr("Entry stop is attached, but one or more TP ladder actions need review."))
                        st.json({"entry_order":{k:v for k,v in entry_order.items() if k!="info"},"protection":protection},expanded=False)
                    except Exception as e: error_box("LIVE execution blocked/failed",e)

def page_positions(exchange_id: str, symbol: str, mode: str):
    st.markdown(tr("## Positions / Execution"))
    if mode=="PAPER":
        if st.button(tr("Refresh & process PAPER positions")):
            events=process_paper_positions(exchange_id)
            for e in events: st.info(e)
        p=read_table("paper_positions")
        if p.empty or not len(p[p.status=="OPEN"]): st.info(tr("No open paper positions."))
        else:
            op=p[p.status=="OPEN"].copy(); st.dataframe(op[["id","opened_at","symbol","side","entry","qty","remaining_qty","leverage","stop","realized_pnl","fees","mfe","mae","status"]],use_container_width=True,hide_index=True)
            st.caption(tr("Paper engine uses conservative same-candle ordering: if SL and TP are both touched, SL is processed first."))
    else:
        ok,msg=credential_status(exchange_id)
        if not ok: st.info(f"Private account data unavailable: {msg}"); return
        if st.button(tr("Load private account positions"),key="load_live_positions"):
            try: st.session_state["live_account"]=private_account_snapshot(exchange_id,symbol)
            except Exception as e: error_box("Private account fetch failed",e)
        acct=st.session_state.get("live_account")
        if not acct: st.info(tr("Private data is loaded only on request; public analysis does not require API credentials.")); return
        render_card("USDT FREE",fmt_num(acct.get("free")),f"total {fmt_num(acct.get('total'))}")
        rows=[]
        for p in acct.get("positions",[]):
            contracts=safe_float(p.get("contracts"),0)
            if contracts==0: continue
            entry=safe_float(p.get("entryPrice")); mark=safe_float(p.get("markPrice")); liq=safe_float(p.get("liquidationPrice")); side=str(p.get("side","")).upper(); pnl=safe_float(p.get("unrealizedPnl")); notional=abs(safe_float(p.get("notional"),contracts*mark)); lev=safe_float(p.get("leverage")); roe=pnl/(notional/max(lev,1))*100 if notional and lev else np.nan
            health="HEALTHY"
            if finite(liq) and finite(mark):
                dist=abs(mark-liq)/mark*100
                health="CRITICAL" if dist<2 else "DANGER" if dist<5 else "ATTENTION" if dist<10 else "HEALTHY"
            rows.append({"Symbol":p.get("symbol"),"Side":side,"Entry":entry,"Mark":mark,"Contracts":contracts,"Notional":notional,"Leverage":lev,"PnL":pnl,"ROE %":roe,"Liquidation":liq,"Health":health})
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        else: st.info(tr("No open positions returned by the exchange."))
        st.caption(tr("For LIVE positions, exchange-reported liquidation price is shown when available and supersedes local estimates."))
    section_label("KILL SWITCH")
    if st.session_state.kill_switch: st.error(tr("KILL SWITCH ACTIVE — NEW ORDERS BLOCKED"))
    c1,c2=st.columns(2)
    if c1.button(tr("Activate kill switch"),disabled=st.session_state.kill_switch): st.session_state.kill_switch=True; audit("KILL_SWITCH_ON",{"exchange":exchange_id},"CRITICAL"); st.rerun()
    if c2.button(tr("Deactivate kill switch"),disabled=not st.session_state.kill_switch): st.session_state.kill_switch=False; audit("KILL_SWITCH_OFF",{"exchange":exchange_id},"WARNING"); st.rerun()
    if mode=="LIVE" and st.session_state.kill_switch:
        st.warning(tr("Optional destructive action: cancel pending orders only. Closing positions is intentionally not automatic."))
        phrase=st.text_input(tr("Type CANCEL PENDING ORDERS"),key="cancel_phrase")
        if st.button(tr("Cancel all pending LIVE orders"),disabled=phrase!="CANCEL PENDING ORDERS"):
            try: res=cancel_pending_live(exchange_id,None); st.success(tr("Cancel request completed.")); st.json(res,expanded=False)
            except Exception as e: error_box("Cancel-all failed",e)

def page_risk_center(exchange_id: str, mode: str):
    st.markdown(tr("## Risk Center / Portfolio Risk"))
    limits=get_risk_limits(); capital=st.number_input(tr("Reference account equity (USDT)"),min_value=1.0,value=10000.0,step=100.0,key="risk_equity")
    ctx=account_context_from_journal(capital)
    cols=st.columns(4)
    with cols[0]: render_card("DAILY PnL %",fmt_pct(ctx["daily_loss_pct"]),f"limit -{limits.max_daily_loss_pct:.1f}%")
    with cols[1]: render_card("DRAWDOWN",fmt_pct(ctx["drawdown_pct"]),f"limit {limits.max_drawdown_pct:.1f}%")
    with cols[2]: render_card("OPEN RISK",fmt_pct(ctx["open_risk_pct"]),f"limit {limits.max_open_risk_pct:.1f}%")
    with cols[3]: render_card("RISK / TRADE",fmt_pct(limits.max_risk_trade_pct),"configured maximum")
    if ctx["daily_loss_pct"]<=-limits.max_daily_loss_pct: st.error(tr("DAILY RISK LIMIT REACHED — new trades should remain blocked."))
    if ctx["drawdown_pct"]>=limits.max_drawdown_pct: st.error(tr("MAX DRAWDOWN LIMIT REACHED."))
    positions=[]; equity=capital
    if mode=="LIVE" and credential_status(exchange_id)[0]:
        if st.button(tr("Fetch LIVE portfolio risk")):
            try:
                ad=ExchangeAdapter(exchange_id,private=True,sandbox=truthy(get_secret("USE_EXCHANGE_SANDBOX",False))); bal=ad.fetch_balance(); positions=ad.fetch_positions(); ad.close(); equity=safe_float((bal.get("USDT") or {}).get("total"),capital); st.session_state["portfolio_positions"]=positions; st.session_state["portfolio_equity"]=equity
            except Exception as e: error_box("Portfolio fetch failed",e)
        positions=st.session_state.get("portfolio_positions",[]); equity=st.session_state.get("portfolio_equity",capital)
    if positions:
        pr=portfolio_risk_from_positions(positions,equity)
        cols=st.columns(5)
        vals=[("LONG EXP",fmt_num(pr["long_exposure"])),("SHORT EXP",fmt_num(pr["short_exposure"])),("NET EXP",fmt_num(pr["net_exposure"])),("PORTFOLIO LEV",f"{pr['portfolio_leverage']:.2f}x" if finite(pr["portfolio_leverage"]) else "—"),("MARGIN USE",fmt_pct(pr["margin_usage_pct"]))]
        for c,(a,b) in zip(cols,vals):
            with c: render_card(a,b,"")
        pdf=pd.DataFrame(pr["rows"]); st.dataframe(pdf,use_container_width=True,hide_index=True)
        syms=pdf.symbol.dropna().unique().tolist()
        if len(syms)>=2:
            corr=correlation_matrix(exchange_id,syms); st.plotly_chart(px.imshow(corr,zmin=-1,zmax=1,text_auto=".2f",aspect="auto",title="Position return correlations"),use_container_width=True)
            vals_corr=corr.where(~np.eye(len(corr),dtype=bool)).abs().stack(); score=float(vals_corr.mean()*100) if len(vals_corr) else 0; render_card("CORRELATION RISK SCORE",f"{score:.0f}/100","High directional correlation can make several trades behave like one exposure.")
    else: st.info(tr("Portfolio-level live exposure appears here when private positions are loaded. PAPER positions remain visible in Positions."))
    section_label("STRESS TEST")
    notional=st.number_input(tr("Portfolio net directional notional for stress test"),min_value=0.0,value=10000.0,step=1000.0)
    stress=[]
    for move in [-5,-3,-2,-1,1,2,3,5]: stress.append({"Market move %":move,"Approx PnL":notional*move/100,"Equity impact %":notional*move/100/capital*100})
    st.dataframe(pd.DataFrame(stress),use_container_width=True,hide_index=True)
    st.caption(tr("Stress test is linear and hypothetical; gaps, nonlinear liquidation mechanics, correlation breakdown and slippage can worsen outcomes."))
def page_journal_analytics():
    st.markdown(tr("## Journal / Analytics"))
    tabs=st.tabs(tr_list(["Journal","Performance","Reviews","Monte Carlo","Capital Flows"]))
    with tabs[0]:
        st.markdown(tr("#### Add / review trade"))
        with st.form("journal_form"):
            c1,c2,c3,c4=st.columns(4)
            symbol=c1.text_input(tr("Symbol"),"BTC/USDT:USDT"); side=c2.selectbox(tr("Side"),["LONG","SHORT"],format_func=tr); setup=c3.selectbox(tr("Setup"),["Manual","Trend Pullback","Breakout Retest","Range Reversal","Liquidity Sweep","Momentum Continuation"],format_func=tr); lev=c4.number_input(tr("Leverage"),1.0,125.0,3.0)
            c1,c2,c3,c4=st.columns(4)
            entry=c1.number_input(tr("Entry"),0.0,value=1.0,format="%.8f"); stop=c2.number_input(tr("Stop"),0.0,value=.95,format="%.8f"); pnl=c3.number_input(tr("PnL gross"),value=0.0); fees=c4.number_input(tr("Fees"),min_value=0.0,value=0.0)
            c1,c2,c3,c4=st.columns(4)
            funding=c1.number_input(tr("Funding"),value=0.0); mfe=c2.number_input(tr("MFE price units"),min_value=0.0,value=0.0); mae=c3.number_input(tr("MAE price units"),min_value=0.0,value=0.0); risk_usdt=c4.number_input(tr("Planned risk USDT"),min_value=0.0,value=100.0)
            reason=st.text_area(tr("Reason / plan")); lesson=st.text_area(tr("Lesson")); mistake=st.text_input(tr("Mistake / rule broken")); notes=st.text_area(tr("Notes"))
            st.caption(tr("Discipline is separate from economic outcome."))
            d1,d2,d3,d4=st.columns(4); respected=d1.checkbox(tr("Respected plan"),True); moved=d2.checkbox(tr("Did NOT widen stop"),True); chased=d3.checkbox(tr("Did NOT chase"),True); within=d4.checkbox(tr("Risk stayed within limit"),True)
            save=st.form_submit_button(tr("Save journal trade"))
        if save:
            net=pnl-fees-funding; r=net/risk_usdt if risk_usdt else None; disc=sum([respected,moved,chased,within])/4*100
            jid=uuid.uuid4().hex
            with db_connect() as con:
                con.execute("INSERT INTO journal(id,opened_at,closed_at,exchange,symbol,side,setup,entry,stop,tps_json,risk_pct,risk_usdt,quantity,leverage,market_regime,long_score,short_score,data_confidence,reason,outcome,pnl,pnl_net,r_result,mfe,mae,duration_min,fees,funding,emotion_json,discipline_json,screenshot,notes,mistake,lesson,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (jid,iso_now(),iso_now(),"manual",symbol,side,setup,entry,stop,"[]",None,risk_usdt,None,lev,"",None,None,None,reason,"WIN" if net>0 else "LOSS" if net<0 else "FLAT",pnl,net,r,mfe,mae,None,fees,funding,"{}",json.dumps({"score":disc,"respected_plan":respected,"did_not_widen_stop":moved,"did_not_chase":chased,"risk_within_limit":within}),"",notes,mistake,lesson,"manual"))
            audit("JOURNAL_TRADE_SAVED",{"id":jid,"symbol":symbol,"net":net}); st.success(tr("Trade saved."))
        j=read_table("journal")
        if j.empty: st.info(tr("No trades yet."))
        else: st.dataframe(j.sort_values("closed_at",ascending=False),use_container_width=True,hide_index=True,height=430)
    with tabs[1]:
        j=read_table("journal"); m=journal_metrics(j)
        if not m.get("trades"): st.info(tr("No completed trades yet."))
        else:
            cols=st.columns(6); vals=[("TRADES",m["trades"]),("WIN RATE",fmt_pct(m["win_rate"])),("NET PnL",fmt_num(m["net_pnl"])),("EXPECTANCY",fmt_num(m["expectancy"])),("PROFIT FACTOR",fmt_num(m["profit_factor"])),("AVG R",f"{m['avg_r']:.2f}R" if finite(m["avg_r"]) else "—")]
            for c,(a,b) in zip(cols,vals):
                with c: render_card(a,str(b),"")
            curve=equity_drawdown_curve(j,10000)
            if not curve.empty:
                fig=go.Figure(); fig.add_trace(go.Scatter(x=curve.time,y=curve.equity,name="Equity")); fig.update_layout(template="plotly_dark",height=360,title="Capital curve",paper_bgcolor="#0a0f17",plot_bgcolor="#0a0f17"); st.plotly_chart(fig,use_container_width=True)
                fig2=go.Figure(); fig2.add_trace(go.Scatter(x=curve.time,y=curve.drawdown_pct,fill="tozeroy",name="Drawdown %")); fig2.update_layout(template="plotly_dark",height=280,title="Drawdown",paper_bgcolor="#0a0f17",plot_bgcolor="#0a0f17"); st.plotly_chart(fig2,use_container_width=True)
            x=j.copy(); x["pnl_net"]=pd.to_numeric(x.pnl_net,errors="coerce").fillna(0); x["r_result"]=pd.to_numeric(x.r_result,errors="coerce")
            section_label("SETUP STATISTICS")
            g=x.groupby("setup").agg(trades=("id","count"),net_pnl=("pnl_net","sum"),avg_r=("r_result","mean"),wins=("pnl_net",lambda s:(s>0).sum())).reset_index(); g["win_rate"]=g.wins/g.trades*100; g["strategy_health"]=np.where(g.trades<10,"INSUFFICIENT DATA",np.where((g.avg_r>0)&(g.win_rate>=45),"HEALTHY",np.where(g.avg_r>-0.1,"WATCH","DEGRADED")))
            st.dataframe(g,use_container_width=True,hide_index=True)
            st.caption(tr("Sample-size guard: strategy health remains INSUFFICIENT DATA below 10 trades. Positive PnL alone is not treated as proven edge."))
    with tabs[2]:
        j=read_table("journal")
        if j.empty: st.info(tr("No review data."))
        else:
            x=j.copy(); x["dt"]=pd.to_datetime(x.closed_at,utc=True,errors="coerce"); x["pnl_net"]=pd.to_numeric(x.pnl_net,errors="coerce").fillna(0); x["r_result"]=pd.to_numeric(x.r_result,errors="coerce").fillna(0)
            now=utc_now(); periods={"DAILY":now-timedelta(days=1),"WEEKLY":now-timedelta(days=7),"MONTHLY":now-timedelta(days=30)}
            for title,start in periods.items():
                y=x[x.dt>=start]; st.markdown(f"#### {title} REVIEW")
                if y.empty: st.caption(tr("No trades in period.")); continue
                cols=st.columns(5); data=[("Trades",len(y)),("PnL",fmt_num(y.pnl_net.sum())),("R",f"{y.r_result.sum():.2f}R"),("Win rate",fmt_pct((y.pnl_net>0).mean()*100)),("Fees",fmt_num(pd.to_numeric(y.fees,errors='coerce').fillna(0).sum()))]
                for c,(a,b) in zip(cols,data):
                    with c: render_card(a,str(b),"")
                if "mistake" in y:
                    mistakes=y.mistake.fillna("").astype(str); top=mistakes[mistakes.str.len()>0].value_counts().head(5)
                    if len(top): st.write("**Most frequent mistakes:**",", ".join(f"{k} ({v})" for k,v in top.items()))
    with tabs[3]:
        j=read_table("journal")
        if j.empty or pd.to_numeric(j.r_result,errors="coerce").dropna().shape[0]<3: st.info(tr("At least 3 R-results are required; 20+ is preferable."))
        else:
            c1,c2,c3=st.columns(3); sims=c1.slider(tr("Simulations"),500,5000,2000,500); future_n=c2.slider(tr("Trades per simulation"),10,200,50,10); risk=c3.number_input(tr("Risk % per future trade"),.1,10.0,1.0,.1)
            out,stats=monte_carlo(pd.to_numeric(j.r_result,errors="coerce").dropna(),sims,future_n,100,risk)
            st.json(stats,expanded=False)
            if not out.empty:
                fig=px.histogram(out,x="final_equity",nbins=60,title="Bootstrap final equity distribution"); fig.update_layout(template="plotly_dark",paper_bgcolor="#0a0f17",plot_bgcolor="#0a0f17"); st.plotly_chart(fig,use_container_width=True)
            st.caption(tr("Monte Carlo is a bootstrap of observed R outcomes, not a forecast; regime changes and non-stationarity can invalidate the distribution."))
    with tabs[4]:
        with st.form("capital_flow"):
            c1,c2,c3=st.columns(3); kind=c1.selectbox(tr("Type"),["DEPOSIT","WITHDRAWAL"]); amt=c2.number_input(tr("Amount"),min_value=0.0,value=0.0); note=c3.text_input(tr("Note")); add=st.form_submit_button(tr("Add capital flow"))
        if add and amt>0:
            with db_connect() as con: con.execute("INSERT INTO capital_flows VALUES(?,?,?,?,?)",(uuid.uuid4().hex,iso_now(),kind,amt,note))
            st.success(tr("Capital flow recorded. Deposits/withdrawals are kept separate from trading PnL."))
        st.dataframe(read_table("capital_flows"),use_container_width=True,hide_index=True)

def page_backtest(exchange_id: str, symbol: str):
    st.markdown(tr("## Backtest / Walk-Forward"))
    c1,c2,c3,c4=st.columns(4); tf=c1.selectbox(tr("Timeframe"),["5m","15m","1h","4h","1d"],index=2,key="bt_tf"); strategy=c2.selectbox(tr("Strategy"),["Trend Pullback","Breakout Retest","Range Reversal","Momentum Continuation"]); bars=c3.slider(tr("Bars"),300,1500,750,50); risk=c4.number_input(tr("Risk %"),.1,5.0,1.0,.1,key="bt_risk")
    c1,c2,c3=st.columns(3); stop_atr=c1.number_input(tr("Stop ATR"),.5,5.0,1.5,.1); rr=c2.number_input(tr("Target R"),.5,10.0,2.0,.25); fee=c3.number_input(tr("Fee % / side"),0.0,.5,.05,.005)
    slip=st.number_input(tr("Slippage % / side"),0.0,1.0,.02,.01,key="bt_slip")
    if st.button(tr("Run backtest"),type="primary"):
        try:
            with st.spinner(tr("Loading historical candles and simulating conservatively…")):
                df=cached_ohlcv(exchange_id,symbol,tf,bars); t,eq,m=run_backtest(df,strategy,risk,stop_atr,rr,fee,slip)
            st.session_state["bt_results"]=(t,eq,m,df)
        except Exception as e: error_box("Backtest failed",e)
    result=st.session_state.get("bt_results")
    if not result: st.info(tr("Backtest uses only available exchange OHLCV. Intrabar collisions are resolved conservatively in favor of the stop.")); return
    t,eq,m,df=result
    if not m.get("trades"): st.warning(tr("No trades generated by this rule set in the selected sample.")); return
    cols=st.columns(6); vals=[("Trades",m["trades"]),("Win rate",fmt_pct(m["win_rate"])),("Net PnL",fmt_num(m["net_pnl"])),("PF",fmt_num(m["profit_factor"])),("Avg R",f"{m['avg_r']:.2f}R"),("Max DD",fmt_pct(m["max_dd_pct"]))]
    for c,(a,b) in zip(cols,vals):
        with c: render_card(a,str(b),"")
    fig=go.Figure(); fig.add_trace(go.Scatter(x=eq.exit_time,y=eq.balance,name="Backtest equity")); fig.update_layout(template="plotly_dark",height=360,paper_bgcolor="#0a0f17",plot_bgcolor="#0a0f17"); st.plotly_chart(fig,use_container_width=True)
    st.dataframe(t.tail(200),use_container_width=True,hide_index=True)
    section_label("BASIC WALK-FORWARD VIEW")
    n=len(df); a,b=int(n*.6),int(n*.8); splits=[("TRAIN",df.iloc[:a]),("VALIDATION",df.iloc[a:b]),("OUT-OF-SAMPLE",df.iloc[b:])]; rows=[]
    for name,part in splits:
        tt,ee,mm=run_backtest(part,strategy,risk,stop_atr,rr,fee,slip); rows.append({"Split":name,**mm})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.caption(tr("Parameters are not optimized separately on validation/OOS here; this deliberately reduces the temptation to overfit a small sample."))

def page_playbook_alerts(exchange_id: str, symbol: str):
    st.markdown(tr("## Playbook / Alerts"))
    tabs=st.tabs(tr_list(["Playbook","Alerts","Overtrading / FOMO"]))
    with tabs[0]:
        with st.form("playbook_form"):
            name=st.text_input(tr("Setup name")); c1,c2,c3=st.columns(3); side=c1.selectbox(tr("Direction"),["BOTH","LONG","SHORT"],format_func=tr); tfs=c2.multiselect(tr("Timeframes"),TIMEFRAMES,default=["15m","1h"]); minrr=c3.number_input(tr("Minimum R:R"),.5,10.0,1.5,.1)
            c1,c2=st.columns(2); vol=c1.selectbox(tr("Allowed volatility"),["ANY","LOW/NORMAL","NORMAL/HIGH","NO EXTREME"],format_func=tr); session=c2.selectbox(tr("Session"),["ANY","ASIA","LONDON","NEW YORK","OVERLAPS"],format_func=tr)
            cond=st.text_area(tr("Conditions")); inv=st.text_area(tr("Invalidation")); checklist=st.text_area(tr("Checklist"),placeholder="One rule per line")
            save=st.form_submit_button(tr("Save setup"))
        if save and name.strip():
            with db_connect() as con:
                con.execute("INSERT INTO playbook VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET side=excluded.side,timeframes=excluded.timeframes,min_rr=excluded.min_rr,volatility=excluded.volatility,session=excluded.session,conditions=excluded.conditions,invalidation=excluded.invalidation,checklist=excluded.checklist,updated_at=excluded.updated_at",(uuid.uuid4().hex,name.strip(),side,json.dumps(tfs),minrr,vol,session,cond,inv,checklist,iso_now()))
            st.success(tr("Setup saved."))
        pb=read_table("playbook"); st.dataframe(pb,use_container_width=True,hide_index=True)
    with tabs[1]:
        with st.form("alert_form"):
            c1,c2,c3,c4=st.columns(4); kind=c1.selectbox(tr("Alert"),["PRICE","RSI","FUNDING","OI_CHANGE","VOLATILITY","SPREAD","STALE_DATA"]); op=c2.selectbox(tr("Operator"),[">",">=","<","<="]); threshold=c3.number_input(tr("Threshold"),value=0.0,format="%.8f"); sev=c4.selectbox(tr("Severity"),SEVERITIES,index=2); note=st.text_input(tr("Note")); add=st.form_submit_button(tr("Add alert"))
        if add:
            with db_connect() as con: con.execute("INSERT INTO alerts VALUES(?,?,?,?,?,?,?,?,?,?,?)",(uuid.uuid4().hex,iso_now(),1,sev,exchange_id,symbol,kind,op,threshold,note,None))
            st.success(tr("Alert rule saved. This single-file app evaluates rules when the relevant page/app reruns; it is not a background daemon."))
        st.dataframe(read_table("alerts"),use_container_width=True,hide_index=True)
    with tabs[2]:
        j=read_table("journal")
        if j.empty: st.info(tr("No trade history to inspect."))
        else:
            x=j.copy(); x["dt"]=pd.to_datetime(x.closed_at,utc=True,errors="coerce"); x["risk_usdt"]=pd.to_numeric(x.risk_usdt,errors="coerce"); x=x.sort_values("dt")
            last24=x[x.dt>=utc_now()-timedelta(days=1)]
            warnings=[]
            if len(last24)>=8: warnings.append(f"High trade count: {len(last24)} trades in 24h")
            if len(x)>=3:
                recent=x.tail(3); prev=x.iloc[-4:-1] if len(x)>=4 else pd.DataFrame()
                if not prev.empty and recent.risk_usdt.mean()>prev.risk_usdt.mean()*1.5: warnings.append("Recent risk size increased >50% versus preceding trades")
            if warnings:
                for w in warnings: st.warning(w)
            else: st.success(tr("No simple overtrading/risk-escalation flag detected from stored journal data."))
            st.caption(tr("FOMO/late-entry checks are behavioral/rule-based alerts, not psychological diagnoses."))
def evaluate_saved_alerts(exchange_id: str, symbol: str, snap: Dict[str,Any]) -> List[Dict[str,Any]]:
    a=read_table("alerts")
    if a.empty: return []
    a=a[(a.enabled==1)&(a.exchange==exchange_id)&(a.symbol==symbol)]
    if a.empty: return []
    r=snap["df"].iloc[-1] if snap.get("status")=="OK" else None
    values={
        "PRICE":snap.get("last"),
        "RSI":safe_float(r.rsi) if r is not None else np.nan,
        "FUNDING":safe_float((snap.get("derivatives") or {}).get("funding"))*100,
        "OI_CHANGE":safe_float((snap.get("derivatives") or {}).get("oi_change_1h")),
        "VOLATILITY":safe_float((snap.get("volatility") or {}).get("percentile")),
        "SPREAD":snap.get("spread_pct"),
        "STALE_DATA":safe_float((snap.get("confidence") or EngineResult("",0,0)).meta.get("age_seconds")),
    }
    out=[]
    for _,row in a.iterrows():
        v=safe_float(values.get(row.kind)); th=safe_float(row.threshold)
        if not finite(v) or not finite(th): continue
        hit={">":v>th,">=":v>=th,"<":v<th,"<=":v<=th}.get(row.operator,False)
        if hit: out.append({"severity":row.severity,"kind":row.kind,"value":v,"threshold":th,"note":row.note})
    return out

def page_system_health(exchange_id: str, symbol: str):
    st.markdown(tr("## Data Quality / System Health"))
    try: snap=market_snapshot(exchange_id,symbol,st.session_state.timeframe)
    except Exception as e: snap={"status":"UNAVAILABLE","errors":[str(e)]}
    rows=[]
    if snap.get("status")=="OK":
        conf=snap["confidence"]
        age=conf.meta.get("age_seconds",np.nan)
        rows += [
          {"Source":"Price/Ticker","Status":"CONNECTED" if finite(snap.get("last")) else "ERROR","Freshness sec":0 if finite(snap.get("last")) else np.nan,"Detail":f"{price_fmt(snap.get('last'))} · {public_data_source_label(exchange_id)}"},
          {"Source":"Candles","Status":"CONNECTED" if finite(age) and age<300 else "STALE","Freshness sec":age,"Detail":f"{len(snap['df'])} bars · {public_data_source_label(exchange_id)}"},
          {"Source":"Order Book","Status":"CONNECTED" if snap.get("orderbook",{}).get("bids") else "ERROR","Freshness sec":0,"Detail":f"spread {fmt_pct(snap.get('spread_pct'),3)}"},
          {"Source":"Funding/OI","Status":"CONNECTED" if snap.get("derivatives",{}).get("status")=="AVAILABLE" else "DELAYED/UNAVAILABLE","Freshness sec":np.nan,"Detail":snap.get("derivatives",{}).get("status","UNAVAILABLE")},
          {"Source":"Data Confidence","Status":conf.status,"Freshness sec":age,"Detail":f"{conf.score:.0f}/100"},
        ]
    else:
        rows.append({"Source":"Market stack","Status":"ERROR","Freshness sec":np.nan,"Detail":"; ".join(snap.get("errors",[]))})
    okcred,msg=credential_status(exchange_id); rows.append({"Source":"Private API credentials","Status":"CONFIGURED" if okcred else "UNAVAILABLE","Freshness sec":np.nan,"Detail":msg})
    rows.append({"Source":"CCXT","Status":"CONNECTED" if ccxt else "ERROR","Freshness sec":np.nan,"Detail":getattr(ccxt,"__version__","not installed") if ccxt else "not installed"})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    cols=st.columns(4)
    with cols[0]: render_card("APP VERSION",APP_VERSION,f"build {BUILD}")
    with cols[1]: render_card("MODE",st.session_state.mode,"LIVE server gate ON" if live_enabled_by_server() else "LIVE server gate OFF")
    with cols[2]: render_card("EXCHANGE",SUPPORTED_EXCHANGES.get(exchange_id,exchange_id),"")
    with cols[3]: render_card("LAST REFRESH",datetime.now().strftime("%H:%M:%S"),"UI rerun time")
    if snap.get("status")=="OK":
        alerts=evaluate_saved_alerts(exchange_id,symbol,snap)
        section_label("ACTIVE ALERT EVALUATION")
        if not alerts: st.success(tr("No saved alert rule is currently triggered for this symbol."))
        else:
            for a in alerts:
                text=f"{a['kind']} = {a['value']:.6g} vs {a['threshold']:.6g}. {a['note'] or ''}"
                if a["severity"] in {"CRITICAL","DANGER"}: st.error(text)
                elif a["severity"]=="WARNING": st.warning(text)
                else: st.info(text)
    section_label("SELF-CHECKS")
    if st.button(tr("Run internal calculation tests")):
        checks=self_checks(); st.dataframe(checks,use_container_width=True,hide_index=True)
        if (checks.Status=="PASS").all(): st.success(tr("All internal calculation self-checks passed."))
        else: st.error(tr("One or more self-checks failed. Do not use LIVE mode until resolved."))
    section_label("AUDIT LOG")
    log=read_table("audit")
    if log.empty: st.info(tr("Audit log is empty."))
    else: st.dataframe(log.sort_values("id",ascending=False).head(200),use_container_width=True,hide_index=True)
    st.caption(tr("The app uses retry with exponential backoff, API timeouts and Streamlit caches. A failing data source degrades its module instead of fabricating replacement market data."))

def page_configuration(exchange_id: str, symbol: str):
    st.markdown(tr("## Configuration / Setup / Deployment"))
    tabs=st.tabs(tr_list(["Risk Limits","Trading Safety","API & Secrets","Deployment","Architecture"]))
    with tabs[0]:
        lim=get_risk_limits()
        with st.form("risk_limits_form"):
            c1,c2,c3=st.columns(3)
            mr=c1.number_input(tr("Max Risk / Trade %"),.1,100.0,lim.max_risk_trade_pct,.1); dl=c2.number_input(tr("Max Daily Loss %"),.1,100.0,lim.max_daily_loss_pct,.1); wl=c3.number_input(tr("Max Weekly Loss %"),.1,100.0,lim.max_weekly_loss_pct,.1)
            c1,c2,c3=st.columns(3)
            ml=c1.number_input(tr("Max Monthly Loss %"),.1,100.0,lim.max_monthly_loss_pct,.1); op=c2.number_input(tr("Max Open Risk %"),.1,100.0,lim.max_open_risk_pct,.1); exp=c3.number_input(tr("Max Portfolio Exposure %"),10.0,2000.0,lim.max_portfolio_exposure_pct,10.0)
            c1,c2,c3=st.columns(3)
            mu=c1.number_input(tr("Max Margin Usage %"),1.0,100.0,lim.max_margin_usage_pct,1.0); lev=c2.number_input(tr("Max Leverage"),1.0,125.0,lim.max_leverage,1.0); dd=c3.number_input(tr("Max Drawdown %"),1.0,100.0,lim.max_drawdown_pct,1.0)
            c1,c2,c3=st.columns(3)
            ct=c1.number_input(tr("Max Concurrent Trades"),1,50,lim.max_concurrent_trades,1); corr=c2.number_input(tr("Max Correlated Trades"),1,20,lim.max_correlated_trades,1); rr=c3.number_input(tr("Minimum R:R"),.1,20.0,lim.min_rr,.1)
            save=st.form_submit_button(tr("Save risk policy"))
        if save:
            save_setting("risk_limits",asdict(RiskLimits(mr,dl,wl,ml,op,exp,mu,lev,dd,int(ct),int(corr),rr))); st.success(tr("Risk policy saved locally."))
    with tabs[1]:
        st.markdown(tr("### Safety hierarchy"))
        st.markdown(tr("1. Preserve capital  \n2. Limit risk  \n3. Prevent operational errors  \n4. Prevent impulsive execution  \n5. Execute correctly  \n6. Analyze opportunities  \n7. Seek returns"))
        st.info(tr("LIVE is OFF by default and additionally requires the server secret `ENABLE_LIVE_TRADING=true`, configured credentials, an approved/conditional gate, an attached-stop capability, a typed phrase and a one-time code."))
        st.warning(tr("Use exchange API keys with withdrawals disabled and only the minimum futures permissions required. IP restrictions are recommended where the exchange/account supports them."))
        st.caption(tr("The emergency kill switch blocks new orders. Cancel-all requires a separate typed confirmation. It never closes positions automatically."))
    with tabs[2]:
        st.code('''# .streamlit/secrets.toml example — NEVER commit this file
ENABLE_LIVE_TRADING = false
USE_EXCHANGE_SANDBOX = false

BINANCE_API_KEY = "..."
BINANCE_API_SECRET = "..."

BYBIT_API_KEY = "..."
BYBIT_API_SECRET = "..."

OKX_API_KEY = "..."
OKX_API_SECRET = "..."
OKX_API_PASSPHRASE = "..."
''',language="toml")
        st.caption(tr("Secrets are read from environment variables first, then `st.secrets`. They are never rendered, logged or included in the audit payload."))
    with tabs[3]:
        st.markdown(tr("### requirements.txt"))
        st.code("""streamlit>=1.40,<2
ccxt>=4.5
pandas>=2.2
numpy>=2.0
plotly>=5.24
tzdata>=2025.2""",language="text")
        st.markdown(tr("### Local"))
        st.code("python -m pip install -r requirements.txt\nstreamlit run app.py",language="bash")
        st.markdown(tr("### GitHub"))
        st.code("git init\ngit add app.py requirements.txt\ngit commit -m \"Futures Command Center Pro\"\ngit branch -M main\ngit remote add origin <YOUR_REPOSITORY_URL>\ngit push -u origin main",language="bash")
        st.markdown(tr("### Streamlit Cloud"))
        st.write("Create an app from the GitHub repository, set `app.py` as the entry point, paste secrets in the app's Secrets settings, and deploy. The app can open without private API secrets; public market modules remain available.")
        st.warning(tr("SQLite on Streamlit Community Cloud should be treated as ephemeral local persistence. For durable multi-device history, migrate the persistence functions to a durable external store while keeping the adapter inside this same `app.py` if the one-file constraint remains."))
    with tabs[4]:
        st.markdown(tr("### Internal one-file architecture"))
        st.code("""IMPORTS / CONFIG / CSS
DATA MODELS
UTILITIES
SQLITE PERSISTENCE
EXCHANGE ADAPTERS (Binance USD-M / Bybit / OKX)
MARKET DATA + INDICATORS
STRUCTURE / LEVELS / LIQUIDITY
DERIVATIVES / ORDER FLOW
REGIME / CONFLUENCE / SCENARIOS
RISK / POSITION SIZE / STOP / TP / LIQUIDATION
LIVE EXECUTION SAFETY GATE
PAPER ENGINE
PORTFOLIO RISK
BACKTEST / WALK-FORWARD / MONTE CARLO
JOURNAL / ANALYTICS / PLAYBOOK / ALERTS
UI COMPONENTS + PAGES
MAIN APP""",language="text")
        st.caption(tr("All financial scores are rule-based and explainable. Data confidence is distinct from signal strength. Missing data remains missing instead of being invented."))

def sidebar() -> Tuple[str,str,str,str]:
    with st.sidebar:
        st.markdown(f"### ⚡ {APP_NAME}")
        lang_codes=list(LANGUAGES.keys())
        language=st.selectbox("🌐 Idioma / Language",lang_codes,format_func=lambda x: LANGUAGES[x],index=lang_codes.index(st.session_state.get("language","es")),key="language_select")
        st.session_state.language=language
        mode=st.selectbox(tr("OPERATING MODE"),["ANALYSIS ONLY","PAPER","LIVE"],format_func=tr,index=["ANALYSIS ONLY","PAPER","LIVE"].index(st.session_state.mode),key="mode_select")
        st.session_state.mode=mode
        exchange_id=st.selectbox(tr("Exchange"),list(SUPPORTED_EXCHANGES),format_func=lambda x:SUPPORTED_EXCHANGES[x],index=list(SUPPORTED_EXCHANGES).index(st.session_state.exchange_id) if st.session_state.exchange_id in SUPPORTED_EXCHANGES else 0)
        st.session_state.exchange_id=exchange_id
        symbols=[]
        try: symbols=cached_market_symbols(exchange_id)
        except Exception as e:
            info=classify_exchange_error(e)
            if info["code"]=="HOST_REGION_RESTRICTED":
                st.warning(tr("Exchange blocked from this app server region. The app is online; the data endpoint is refusing the host."))
            else:
                st.caption(f"Market list unavailable: {info['code']}")
        if symbols:
            default=st.session_state.symbol if st.session_state.symbol in symbols else next((s for s in symbols if s.startswith("BTC/USDT")),symbols[0])
            symbol=st.selectbox(tr("Contract"),symbols,index=symbols.index(default))
        else:
            symbol=st.text_input(tr("Contract"),st.session_state.symbol or DEFAULT_SYMBOL)
        st.session_state.symbol=symbol
        if exchange_id=="binanceusdm":
            st.caption(tr("📡 Public data: Binance Vision (Spot proxy). Funding/OI: Binance Futures only when reachable. LIVE stays fail-closed and revalidates on the real futures API."))
        tf=st.selectbox(tr("Primary timeframe"),TIMEFRAMES,index=TIMEFRAMES.index(st.session_state.timeframe) if st.session_state.timeframe in TIMEFRAMES else 3)
        st.session_state.timeframe=tf
        st.markdown(tr("---"))
        nav=st.radio(tr("Navigation"),["Command Center","Market / Analysis","Scanner","Trade Builder","Positions / Execution","Risk Center","Journal / Analytics","Backtest","Playbook / Alerts","Data Quality / Health","Configuration"],format_func=tr,key="nav_radio")
        st.markdown(tr("---"))
        if mode=="LIVE": st.error(tr("LIVE · REAL ORDERS"))
        elif mode=="PAPER": st.warning(tr("PAPER · SIMULATION"))
        else: st.info(tr("ANALYSIS ONLY"))
        st.checkbox(tr("Debug diagnostics"),key="debug_mode")
        st.caption(f"v{APP_VERSION} · build {BUILD}")
    return nav,mode,exchange_id,symbol

def main():
    init_db(); init_state()
    nav,mode,exchange_id,symbol=sidebar(); app_header(mode,exchange_id,symbol)
    if ccxt is None:
        st.error(tr("CCXT is not installed. Install requirements before using market data."))
        page_configuration(exchange_id,symbol); return
    try:
        if nav=="Command Center": page_command_center(exchange_id,symbol)
        elif nav=="Market / Analysis": page_market_analysis(exchange_id,symbol)
        elif nav=="Scanner": page_scanner(exchange_id)
        elif nav=="Trade Builder": page_trade_builder(exchange_id,symbol,mode)
        elif nav=="Positions / Execution": page_positions(exchange_id,symbol,mode)
        elif nav=="Risk Center": page_risk_center(exchange_id,mode)
        elif nav=="Journal / Analytics": page_journal_analytics()
        elif nav=="Backtest": page_backtest(exchange_id,symbol)
        elif nav=="Playbook / Alerts": page_playbook_alerts(exchange_id,symbol)
        elif nav=="Data Quality / Health": page_system_health(exchange_id,symbol)
        elif nav=="Configuration": page_configuration(exchange_id,symbol)
    except Exception as e:
        error_box("Unexpected page error",e)
    st.markdown(tr("---"))
    st.caption("Futures Command Center Pro es una herramienta de análisis y gestión de riesgo; no garantiza resultados. Los futuros apalancados pueden generar pérdidas rápidas y significativas. Preferí NO OPERAR cuando los datos, el riesgo, la calidad del setup o la disciplina sean insuficientes." if st.session_state.get("language","es")=="es" else "Futures Command Center Pro is an analysis and risk-management tool, not a guarantee of results. Leveraged crypto futures can cause rapid and significant losses. Prefer NO TRADE whenever data, risk, setup quality or discipline is inadequate.")

if __name__ == "__main__":
    main()
