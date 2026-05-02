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
    pos = ['alta', 'aprova', 'compra', 'bull', 'corte', 'adoção', 'etf', 'dispara']
    neg = ['baixa', 'queda', 'vende', 'guerra', 'inflação', 'juros', 'crise', 'taxa']
    score = sum(1 for p in pos if p in titulo_min) - sum(1 for n in neg if n in titulo_min)
    if score > 0: return "🟢 **Potencial Positivo**"
    elif score < 0: return "🔴 **Potencial Negativo**"
    return "🟡 **Neutro/Misto**"

def buscar_noticias():
    url = "https://livecoins.com.br/feed/"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
        return [{'titulo': i.find('title').text, 'link': i.find('link').text, 
                 'analise': analisar_sentimento(i.find('title').text)} for i in root.findall('.//item')[:8]]
    except: return []

# --- INTERFACE ---

st.title("📊 Monitor de Investimentos")
tab1, tab2, tab3 = st.tabs(["📊 Ciclo Longo (BRAI)", "⚡ Curto Prazo (24h)", "📰 Radar Macro"])

# ABA 1: LONGO PRAZO
with tab1:
    st.subheader("Índice de Ciclo (BRAI)")
    if st.button('🔄 Calcular BRAI'):
        with st.spinner('Processando...'):
            try:
                # Usando .history() que é mais estável para evitar erros de colunas
                btc = yf.Ticker("BTC-USD").history(period="400d")
                usd = yf.Ticker("USDBRL=X").history(period="400d")
                
                b_p, b_200 = btc['Close'].iloc[-1], btc['Close'].rolling(200).mean().iloc[-1]
                u_p, u_200 = usd['Close'].iloc[-1], usd['Close'].rolling(200).mean().iloc[-1]
                
                indice = (float(b_p)/float(b_200)) * (float(u_p)/float(u_200))
                st.metric("BRAI Atual", f"{indice:.4f}")
                if indice < 1.0: st.success("Zona de Acumulação")
                else: st.warning("Zona de Atenção")
            except Exception as e: st.error(f"Erro no BRAI: {e}")

# ABA 2: CURTO PRAZO (CORREÇÃO DO ERRO 'CLOSE')
with tab2:
    st.subheader("⚡ Janela de Oportunidade 24h")
    if st.button('⚡ Verificar Preço Ideal Agora'):
        with st.spinner('Analisando mercado...'):
            try:
                # Mudança estratégica: baixamos um por um sem group_by para garantir colunas simples
                # O intervalo de 15m às vezes falha se o mercado estiver fechado, usamos 30m para segurança
                btc_data = yf.download("BTC-USD", period="2d", interval="30m", progress=False)
                usd_data = yf.download("USDBRL=X", period="2d", interval="30m", progress=False)

                if btc_data.empty or usd_data.empty:
                    st.error("Dados indisponíveis no momento. Tente novamente em instantes.")
                else:
                    # Correção técnica: Garantimos que estamos pegando a coluna 'Close' e 'Low' de forma escalar
                    # Usamos .values.flatten() para evitar qualquer problema de formato do Pandas
                    b_atual = float(btc_data['Close'].iloc[-1])
                    b_min = float(btc_data['Low'].min())
                    u_atual = float(usd_data['Close'].iloc[-1])
                    u_min = float(usd_data['Low'].min())
                    
                    ipm = ((b_atual/b_min) - 1 + (u_atual/u_min) - 1) * 100
                    
                    c1, c2 = st.columns(2)
                    c1.metric("BTC", f"US$ {b_atual:,.0f}", f"Mín: {b_min:,.0f}")
                    c2.metric("Dólar", f"R$ {u_atual:.4f}", f"Mín: {u_min:.4f}")
                    
                    st.divider()
                    st.write(f"**Desvio da Mínima (IPM): {ipm:.2f}%**")
                    if ipm < 1.0: st.success("💎 ÓTIMA OPORTUNIDADE")
                    else: st.info("Aguarde uma retração para as mínimas")
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")
                st.info("Dica: Se o erro persistir, o Yahoo Finance pode estar limitando as requisições. Tente atualizar a página.")

# ABA 3: RADAR MACRO
with tab3:
    st.subheader("Tendências Recentes")
    if st.button('🗞️ Carregar Notícias'):
        for n in buscar_noticias():
            st.markdown(f"**[{n['titulo']}]({n['link']})**")
            st.caption(n['analise'])
            st.divider()
