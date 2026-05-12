import time
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False


# =========================================================
# Configuração da página
# =========================================================

st.set_page_config(
    page_title="jaumNost metodo",
    page_icon="₿",
    layout="wide"
)


# =========================================================
# CSS estilo GitHub Dark
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #f0f6fc;
    }

    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #f0f6fc;
    }

    .main-title {
        font-size: 56px;
        font-weight: 800;
        text-align: center;
        color: #f0f6fc;
        margin-bottom: 8px;
    }

    .subtitle {
        text-align: center;
        color: #8b949e;
        font-size: 17px;
        margin-bottom: 28px;
    }

    .github-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }

    .metric-label {
        color: #8b949e;
        font-size: 14px;
        margin-bottom: 4px;
    }

    .metric-value {
        color: #f0f6fc;
        font-size: 28px;
        font-weight: 700;
    }

    .positive {
        color: #3fb950;
        font-weight: 700;
    }

    .negative {
        color: #f85149;
        font-weight: 700;
    }

    .neutral {
        color: #58a6ff;
        font-weight: 700;
    }

    .warning-box {
        background-color: #161b22;
        border: 1px solid #f0883e;
        border-left: 5px solid #f0883e;
        border-radius: 12px;
        padding: 16px;
        color: #f0f6fc;
        margin-top: 18px;
        margin-bottom: 18px;
    }

    .stButton > button {
        background-color: #238636;
        color: white;
        border: 1px solid #2ea043;
        border-radius: 10px;
        padding: 0.7rem 1.2rem;
        font-weight: 700;
        transition: 0.2s ease-in-out;
    }

    .stButton > button:hover {
        background-color: #2ea043;
        color: white;
        border: 1px solid #3fb950;
        transform: translateY(-1px);
    }

    div[data-testid="stMetricValue"] {
        color: #f0f6fc;
    }

    div[data-testid="stMetricLabel"] {
        color: #8b949e;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 10px 18px;
        color: #f0f6fc;
    }

    .stTabs [aria-selected="true"] {
        background-color: #21262d;
        border-color: #58a6ff;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Constantes
# =========================================================

BINANCE_BASE_URL = "https://api.binance.com"
AWESOME_API_URL = "https://economia.awesomeapi.com.br/json/last/USD-BRL"


# =========================================================
# Funções de API
# =========================================================

@st.cache_data(ttl=30)
def get_binance_klines(symbol="BTCUSDT", interval="1m", limit=300):
    """
    Busca candles da Binance.

    interval exemplos:
    - 1m
    - 5m
    - 15m
    - 1h
    - 1d
    """
    url = f"{BINANCE_BASE_URL}/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()

    data = response.json()

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore"
    ]

    df = pd.DataFrame(data, columns=columns)

    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_volume",
        "taker_buy_quote_volume"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    return df


@st.cache_data(ttl=60)
def get_usd_brl():
    """
    Busca cotação atual USD/BRL pela AwesomeAPI.
    """
    response = requests.get(AWESOME_API_URL, timeout=12)
    response.raise_for_status()

    data = response.json()
    usd_brl = float(data["USDBRL"]["bid"])

    return usd_brl


# =========================================================
# Indicadores técnicos
# =========================================================

def calculate_indicators(df):
    """
    Calcula indicadores técnicos clássicos.
    """
    df = df.copy()

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # Médias móveis
    df["sma_9"] = close.rolling(9).mean()
    df["sma_21"] = close.rolling(21).mean()
    df["sma_50"] = close.rolling(50).mean()

    df["ema_9"] = close.ewm(span=9, adjust=False).mean()
    df["ema_21"] = close.ewm(span=21, adjust=False).mean()
    df["ema_50"] = close.ewm(span=50, adjust=False).mean()

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Bandas de Bollinger
    df["bb_mid"] = close.rolling(20).mean()
    df["bb_std"] = close.rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - 2 * df["bb_std"]

    # Volume médio
    df["volume_sma_20"] = volume.rolling(20).mean()

    # Volatilidade recente
    df["returns"] = close.pct_change()
    df["volatility_20"] = df["returns"].rolling(20).std()

    # Suporte e resistência simples
    df["support_30"] = low.rolling(30).min()
    df["resistance_30"] = high.rolling(30).max()

    # Momentum
    df["momentum_10"] = close - close.shift(10)

    # Corpo do candle
    df["candle_body"] = df["close"] - df["open"]
    df["candle_range"] = df["high"] - df["low"]

    return df


