import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="BRAI Index Monitor", page_icon="📈")

st.title("📊 BTC Real Adjusted Index (BRAI)")
st.subheader("Versão Web para Investidores Brasileiros")

def buscar_dados():
    try:
        # Usando yf.Ticker em vez de yf.download para maior estabilidade na nuvem
        btc = yf.Ticker("BTC-USD").history(period="400d")
        if btc.empty:
            return None, None, None, None
        
        btc_price = float(btc['Close'].iloc[-1])
        btc_200dma = float(btc['Close'].rolling(window=200).mean().iloc[-1])
        
        usdbrl = yf.Ticker("USDBRL=X").history(period="400d")
        if usdbrl.empty:
            return None, None, None, None
            
        dolar_atual = float(usdbrl['Close'].iloc[-1])
        dolar_200dma = float(usdbrl['Close'].rolling(window=200).mean().iloc[-1])
        
        return btc_price, btc_200dma, dolar_atual, dolar_200dma
        
    except Exception as e:
        # Se der qualquer erro na coleta, ele não quebra o site inteiro
        return None, None, None, None

if st.button('🔄 Atualizar Dados Agora'):
    with st.spinner('Consultando mercado...'):
        btc_p, btc_200, dol_a, dol_200 = buscar_dados()
        
        # Verificação de segurança: checa se os dados vieram vazios
        if btc_p is None:
            st.error("⚠️ Falha na conexão com os dados de mercado. O Yahoo Finance pode estar instável no momento. Tente novamente em alguns instantes.")
        else:
            # Cálculos
            razao_btc = btc_p / btc_200
            razao_dolar = dol_a / dol_200
            indice = razao_btc * razao_dolar
            
            # Dashboard Principal
            col1, col2 = st.columns(2)
            col1.metric("BTC Atual", f"US$ {btc_p:,.2f}")
            col2.metric("USD/BRL", f"R$ {dol_a:.4f}")

            # Estilização do Índice
            st.divider()
            if indice < 0.90:
                st.success(f"### ÍNDICE FINAL: {indice:.4f} \n **MUITO BARATO** (Forte Compra)")
            elif indice < 1.0:
                st.info(f"### ÍNDICE FINAL: {indice:.4f} \n **BARATO** (Bom momento)")
            elif indice < 1.25:
                st.warning(f"### ÍNDICE FINAL: {indice:.4f} \n **CARO / JUSTO** (Atenção)")
            else:
                st.error(f"### ÍNDICE FINAL: {indice:.4f} \n **MUITO CARO** (Venda/Realize)")
            
            # Tabela de Detalhes
            with st.expander("Ver detalhes técnicos"):
                df_info = pd.DataFrame({
                    "Métrica": ["BTC 200 DMA", "Dólar 200 DMA", "Razão BTC", "Razão Dólar"],
                    "Valor": [f"US$ {btc_200:,.2f}", f"R$ {dol_200:.4f}", f"{razao_btc:.4f}", f"{razao_dolar:.4f}"]
                })
                st.table(df_info)
                st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
else:
    st.write("Clique no botão acima para carregar o índice.")
