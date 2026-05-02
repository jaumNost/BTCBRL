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
tab1, tab2 = st.tabs(["📊 Índice BRAI (Preço)", "📰 Tendências e Macro (Notícias)"])

# ==========================================
# ABA 1: CÁLCULO DO ÍNDICE BRAI
# ==========================================
with tab1:
    st.subheader("BTC Real Adjusted Index (BRAI)")

    def buscar_dados():
        try:
            btc = yf.Ticker("BTC-USD").history(period="400d")
            if btc.empty: return None, None, None, None
            
            btc_price = float(btc['Close'].iloc[-1])
            btc_200dma = float(btc['Close'].rolling(window=200).mean().iloc[-1])
            
            usdbrl = yf.Ticker("USDBRL=X").history(period="400d")
            if usdbrl.empty: return None, None, None, None
                
            dolar_atual = float(usdbrl['Close'].iloc[-1])
            dolar_200dma = float(usdbrl['Close'].rolling(window=200).mean().iloc[-1])
            
            return btc_price, btc_200dma, dolar_atual, dolar_200dma
        except Exception:
            return None, None, None, None

    if st.button('🔄 Atualizar Índice Agora'):
        with st.spinner('Consultando mercado...'):
            btc_p, btc_200, dol_a, dol_200 = buscar_dados()
            
            if btc_p is None:
                st.error("⚠️ Falha na conexão com os dados do Yahoo Finance.")
            else:
                razao_btc = btc_p / btc_200
                razao_dolar = dol_a / dol_200
                indice = razao_btc * razao_dolar
                
                col1, col2 = st.columns(2)
                col1.metric("BTC Atual", f"US$ {btc_p:,.2f}")
                col2.metric("USD/BRL", f"R$ {dol_a:.4f}")

                st.divider()
                if indice < 0.90:
                    st.success(f"### ÍNDICE FINAL: {indice:.4f} \n **MUITO BARATO** (Forte Compra)")
                elif indice < 1.0:
                    st.info(f"### ÍNDICE FINAL: {indice:.4f} \n **BARATO** (Bom momento)")
                elif indice < 1.25:
                    st.warning(f"### ÍNDICE FINAL: {indice:.4f} \n **CARO / JUSTO** (Atenção)")
                else:
                    st.error(f"### ÍNDICE FINAL: {indice:.4f} \n **MUITO CARO** (Venda/Realize)")
                
                with st.expander("Ver detalhes técnicos"):
                    df_info = pd.DataFrame({
                        "Métrica": ["BTC 200 DMA", "Dólar 200 DMA", "Razão BTC", "Razão Dólar"],
                        "Valor": [f"US$ {btc_200:,.2f}", f"R$ {dol_200:.4f}", f"{razao_btc:.4f}", f"{razao_dolar:.4f}"]
                    })
                    st.table(df_info)
    else:
        st.write("Clique no botão para carregar o índice financeiro.")

# ==========================================
# ABA 2: TENDÊNCIAS E MACROECONOMIA
# ==========================================
with tab2:
    st.subheader("Radar Macroeconômico e Cripto")
    st.write("Últimas notícias do mercado com análise rápida de sentimento.")

    def analisar_sentimento(titulo):
        titulo_min = titulo.lower()
        
        peso_positivo = ['alta', 'aprova', 'compra', 'crescimento', 'bull', 'suporte', 'otimismo', 'corte', 'adoção', 'lucro', 'investimento', 'etf', 'dispara', 'avança']
        peso_negativo = ['baixa', 'queda', 'vende', 'processa', 'sec', 'guerra', 'inflação', 'juros', 'hacker', 'crise', 'recessão', 'taxa', 'medo', 'tensão', 'recua', 'foge']
        
        score = 0
        for p in peso_positivo:
            if p in titulo_min: score += 1
        for n in peso_negativo:
            if n in titulo_min: score -= 1
            
        if score > 0:
            return "🟢 **Potencial Positivo:** O mercado costuma ler isso como injeção de liquidez ou aumento de adoção. Tende a favorecer ativos de risco como o BTC."
        elif score < 0:
            return "🔴 **Potencial Negativo:** Fatores ligados a aperto monetário (juros/inflação) ou incerteza (guerras/regulação). Tende a tirar dinheiro do BTC para ativos mais seguros."
        else:
            return "🟡 **Neutro/Misto:** Notícia de impacto local ou sem viés direcional forte imediato para o macro."

    def buscar_noticias():
        # Trocamos para o Livecoins (muito bom e com feed mais aberto)
        url = "https://livecoins.com.br/feed/"
        noticias = []
        try:
            # Simulando um navegador real (Chrome no Windows) para evitar bloqueios
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Pega as 10 notícias mais recentes
            for item in root.findall('.//item')[:10]:
                titulo = item.find('title').text
                link = item.find('link').text
                
                # Prevenção extra caso alguma notícia venha sem data
                data_element = item.find('pubDate')
                data_pub = data_element.text if data_element is not None else "Data não informada"
                
                analise = analisar_sentimento(titulo)
                noticias.append({'titulo': titulo, 'link': link, 'data': data_pub, 'analise': analise})
            return noticias
        except Exception as e:
            # Caso ainda dê erro, ele vai imprimir na tela exatamente o que falhou para podermos consertar
            st.error(f"Erro técnico detalhado: {e}")
            return []

    if st.button('🗞️ Buscar Notícias Recentes'):
        with st.spinner('Varrendo portais financeiros...'):
            lista_noticias = buscar_noticias()
            
            if not lista_noticias:
                st.error("Não foi possível carregar as notícias no momento. Os portais podem estar instáveis.")
            else:
                for noti in lista_noticias:
                    with st.container():
                        st.markdown(f"#### [{noti['titulo']}]({noti['link']})")
                        st.caption(f"📅 Publicado em: {noti['data']}")
                        st.info(noti['analise'])
                        st.divider()
    else:
        st.write("Clique no botão para varrer a rede por notícias macroeconômicas.")