# =========================================================
# Lógica educacional de previsão
# =========================================================

def predict_next_5_minutes(df):
    """
    Gera uma análise probabilística educacional.

    A ideia é combinar sinais técnicos em uma pontuação.
    Isso NÃO é recomendação financeira.
    """

    df = calculate_indicators(df)
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    score = 0
    max_score = 0
    reasons = []

    price = latest["close"]

    # 1. Tendência por médias móveis
    max_score += 2
    if latest["ema_9"] > latest["ema_21"]:
        score += 2
        reasons.append("EMA 9 acima da EMA 21, sugerindo tendência curta positiva.")
    else:
        score -= 2
        reasons.append("EMA 9 abaixo da EMA 21, sugerindo tendência curta negativa.")

    # 2. Cruzamento de médias
    max_score += 2
    if previous["ema_9"] <= previous["ema_21"] and latest["ema_9"] > latest["ema_21"]:
        score += 2
        reasons.append("Cruzamento recente de médias para cima.")
    elif previous["ema_9"] >= previous["ema_21"] and latest["ema_9"] < latest["ema_21"]:
        score -= 2
        reasons.append("Cruzamento recente de médias para baixo.")
    else:
        reasons.append("Sem cruzamento recente relevante entre EMA 9 e EMA 21.")

    # 3. RSI
    max_score += 2
    rsi = latest["rsi"]

    if rsi < 30:
        score += 2
        reasons.append("RSI abaixo de 30, possível sobrevenda.")
    elif rsi > 70:
        score -= 2
        reasons.append("RSI acima de 70, possível sobrecompra.")
    elif 50 <= rsi <= 70:
        score += 1
        reasons.append("RSI em zona positiva moderada.")
    elif 30 <= rsi < 50:
        score -= 1
        reasons.append("RSI em zona fraca moderada.")

    # 4. MACD
    max_score += 2
    if latest["macd"] > latest["macd_signal"]:
        score += 2
        reasons.append("MACD acima da linha de sinal.")
    else:
        score -= 2
        reasons.append("MACD abaixo da linha de sinal.")

    # 5. Histograma MACD melhorando ou piorando
    max_score += 1
    if latest["macd_hist"] > previous["macd_hist"]:
        score += 1
        reasons.append("Histograma do MACD está melhorando.")
    else:
        score -= 1
        reasons.append("Histograma do MACD está enfraquecendo.")

    # 6. Bandas de Bollinger
    max_score += 2
    if price <= latest["bb_lower"]:
        score += 2
        reasons.append("Preço próximo ou abaixo da banda inferior de Bollinger.")
    elif price >= latest["bb_upper"]:
        score -= 2
        reasons.append("Preço próximo ou acima da banda superior de Bollinger.")
    else:
        reasons.append("Preço dentro das Bandas de Bollinger.")

    # 7. Volume
    max_score += 1
    if latest["volume"] > latest["volume_sma_20"]:
        if latest["candle_body"] > 0:
            score += 1
            reasons.append("Volume acima da média com candle positivo.")
        else:
            score -= 1
            reasons.append("Volume acima da média com candle negativo.")
    else:
        reasons.append("Volume abaixo ou próximo da média recente.")

    # 8. Suporte e resistência
    max_score += 2
    distance_to_support = abs(price - latest["support_30"]) / price
    distance_to_resistance = abs(latest["resistance_30"] - price) / price

    if distance_to_support < 0.002:
        score += 2
        reasons.append("Preço próximo de suporte recente.")
    elif distance_to_resistance < 0.002:
        score -= 2
        reasons.append("Preço próximo de resistência recente.")
    else:
        reasons.append("Preço distante dos suportes e resistências imediatos.")

    # 9. Momentum
    max_score += 2
    if latest["momentum_10"] > 0:
        score += 2
        reasons.append("Momentum dos últimos candles está positivo.")
    else:
        score -= 2
        reasons.append("Momentum dos últimos candles está negativo.")

    # 10. Candle atual
    max_score += 1
    if latest["candle_body"] > 0:
        score += 1
        reasons.append("Último candle fechou positivo.")
    else:
        score -= 1
        reasons.append("Último candle fechou negativo.")

    # Normalização da pontuação
    normalized = score / max_score if max_score else 0

    if normalized >= 0:
        direction = "Maior chance de subir"
        probability = 50 + abs(normalized) * 35
    else:
        direction = "Maior chance de descer"
        probability = 50 + abs(normalized) * 35

    probability = min(probability, 85)

    abs_norm = abs(normalized)

    if abs_norm < 0.25:
        confidence = "Baixa"
    elif abs_norm < 0.55:
        confidence = "Média"
    else:
        confidence = "Alta"

    return {
        "direction": direction,
        "probability": probability,
        "confidence": confidence,
        "score": score,
        "max_score": max_score,
        "normalized": normalized,
        "reasons": reasons,
        "latest": latest
    }


