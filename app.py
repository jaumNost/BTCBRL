import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET

# Configuração da página
st.set_page_config(page_title="BRAI & Macro Monitor", page_icon="📈", layout="centered")

# --- FUNÇÕES DE APOIO ---

def analisar_sentimento(titulo):
    titulo_min = titulo.lower()
    peso_positivo = ['alta', 'aprova', 'compra', 'crescimento', 'bull', 'suporte', 'otimismo', 'corte', 'adoção', 'lucro', 'investimento', 'etf', 'dispara', 'avança']
    peso_negativo = ['baixa', 'queda', 'vende', 'processa', 'sec', 'guerra', 'inflação', 'juros', 'hacker', 'crise', 'recessão', 'taxa', 'medo', 'tensão', 'recua', 'foge']
    score = sum(1 for p in peso_positivo if p in titulo_min) - sum(1 for n in peso_negativo if n in titulo_min)
    
    if score > 0: return "🟢 **Potencial Positivo:** Favorece ativos de risco (BTC)."
    elif score < 0: return "🔴 **Potencial Negativo:** Tende a pressionar o preço para baixo."
    return "🟡 **Neutro/Misto:** Sem viés direcional forte."

def buscar_noticias():
    url = "https://livecoins.com.br/feed/"
    noticias = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
        for item in root.findall('.//item')[:10]:
            titulo = item.find('title').text
            link = item.find('link').text
            data_pub = item.find('pubDate').text if item.find('pubDate') is not None else ""
            noticias.append({'titulo': titulo, 'link': link, 'data': data_pub, 'analise': analisar_sentimento(titulo)})
        return noticias
    except: return []

# --- INTERFACE ---

st.title("📊 Monitor de Investimentos")
tab1, tab2, tab3 = st.tabs(["📊 Ciclo Longo (BRAI)", "⚡ Curto Prazo (24h)", "📰 Radar Macro"])

# ABA 1: LONGO PRAZO
with tab1:
    st.subheader("Índice BRAI (Média de 200 Dias)")
    if st.button('🔄 Calcular Índice de Ciclo'):
        with st.spinner('Puxando dados históricos...'):
            try:
                btc = yf.Ticker("BTC-USD").history(period="400d")
                usd = yf.Ticker("USDBRL=X").history(period="400d")
                
                btc_p, btc_200 = btc['Close'].iloc[-1], btc['Close'].rolling(200).mean().iloc[-1]
                usd_p, usd_200 = usd['Close'].iloc[-1], usd['Close'].rolling(200).mean().iloc[-1]
                
                indice = (btc_p / btc_200) * (usd_p / usd_200)
                
                st.metric("BRAI Atual", f"{indice:.4f}")
                if indice < 1.0: st.success("Ponto de Acumulação Estratégica")
                else: st.warning("Atenção: Preço acima da média histórica")
            except: st.error("Erro ao carregar dados de longo prazo.")

# ABA 2: CURTO PRAZO (A que você clicou e não funcionou)
with tab2:
    st.subheader("⚡ Janela de Oportunidade 24h")
    st.write("Busca o melhor momento do dia combinando as mínimas de BTC e Dólar.")
    
    if st.button('⚡ Verificar Preço Ideal agora'):
        with st.spinner('Analisando mínimas do dia...'):
            try:
                # Mudança para '5d' para garantir que o Yahoo sempre retorne dados recentes
                btc_24 = yf.download("BTC-USD", period="2d", interval="15m", progress=False)
                usd_24 = yf.download("USDBRL=X", period="2d", interval="15m", progress=False)
                
                b_atual, b_min = btc_24['Close'].iloc[-1], btc_24['Low'].min()
                u_atual, u_min = usd_24['Close'].iloc[-1], usd_24['Low'].min()
                
                ipm = ((b_atual/b_min) - 1 + (u_atual/u_min) - 1) * 100
                
                c1, c2 = st.columns(2)
                c1.metric("BTC", f"US$ {b_atual:,.0f}", f"Mín: {b_min:,.0f}")
                c2.metric("Dólar", f"R$ {u_atual:.3f}", f"Mín: {u_min:.3f}")
                
                st.divider()
                st.write(f"**Desvio da Mínima Combinada: {ipm:.2f}%**")
                
                if ipm < 0.8: st.success("💎 **COMPRA IMEDIATA:** Preços muito próximos da mínima diária.")
                elif ipm < 2.0: st.info("✅ **PREÇO BOM:** Pequeno desvio do fundo do dia.")
                else: st.warning("⏳ **AGUARDE:** O preço esticou. Tente comprar mais perto das mínimas.")
            except Exception as e:
                st.error(f"Erro ao calcular 24h: {e}")

# ABA 3: NOTÍCIAS
with tab3:
    st.subheader("Tendências de Mercado")
    if st.button('🗞️ Carregar Últimas Notícias'):
        with st.spinner('Lendo portais...'):
            noticias = buscar_noticias()
            if not noticias: st.warning("Não foi possível acessar o portal de notícias.")
            for n in noticias:
                st.markdown(f"**[{n['titulo']}]({n['link']})**")
                st.caption(n['analise'])
                st.divider()
