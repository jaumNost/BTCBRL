import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET

# Configuração da página
st.set_page_config(page_title="BRAI & Macro Monitor", page_icon="📈", layout="centered")

# --- FUNÇÕES DE APOIO (LÓGICA E NOTÍCIAS) ---

def analisar_sentimento(titulo):
    """Analisa o peso das palavras no título para definir o viés macro."""
    titulo_min = titulo.lower()
    peso_positivo = ['alta', 'aprova', 'compra', 'crescimento', 'bull', 'suporte', 'otimismo', 'corte', 'adoção', 'lucro', 'investimento', 'etf', 'dispara', 'avança']
    peso_negativo = ['baixa', 'queda', 'vende', 'processa', 'sec', 'guerra', 'inflação', 'juros', 'hacker', 'crise', 'recessão', 'taxa', 'medo', 'tensão', 'recua', 'foge']
    
    score = sum(1 for p in peso_positivo if p in titulo_min) - sum(1 for n in peso_negativo if n in titulo_min)
    
    if score > 0:
        return "🟢 **Potencial Positivo:** Favorece ativos de risco. O mercado lê como aumento de liquidez ou adoção."
    elif score < 0:
        return "🔴 **Potencial Negativo:** Fatores de incerteza ou aperto monetário. Tende a pressionar o BTC para baixo."
    return "🟡 **Neutro/Misto:** Sem viés direcional forte identificado no título."

def buscar_noticias():
    """Busca notícias via RSS com cabeçalhos para evitar bloqueios de robôs."""
    url = "https://livecoins.com.br/feed/"
    noticias = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        for item in root.findall('.//item')[:10]:
            titulo = item.find('title').text
            link = item.find('link').text
            data_pub = item.find('pubDate').text if item.find('pubDate') is not None else "Data não disponível"
            noticias.append({
                'titulo': titulo, 
                'link': link, 
                'data': data_pub, 
                'analise': analisar_sentimento(titulo)
            })
        return noticias
    except Exception as e:
        return []

# --- INTERFACE PRINCIPAL ---

st.title("📊 Monitor de Investimentos")
tab1, tab2, tab3 = st.tabs(["📊 Ciclo Longo (BRAI)", "⚡ Curto Prazo (24h)", "📰 Radar Macro"])

# ABA 1: LONGO PRAZO (ÍNDICE BRAI)
with tab1:
    st.subheader("Índice de Ciclo (Média de 200 Dias)")
    st.write("Ideal para identificar zonas de acumulação estratégica em horizontes de longo prazo.")
    
    if st.button('🔄 Calcular Índice BRAI'):
        with st.spinner('Puxando dados históricos (400 dias)...'):
            try:
                btc = yf.Ticker("BTC-USD").history(period="400d")
                usd = yf.Ticker("USDBRL=X").history(period="400d")
                
                if btc.empty or usd.empty:
                    st.error("Falha ao obter dados do Yahoo Finance.")
                else:
                    btc_p = float(btc['Close'].iloc[-1])
                    btc_200 = float(btc['Close'].rolling(window=200).mean().iloc[-1])
                    usd_p = float(usd['Close'].iloc[-1])
                    usd_200 = float(usd['Close'].rolling(window=200).mean().iloc[-1])
                    
                    indice = (btc_p / btc_200) * (usd_p / usd_200)
                    
                    st.metric("BRAI Atual", f"{indice:.4f}")
                    
                    if indice < 1.0:
                        st.success("💎 **ZONA DE ACUMULAÇÃO:** Preço ajustado está abaixo da média histórica.")
                    elif indice < 1.25:
                        st.warning("🟡 **PREÇO JUSTO/CARO:** Considere cautela em novas entradas.")
                    else:
                        st.error("🔴 **EXTREMO ESTICADO:** Risco de correção elevado.")
            except Exception as e:
                st.error(f"Erro no cálculo de longo prazo: {e}")

# ABA 2: CURTO PRAZO (VOLATILIDADE DIÁRIA)
with tab2:
    st.subheader("⚡ Janela de Oportunidade 24h")
    st.write("Compara o preço atual com as mínimas do dia para identificar o melhor momento de entrada imediata.")
    
    if st.button('⚡ Verificar Preço Ideal Agora'):
        with st.spinner('Analisando mínimas de 24h...'):
            try:
                # Download garantindo dados de 15 min para precisão
                btc_24 = yf.download("BTC-USD", period="2d", interval="15m", progress=False, group_by='ticker')
                usd_24 = yf.download("USDBRL=X", period="2d", interval="15m", progress=False, group_by='ticker')
                
                # Extração forçada para float para evitar erro de Series format
                b_atual = float(btc_24['Close'].iloc[-1])
                b_min = float(btc_24['Low'].min())
                u_atual = float(usd_24['Close'].iloc[-1])
                u_min = float(usd_24['Low'].min())
                
                # Cálculo do Índice de Desvio da Mínima
                ipm = ((b_atual/b_min) - 1 + (u_atual/u_min) - 1) * 100
                
                col1, col2 = st.columns(2)
                col1.metric("BTC", f"US$ {b_atual:,.2f}", f"Mín: {b_min:,.2f}", delta_color="inverse")
                col2.metric("Dólar", f"R$ {u_atual:.4f}", f"Mín: {u_min:.4f}", delta_color="inverse")
                
                st.divider()
                st.markdown(f"### Índice de Desvio da Mínima: **{ipm:.2f}%**")
                
                if ipm < 0.8:
                    st.success("💎 **OPORTUNIDADE DIÁRIA:** Preço excelente em relação ao fundo do dia.")
                elif ipm < 2.0:
                    st.info("✅ **MOMENTO ADEQUADO:** Desvio pequeno, entrada ainda competitiva.")
                else:
                    st.warning("⏳ **AGUARDE:** O preço já subiu consideravelmente desde a mínima do dia.")
            except Exception as e:
                st.error(f"Erro ao processar dados de 24h: {e}")

# ABA 3: RADAR MACRO (NOTÍCIAS)
with tab3:
    st.subheader("Radar de Tendências")
    st.write("Fatores macroeconômicos e notícias recentes que impactam o apetite ao risco.")
    
    if st.button('🗞️ Carregar Notícias Recentes'):
        with st.spinner('Varrendo portais financeiros...'):
            noticias = buscar_noticias()
            if not noticias:
                st.error("Não foi possível carregar o feed de notícias. Tente novamente em instantes.")
            else:
                for n in noticias:
                    with st.container():
                        st.markdown(f"#### [{n['titulo']}]({n['link']})")
                        st.caption(f"📅 {n['data']}")
                        st.info(n['analise'])
                        st.divider()