# =========================================================
# Gráfico
# =========================================================

def make_candlestick_chart(df):
    """
    Cria gráfico de candles com médias móveis.
    """
    df = calculate_indicators(df)

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["open_time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="BTC/USDT",
            increasing_line_color="#3fb950",
            decreasing_line_color="#f85149"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["open_time"],
            y=df["ema_9"],
            mode="lines",
            name="EMA 9",
            line=dict(color="#58a6ff", width=1.4)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["open_time"],
            y=df["ema_21"],
            mode="lines",
            name="EMA 21",
            line=dict(color="#d29922", width=1.4)
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#f0f6fc"),
        height=620,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor="#161b22",
            bordercolor="#30363d",
            borderwidth=1
        ),
        title=dict(
            text="Gráfico BTC/USDT em tempo quase real",
            font=dict(size=22, color="#f0f6fc")
        )
    )

    fig.update_xaxes(
        gridcolor="#30363d",
        zerolinecolor="#30363d"
    )

    fig.update_yaxes(
        gridcolor="#30363d",
        zerolinecolor="#30363d"
    )

    return fig


# =========================================================
# Longo prazo
# =========================================================

def calculate_long_term_index():
    """
    Calcula índice simples de valuation.

    Fórmula principal:
    índice = preço_atual_btc_brl / média_365_dias_btc_brl

    Como aproximação:
    - preço_atual_btc_brl = BTC atual em USDT * USD/BRL atual
    - média_365_dias_btc_brl = média de fechamento dos últimos 365 dias em USDT * USD/BRL atual

    Observação:
    O ideal seria usar uma série histórica completa de USD/BRL.
    Para simplificar e manter o app leve, usamos a cotação atual do dólar
    como aproximação cambial.
    """

    daily_df = get_binance_klines(
        symbol="BTCUSDT",
        interval="1d",
        limit=365
    )

    usd_brl = get_usd_brl()

    btc_current_usd = float(daily_df.iloc[-1]["close"])
    btc_avg_365_usd = float(daily_df["close"].mean())

    btc_current_brl = btc_current_usd * usd_brl
    btc_avg_365_brl = btc_avg_365_usd * usd_brl

    index = btc_current_brl / btc_avg_365_brl

    if index < 0.9:
        interpretation = "Bitcoin aparentemente barato"
        color_class = "positive"
    elif index <= 1.1:
        interpretation = "Bitcoin próximo do preço justo"
        color_class = "neutral"
