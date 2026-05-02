import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET

# Configuração da página
st.set_page_config(page_title="BRAI & Macro Monitor", page_icon="📈", layout="centered")

st.title("📊 Monitor de Investimentos (BRAI & Macro)")

# Criando as abas
tab1, tab2, tab3 = st.tabs(["📊 Índice BRAI (Longo Prazo)", "⚡ Curto Prazo (24h)", "📰 Tendências e Macro"])

# ==========================================
# ABA 1: CÁLCULO DO ÍNDICE BRAI (200 DMA)
# ==========================================
with tab1:
    st.subheader("Índice de Ciclo (BRAI - 200 Dias)")
    # [Mantendo sua lógica original de 200 dias para o BRAI]
    def buscar_dados_longo_prazo():
        try:
            btc = yf.Ticker("BTC-USD").history(period="400d")
            usdbrl = yf.Ticker("USDBRL=X").history(period="400d")
            if btc.empty or usdbrl.empty: return None
            
            res = {
                "btc_p": float(btc['Close'].iloc[-1]),
                "btc_200": float(btc['Close'].rolling(window=200).mean().iloc[-1]),
                "dol_a": float(usdbrl['Close'].iloc[-1]),
                "dol_200": float(usdbrl['Close'].rolling(window=200).mean().iloc[-1])
            }
            return res
        except: return None

    if st.button('🔄 Calcular BRAI'):
        d = buscar_dados_longo_prazo()
        if d:
            indice = (d['btc_p']/d['btc_200']) * (d['dol_a']/d['dol_200'])
            st.metric("Índice BRAI Atual", f"{indice:.4f}")
            if indice < 1.0: st.success("Zona de Acumulação de Longo Prazo")
            else: st.warning("Zona de Atenção / Realização")

# ==========================================
# ABA 2: ÍNDICE DE CURTO PRAZO (24 HORAS)
# ==========================================
with tab3: # Reordenado conforme pedido
    pass 

with tab2:
    st.subheader("⚡ Oportunidade Diária (Janela 24h)")
    st.write("Relaciona a mínima do BTC com a mínima do Dólar no dia para achar o 'preço ideal'.")

    def buscar_dados_24h():
        try:
            # Pegando dados de 1 dia com intervalo de 15 minutos para precisão
            btc_24h = yf.download("BTC-USD", period="1d", interval="15m", progress=False)
            usd_24h = yf.download("USDBRL=X", period="1d", interval="15m", progress=False)
            
            if btc_24h.empty or usd_24h.empty: return None

            dados = {
                "btc_atual": float(btc_24h['Close'].iloc[-1]),
                "btc_min_24h": float(btc_24h['Low'].min()),
                "dol_atual": float(usd_24h['Close'].iloc[-1]),
                "dol_min_24h": float(usd_24h['Low'].min()),
            }
            return dados
        except: return None

    if st.button('⚡ Verificar Janela de Compra 24h'):
        with st.spinner('Analisando volatilidade do dia...'):
            d24 = buscar_dados_24h()
            if d24:
                # Distância para a mínima do dia (Quanto menor, melhor a compra)
                dist_btc = (d24['btc_atual'] / d24['btc_min_24h']) - 1
                dist_dol = (d24['dol_atual'] / d24['dol_min_24h']) - 1
                
                # Índice de Proximidade da Mínima (IPM)
                # 0% significa que você está comprando EXATAMENTE no melhor preço do dia.
                ipm = (dist_btc + dist_dol) * 100

                col1, col2 = st.columns(2)
                col1.metric("Preço BTC", f"US$ {d24['btc_atual']:,.2f}", f"Mín: {d24['btc_min_24h']:,.0f}", delta_color="inverse")
                col2.metric("Dólar", f"R$ {d24['dol_atual']:.4f}", f"Mín: {d24['dol_min_24h']:.4f}", delta_color="inverse")

                st.divider()
                st.write(f"**Índice de Proximidade da Mínima (IPM): {ipm:.2f}%**")
                
                if ipm < 0.5:
                    st.success("💎 **OPORTUNIDADE RARA:** Você está comprando quase na mínima simultânea de ambos os ativos!")
                elif ipm < 1.5:
                    st.info("✅ **BOM MOMENTO:** O preço está muito próximo do melhor valor das últimas 24h.")
                else:
                    st.warning("⏳ **AGUARDE:** O preço subiu em relação às mínimas do dia. Pode haver correção em breve.")

                st.caption("Nota: O IPM calcula o desvio combinado entre o preço atual e a mínima de 24h do BTC e do USD/BRL.")

# ==========================================
# ABA 3: TENDÊNCIAS (Notícias com o Fix de Segurança)
# ==========================================
with tab3:
    st.subheader("Radar Macroeconômico")
    # [Código das notícias com o cabeçalho de simulação de navegador do Livecoins]
    # (Inserir aqui a lógica de busca_noticias() anterior)
