import streamlit as st
import pandas as pd
import requests
import sqlite3
from datetime import datetime
import json
import os
import mock_data

# =========================================
# CONFIGURAÇÃO DE PÁGINA
# =========================================
st.set_page_config(
    page_title="Trader LD PRO",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para visual Premium e Dark/Trading
st.markdown("""
<style>
    /* Importando fonte Outfit do Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Cabeçalho Gradiente */
    .title-gradient {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    
    /* Efeito de Card com Vidro (Glassmorphism) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        backdrop-filter: blur(8px) !important;
        margin-bottom: 20px !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        transform: translateY(-2px);
        border-color: rgba(146, 254, 157, 0.3) !important;
    }
    
    /* Ajuste de métricas */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    
    /* Badges coloridas */
    .badge-green {
        background-color: rgba(0, 230, 118, 0.15);
        color: #00e676;
        border: 1px solid rgba(0, 230, 118, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .badge-red {
        background-color: rgba(255, 23, 68, 0.15);
        color: #ff1744;
        border: 1px solid rgba(255, 23, 68, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .badge-gold {
        background-color: rgba(255, 214, 0, 0.15);
        color: #ffd600;
        border: 1px solid rgba(255, 214, 0, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    /* Estilo de botões de Ação */
    .stButton>button {
        width: 100%;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================
# BANCO DE DADOS (Conexão Segura com context manager e Migração)
# =========================================
DB_NAME = "trader_ld.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            jogo TEXT,
            odd REAL,
            stake REAL,
            responsabilidade REAL,
            resultado TEXT,
            lucro REAL
        )
        """)
        
        # Migração segura: Adicionar coluna liga se ela não existir
        try:
            cursor.execute("ALTER TABLE operacoes ADD COLUMN liga TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Coluna já existe
            pass

init_db()

# =========================================
# CONFIGURAÇÃO DE PERSISTÊNCIA DAS CHAVES
# =========================================
CONFIG_FILE = "config.json"

def carregar_configuracao():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "api_football": "SUA_API_FOOTBALL",
        "api_odds": "SUA_API_ODDS",
        "telegram_token": "",
        "telegram_chat_id": ""
    }

def salvar_configuracao(api_football, api_odds, telegram_token, telegram_chat_id):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "api_football": api_football,
                "api_odds": api_odds,
                "telegram_token": telegram_token,
                "telegram_chat_id": telegram_chat_id
            }, f)
    except:
        pass

# =========================================
# SESSION STATE (Inicialização de chaves)
# =========================================
config_carregada = carregar_configuracao()

if "banca" not in st.session_state:
    st.session_state.banca = 1000.0

if "api_mode" not in st.session_state:
    st.session_state.api_mode = "Simulador (Demo)"

if "api_football" not in st.session_state:
    st.session_state.api_football = config_carregada.get("api_football", "SUA_API_FOOTBALL")

if "api_odds" not in st.session_state:
    st.session_state.api_odds = config_carregada.get("api_odds", "SUA_API_ODDS")

if "telegram_token" not in st.session_state:
    st.session_state.telegram_token = config_carregada.get("telegram_token", "")

if "telegram_chat_id" not in st.session_state:
    st.session_state.telegram_chat_id = config_carregada.get("telegram_chat_id", "")

# =========================================
# SIDEBAR - CONFIGURAÇÃO E GESTÃO
# =========================================
st.sidebar.markdown("### ⚙️ Painel de Controle")

# 1. Configurações de API, Conectividade e Telegram
api_expander = st.sidebar.expander("🔌 APIs & Fonte de Dados", expanded=True)
with api_expander:
    api_mode = st.radio(
        "Fonte de Dados",
        ["Simulador (Demo)", "API Real"],
        index=0 if st.session_state.api_mode == "Simulador (Demo)" else 1,
        help="Simulador gera dados reais flutuantes para demonstração sem chaves pagas."
    )
    st.session_state.api_mode = api_mode
    
    if api_mode == "API Real":
        api_football = st.text_input(
            "Football-Data Token",
            value=st.session_state.api_football,
            type="password",
            help="Seu token X-Auth-Token do football-data.org"
        )
        
        api_odds = st.text_input(
            "The Odds API Key",
            value=st.session_state.api_odds,
            type="password",
            help="Sua chave apiKey do the-odds-api.com"
        )
    else:
        api_football = st.session_state.api_football
        api_odds = st.session_state.api_odds
        
    st.markdown("---")
    st.markdown("💬 **Integração Telegram (Opcional)**")
    telegram_token = st.text_input(
        "Telegram Bot Token",
        value=st.session_state.telegram_token,
        type="password",
        help="Token do seu Bot do Telegram (obtido via @BotFather)."
    )
    telegram_chat_id = st.text_input(
        "Telegram Chat ID",
        value=st.session_state.telegram_chat_id,
        help="ID do chat, grupo ou canal de trading que receberá os alertas."
    )
    
    if st.button("💾 Salvar Configurações", use_container_width=True, help="Salva suas chaves de API e Telegram localmente."):
        st.session_state.api_football = api_football
        st.session_state.api_odds = api_odds
        st.session_state.telegram_token = telegram_token
        st.session_state.telegram_chat_id = telegram_chat_id
        salvar_configuracao(api_football, api_odds, telegram_token, telegram_chat_id)
        st.success("Configurações salvas localmente com sucesso!")
        st.rerun()
        
    # Sincronização em tempo real do estado
    st.session_state.api_football = api_football
    st.session_state.api_odds = api_odds
    st.session_state.telegram_token = telegram_token
    st.session_state.telegram_chat_id = telegram_chat_id

# 2. Gestão de Banca
banca_expander = st.sidebar.expander("💰 Gestão de Banca", expanded=True)
with banca_expander:
    banca = st.number_input(
        "Banca Atual (R$)",
        min_value=10.0,
        max_value=1000000.0,
        value=st.session_state.banca,
        step=50.0
    )
    st.session_state.banca = banca

    stake_percentual = st.slider(
        "Stake Recomendada %",
        min_value=1.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="Porcentagem recomendada para Lay ao Empate (geralmente de 2% a 5%)."
    )
    stake_base = banca * (stake_percentual / 100)
    st.caption(f"Stake Base: **R$ {stake_base:.2f}**")

# 3. Parametrização do Modelo de EV+
model_expander = st.sidebar.expander("🧮 Parâmetros do Modelo", expanded=False)
with model_expander:
    media_gols = st.slider(
        "Média de Gols da Liga",
        min_value=1.5,
        max_value=4.5,
        value=2.8,
        step=0.1,
        help="Média histórica de gols da liga. Quanto mais gols, menor a probabilidade de empate."
    )
    st.caption("Fórmula base: Lay Empate EV+ com amortecimento dinâmico.")

# 4. Ações e Reset de Segurança
danger_expander = st.sidebar.expander("⚠️ Configurações de Segurança", expanded=False)
with danger_expander:
    st.warning("Ação irreversível!")
    confirm_reset = st.checkbox("Desejo zerar todo o histórico")
    if st.button("Resetar Histórico", type="secondary"):
        if confirm_reset:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM operacoes")
                conn.commit()
            st.success("Histórico apagado com sucesso!")
            st.rerun()
        else:
            st.error("Marque a caixa de confirmação primeiro!")

# =========================================
# LÓGICA DO MODELO MATEMÁTICO & TELEGRAM
# =========================================
def prob_mercado(odd):
    return round((1 / odd) * 100, 2)

def modelo_empate(media_gols_ajustada):
    # Modelo estatístico linear de gols vs empates ajustado dinamicamente
    prob = 35.0
    prob -= (media_gols_ajustada - 2) * 10.0
    prob = max(5.0, min(prob, 40.0))
    return round(prob, 2)

def calcular_ev(stake, odd, p_modelo):
    p_red = p_modelo / 100
    p_green = 1 - p_red
    lucro = stake
    loss = stake * (odd - 1)
    ev = (p_green * lucro) - (p_red * loss)
    return round(ev, 2)

def stake_ajustada(stake, odd):
    # Gerenciamento de risco: Reduzir stake em odds excessivamente altas
    if odd >= 7.0:
        return stake * 0.4
    elif odd >= 6.0:
        return stake * 0.6
    elif odd >= 5.0:
        return stake * 0.8
    return stake

def enviar_alerta_telegram(token, chat_id, mensagem):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

# =========================================
# TÍTULO E SUBTÍTULO
# =========================================
st.markdown('<h1 class="title-gradient">📈 Trader LD PRO</h1>', unsafe_allow_html=True)
st.caption("Lay ao Empate (LD) EV+ • Inteligência Quantitativa e Gestão Avançada")
st.write("")

# =========================================
# CARREGAMENTO E ANÁLISE DE HISTÓRICO
# =========================================
with sqlite3.connect(DB_NAME) as conn:
    historico = pd.read_sql_query("SELECT * FROM operacoes ORDER BY id ASC", conn)

greens = len(historico[historico["resultado"] == "GREEN"])
reds = len(historico[historico["resultado"] == "RED"])
operacoes_totais = greens + reds

if operacoes_totais > 0:
    winrate = (greens / operacoes_totais) * 100
    lucro_total = historico["lucro"].sum()
    stake_total_acumulada = historico["stake"].sum()
    roi = (lucro_total / stake_total_acumulada) * 100 if stake_total_acumulada > 0 else 0.0
else:
    winrate = 0.0
    lucro_total = 0.0
    roi = 0.0

# =========================================
# DASHBOARD DE KPIS GERAIS
# =========================================
kpi_cols = st.columns(5)

kpi_cols[0].metric(
    "💰 Banca Atual",
    f"R$ {banca:.2f}",
    help="Sua banca de trading configurada na barra lateral."
)
kpi_cols[1].metric(
    "📈 Lucro Acumulado",
    f"R$ {lucro_total:+.2f}",
    delta=f"{lucro_total:+.2f} R$",
    delta_color="normal" if lucro_total >= 0 else "inverse",
    help="Resultado líquido total de todas as entradas salvas."
)
kpi_cols[2].metric(
    "✅ Greens / ❌ Reds",
    f"{greens} G / {reds} R",
    help="Relação de entradas vencedoras e perdedoras."
)
kpi_cols[3].metric(
    "🎯 Winrate",
    f"{winrate:.1f}%",
    help="Percentual de vitórias com base no histórico gravado."
)
kpi_cols[4].metric(
    "📊 ROI do Histórico",
    f"{roi:+.1f}%",
    help="Retorno sobre o capital total investido (Stake Total)."
)

st.write("")

# =========================================
# SISTEMA DE ABAS (Layout Premium)
# =========================================
tab_feed, tab_calculator, tab_insights = st.tabs([
    "⚽ Monitor de Oportunidades EV+",
    "🧮 Calculadora de Cashout & Hedging",
    "📊 Estatísticas & Insights"
])

# =========================================
# ABA 1: MONITOR DE OPORTUNIDADES
# =========================================
with tab_feed:
    
    # Exibir gráficos analíticos e histórico de forma expansiva
    if operacoes_totais > 0:
        graph_cols = st.columns([7, 3])
        
        with graph_cols[0]:
            st.subheader("📈 Curva de Crescimento (Lucro Acumulado)")
            # Calculando o lucro acumulado passo a passo
            historico_acumulado = historico.copy()
            historico_acumulado["lucro_acumulado"] = historico_acumulado["lucro"].cumsum()
            
            # Inserindo ponto de partida zero para o gráfico ficar bonito
            ponto_inicial = pd.DataFrame([{
                "id": 0, "data": "Início", "jogo": "Capital Inicial", "liga": "START",
                "odd": 0.0, "stake": 0.0, "responsabilidade": 0.0,
                "resultado": "START", "lucro": 0.0, "lucro_acumulado": 0.0
            }])
            df_plot = pd.concat([ponto_inicial, historico_acumulado], ignore_index=True)
            
            # Gráfico Streamlit Line Chart elegante
            st.line_chart(
                data=df_plot,
                x="id",
                y="lucro_acumulado",
                color="#00C9FF",
                use_container_width=True
            )
            
        with graph_cols[1]:
            st.subheader("📊 Resumo Operacional")
            media_odd_green = historico[historico["resultado"] == "GREEN"]["odd"].mean()
            media_odd_green = media_odd_green if not pd.isna(media_odd_green) else 0.0
            
            media_odd_red = historico[historico["resultado"] == "RED"]["odd"].mean()
            media_odd_red = media_odd_red if not pd.isna(media_odd_red) else 0.0
            
            avg_stake = historico["stake"].mean()
            avg_stake = avg_stake if not pd.isna(avg_stake) else 0.0
            
            st.markdown(f"""
            <div style="background-color: rgba(255,255,255,0.03); padding: 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                <p style="margin-bottom: 8px;"><strong>Métricas Operacionais Estendidas:</strong></p>
                <hr style="margin: 8px 0; border-color: rgba(255,255,255,0.1);">
                <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
                    <span>Odd Média de Entrada:</span>
                    <span class="badge-gold">{historico["odd"].mean():.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
                    <span>Odd Média nos Greens:</span>
                    <span class="badge-green">{media_odd_green:.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
                    <span>Odd Média nos Reds:</span>
                    <span class="badge-red">{media_odd_red:.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 6px;">
                    <span>Stake Média Utilizada:</span>
                    <span style="font-weight:bold;">R$ {avg_stake:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            
            # Botão rápido para apagar a última entrada caso o usuário erre
            if st.button("↩️ Excluir Última Operação"):
                if len(historico) > 0:
                    ultimo_id = int(historico.iloc[-1]["id"])
                    with sqlite3.connect(DB_NAME) as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM operacoes WHERE id = ?", (ultimo_id,))
                        conn.commit()
                    st.success("Última operação desfeita!")
                    st.rerun()

        st.write("---")

    # Filtros e Buscas
    st.subheader("⚽ Jogos EV+ Encontrados")
    filter_cols = st.columns([4, 3, 3, 2])
    with filter_cols[0]:
        search_query = st.text_input("🔍 Buscar por Time ou Liga", "", help="Filtre os jogos por nome de time ou campeonato.", key="search_feed")
    with filter_cols[1]:
        min_odd_filter = st.slider("Filtro Odd Mínima do Empate", 2.0, 8.0, 2.5, step=0.1, key="min_odd_feed")
    with filter_cols[2]:
        min_ev_filter = st.slider("Filtro EV Mínimo (R$)", 0.0, 100.0, 0.0, step=1.0, key="min_ev_feed")
    with filter_cols[3]:
        sort_by = st.selectbox(
            "Ordenar por",
            ["Maior EV+", "Maior Edge", "Mais Cedo", "Menor Odd Empate"],
            key="sort_feed"
        )

    # Captura de dados de acordo com a sidebar
    dados = None
    odds_data = None
    
    try:
        if st.session_state.api_mode == "Simulador (Demo)":
            dados, odds_data = mock_data.generate_mock_data()
        else:
            headers = {"X-Auth-Token": st.session_state.api_football}
            session = requests.Session()
            session.trust_env = False
            
            response = session.get(
                "https://api.football-data.org/v4/matches?status=SCHEDULED",
                headers=headers,
                timeout=20
            )
            if response.status_code != 200:
                raise Exception(f"Erro na API Football-Data ({response.status_code}): {response.text}")
            dados = response.json()
            
            odds_url = (
                "https://api.the-odds-api.com/v4/sports/soccer/odds/"
                f"?apiKey={st.session_state.api_odds}"
                "&regions=eu"
                "&markets=h2h"
                "&oddsFormat=decimal"
            )
            odds_response = session.get(odds_url, timeout=20)
            if odds_response.status_code != 200:
                raise Exception(f"Erro na The Odds API ({odds_response.status_code}): {odds_response.text}")
            odds_data = odds_response.json()

        # Mapeamento das Odds
        odds_dict = {}
        for jogo in odds_data:
            try:
                home = jogo["home_team"]
                away = jogo["away_team"]
                nome = f"{home} x {away}"
                odd_draw = None
                
                for bookmaker in jogo["bookmakers"]:
                    for market in bookmaker["markets"]:
                        for outcome in market["outcomes"]:
                            if outcome["name"] == "Draw":
                                odd_draw = outcome["price"]
                
                if odd_draw:
                    odds_dict[nome] = odd_draw
            except:
                pass

        # Filtragem e processamento
        oportunidades = []
        for partida in dados.get("matches", []):
            casa = partida["homeTeam"]["name"]
            fora = partida["awayTeam"]["name"]
            liga = partida["competition"]["name"]
            horario_utc = partida["utcDate"]
            
            try:
                dt = datetime.strptime(horario_utc, "%Y-%m-%dT%H:%M:%SZ")
                horario = dt.strftime("%H:%M")
            except:
                horario = horario_utc[11:16]
                
            jogo = f"{casa} x {fora}"
            odd = None
            
            for nome_odds, odd_valor in odds_dict.items():
                nome_lower = nome_odds.lower()
                if casa.lower() in nome_lower and fora.lower() in nome_lower:
                    odd = odd_valor
                    break
                    
            if not odd:
                continue
                
            p_mercado = prob_mercado(odd)
            p_modelo = modelo_empate(media_gols)
            edge = round(p_mercado - p_modelo, 2)
            
            stake_real = stake_ajustada(stake_base, odd)
            responsabilidade = round(stake_real * (odd - 1), 2)
            ev = calcular_ev(stake_real, odd, p_modelo)
            
            if ev <= 0:
                continue
            if odd < min_odd_filter:
                continue
            if ev < min_ev_filter:
                continue
                
            if search_query:
                q = search_query.lower()
                if q not in casa.lower() and q not in fora.lower() and q not in liga.lower():
                    continue
                    
            oportunidades.append({
                "id": partida["id"],
                "partida": partida,
                "jogo": jogo,
                "liga": liga,
                "horario": horario,
                "odd": odd,
                "p_mercado": p_mercado,
                "p_modelo": p_modelo,
                "edge": edge,
                "stake_real": stake_real,
                "responsabilidade": responsabilidade,
                "ev": ev
            })

        if sort_by == "Maior EV+":
            oportunidades = sorted(oportunidades, key=lambda x: x["ev"], reverse=True)
        elif sort_by == "Maior Edge":
            oportunidades = sorted(oportunidades, key=lambda x: x["edge"], reverse=True)
        elif sort_by == "Mais Cedo":
            oportunidades = sorted(oportunidades, key=lambda x: x["horario"])
        elif sort_by == "Menor Odd Empate":
            oportunidades = sorted(oportunidades, key=lambda x: x["odd"])

        # Display dos Jogos
        if len(oportunidades) == 0:
            st.info("Nenhum jogo EV+ com odds de valor detectado com base nos seus parâmetros atuais.")
        else:
            st.write(f"Exibindo **{len(oportunidades)}** oportunidades de Lay Empate:")
            for op in oportunidades:
                m_id = op["id"]
                
                with st.container(border=True):
                    col_det, col_odds, col_risco = st.columns([3.5, 2, 2.5])
                    
                    with col_det:
                        st.markdown(f"### ⚽ {op['jogo']}")
                        st.markdown(f"🏆 `{op['liga']}` • 🕒 Horário: **{op['horario']}**")
                        
                        st.markdown("""
                        <div style="background-color: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #00C9FF;">
                            🎯 <strong>Entrada:</strong> Próximo aos 10min de jogo (se empatado)<br>
                            🚪 <strong>Saída (Cashout):</strong> Imediatamente após o primeiro gol
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("")
                        
                    with col_odds:
                        st.metric("Odd Empate (Lay)", f"{op['odd']:.2f}")
                        st.metric("Edge Modelo vs Mercado", f"{op['edge']:+.2f}%")
                        
                    with col_risco:
                        st.metric("Stake Recomendada", f"R$ {op['stake_real']:.2f}")
                        st.metric("Responsabilidade Máxima", f"R$ {op['responsabilidade']:.2f}")

                    # Linha de Ações (Link, Telegram, Green, Red)
                    action_cols = st.columns([2.5, 2.5, 2, 2])
                    
                    with action_cols[0]:
                        st.link_button(
                            "🔥 Abrir Exchange Fulltbet",
                            "https://fulltbet.bet",
                            use_container_width=True
                        )
                        
                    with action_cols[1]:
                        if st.button("🚀 Alertar Telegram", key=f"tg_btn_{m_id}", use_container_width=True):
                            if not st.session_state.telegram_token or not st.session_state.telegram_chat_id:
                                st.error("Configure suas credenciais do Telegram na barra lateral esquerda primeiro!")
                            else:
                                msg_sinal = f"""
🚨 *NOVA OPORTUNIDADE: LAY DRAW EV+* 🚨

⚽ *Jogo:* {op['jogo']}
🏆 *Campeonato:* {op['liga']}
🕒 *Horário:* {op['horario']} UTC

📊 *Análise Quantitativa:*
• Odd Empate (Lay): `{op['odd']:.2f}`
• Prob. Mercado: `{op['p_mercado']:.1f}%`
• Prob. Modelo: `{op['p_modelo']:.1f}%`
• Edge (Vantagem): *{op['edge']:+.2f}%*
• EV Esperado: *R$ {op['ev']:.2f}*

💰 *Gestão de Stake recomendada:*
• Stake Lay sugerida: *R$ {op['stake_real']:.2f}*
• Responsabilidade Máxima: *R$ {op['responsabilidade']:.2f}*

🎯 *ESTRATÉGIA OPERACIONAL:*
1. **Entrada**: Entrar em Lay Empate próximo aos 10 minutos do primeiro tempo se a partida continuar 0x0.
2. **Saída (Cashout)**: Fazer Cashout/Hedging (fechar a operação) imediatamente após o primeiro gol ocorrer.

🔥 _Sinal enviado automaticamente via Trader LD PRO_
"""
                                sucesso, msg_status = enviar_alerta_telegram(
                                    st.session_state.telegram_token,
                                    st.session_state.telegram_chat_id,
                                    msg_sinal
                                )
                                if sucesso:
                                    st.success("Sinal enviado ao Telegram com sucesso!")
                                else:
                                    st.error(f"Erro no disparo do alerta: {msg_status}")

                    with action_cols[2]:
                        if st.button(f"✅ GREEN", key=f"green_{m_id}", use_container_width=True):
                            lucro = op["stake_real"]
                            with sqlite3.connect(DB_NAME) as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                INSERT INTO operacoes (data, jogo, liga, odd, stake, responsabilidade, resultado, lucro)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    op["jogo"],
                                    op["liga"],
                                    op["odd"],
                                    op["stake_real"],
                                    op["responsabilidade"],
                                    "GREEN",
                                    lucro
                                ))
                                conn.commit()
                            st.success(f"Green registrado com sucesso!")
                            st.rerun()

                    with action_cols[3]:
                        if st.button(f"❌ RED", key=f"red_{m_id}", use_container_width=True):
                            prejuizo = -op["responsabilidade"]
                            with sqlite3.connect(DB_NAME) as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                INSERT INTO operacoes (data, jogo, liga, odd, stake, responsabilidade, resultado, lucro)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    op["jogo"],
                                    op["liga"],
                                    op["odd"],
                                    op["stake_real"],
                                    op["responsabilidade"],
                                    "RED",
                                    prejuizo
                                ))
                                conn.commit()
                            st.error(f"Red registrado com prejuízo.")
                            st.rerun()

        # Operações recentes exibidas na base do Monitor
        st.write("---")
        st.subheader("📋 Histórico de Operações Recentes")
        if len(historico) > 0:
            df_formatado = historico.copy()
            df_formatado = df_formatado.sort_values(by="id", ascending=False)
            df_formatado["resultado"] = df_formatado["resultado"].apply(lambda r: "✅ GREEN" if r == "GREEN" else ("❌ RED" if r == "RED" else r))
            df_formatado["stake"] = df_formatado["stake"].map("R$ {:.2f}".format)
            df_formatado["responsabilidade"] = df_formatado["responsabilidade"].map("R$ {:.2f}".format)
            df_formatado["lucro"] = df_formatado["lucro"].map("R$ {:+.2f}".format)
            df_formatado["odd"] = df_formatado["odd"].map("{:.2f}".format)
            
            st.dataframe(
                df_formatado,
                use_container_width=True,
                column_config={
                    "id": "ID",
                    "data": "Data/Hora",
                    "jogo": "Partida",
                    "liga": "Campeonato",
                    "odd": "Odd do Empate",
                    "stake": "Stake Real",
                    "responsabilidade": "Responsabilidade",
                    "resultado": "Resultado",
                    "lucro": "Lucro Líquido"
                },
                hide_index=True
            )
        else:
            st.info("Nenhuma entrada operacional registrada ainda.")

    except Exception as e:
        st.error("🚨 Erro crítico de inicialização ou no processamento de APIs.")
        st.markdown(f"**Detalhes do erro:** `{str(e)}`")
        st.markdown("""
        💡 **Dica:** Certifique-se de que selecionou o modo **Simulador (Demo)** na barra lateral caso não tenha chaves válidas configuradas nas APIs. 
        Se você ativou a **API Real**, confira se suas chaves e plano de chamadas de API estão ativos e corretos.
        """)

# =========================================
# ABA 2: CALCULADORA DE CASHOUT
# =========================================
with tab_calculator:
    st.subheader("🧮 Calculadora de Cashout & Cobertura (Hedging) para Exchange")
    st.markdown("""
    Esta calculadora ajuda você a garantir lucros (*Greenbook*) no mercado de **Lay ao Empate** após a ocorrência de um gol.
    Insira os valores da sua entrada original em Lay e as Odds de Back ao vivo para obter a stake ideal de cobertura.
    """)
    
    col_inputs, col_results = st.columns([1, 1])
    
    with col_inputs:
        st.markdown("#### 📥 Entrada Original (Lay)")
        odd_lay_calc = st.number_input("Odd do Lay Inicial", min_value=1.01, max_value=20.0, value=3.40, step=0.05, format="%.2f", key="odd_lay_calc")
        stake_lay_calc = st.number_input("Stake do Lay Inicial (R$)", min_value=1.0, max_value=100000.0, value=50.0, step=5.0, key="stake_lay_calc")
        
        st.markdown("#### ⚡ Cenário Live (Back)")
        odd_back_calc = st.number_input("Odd Back do Empate no Live", min_value=1.01, max_value=100.0, value=6.50, step=0.1, format="%.2f", key="odd_back_calc")
        
    with col_results:
        st.markdown("#### 📈 Resultado da Cobertura (Greenbook)")
        responsabilidade_calc = stake_lay_calc * (odd_lay_calc - 1)
        
        # Fórmulas de Hedging
        if odd_back_calc > 0:
            stake_back_cobertura = (stake_lay_calc * odd_lay_calc) / odd_back_calc
            lucro_garantido = stake_lay_calc - stake_back_cobertura
            roi_calculado = (lucro_garantido / responsabilidade_calc) * 100 if responsabilidade_calc > 0 else 0.0
        else:
            stake_back_cobertura = 0.0
            lucro_garantido = 0.0
            roi_calculado = 0.0
            
        if lucro_garantido >= 0:
            st.markdown(f"""
            <div style="background-color: rgba(0, 230, 118, 0.1); border: 2px solid #00e676; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #00e676; margin-top:0px; margin-bottom:10px;">🟢 COBERTURA COM LUCRO</h3>
                <p style="margin: 4px 0;">Sua Responsabilidade Original: <strong>R$ {responsabilidade_calc:.2f}</strong></p>
                <hr style="border-color: rgba(0, 230, 118, 0.2); margin: 8px 0;">
                <h4 style="margin: 4px 0; color: #ffffff;">Fazer aposta de <strong>BACK</strong> ao Empate no Live:</h4>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 4px 0; color: #00C9FF;">Stake Back ideal: R$ {stake_back_cobertura:.2f}</p>
                <p style="font-size: 1.1rem; margin: 4px 0;">Na Odd Live de: <strong>@{odd_back_calc:.2f}</strong></p>
                <hr style="border-color: rgba(0, 230, 118, 0.2); margin: 8px 0;">
                <p style="font-size: 1.3rem; font-weight: bold; color: #00e676; margin: 4px 0;">LUCRO LÍQUIDO GARANTIDO: R$ {lucro_garantido:.2f}</p>
                <p style="font-size: 1.0rem; margin: 4px 0; color: #a1a1a1;">Retorno garantido sobre risco: <strong>{roi_calculado:.1f}%</strong></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: rgba(255, 23, 68, 0.1); border: 2px solid #ff1744; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #ff1744; margin-top:0px; margin-bottom:10px;">🔴 COBERTURA COM PREJUÍZO (Redbook)</h3>
                <p style="margin: 4px 0;">Sua Responsabilidade Original: <strong>R$ {responsabilidade_calc:.2f}</strong></p>
                <hr style="border-color: rgba(255, 23, 68, 0.2); margin: 8px 0;">
                <h4 style="margin: 4px 0; color: #ffffff;">Fazer aposta de <strong>BACK</strong> ao Empate no Live:</h4>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 4px 0; color: #00C9FF;">Stake Back ideal: R$ {stake_back_cobertura:.2f}</p>
                <p style="font-size: 1.1rem; margin: 4px 0;">Na Odd Live de: <strong>@{odd_back_calc:.2f}</strong></p>
                <hr style="border-color: rgba(255, 23, 68, 0.2); margin: 8px 0;">
                <p style="font-size: 1.3rem; font-weight: bold; color: #ff1744; margin: 4px 0;">PREJUÍZO LÍQUIDO LIMITADO: R$ {lucro_garantido:.2f}</p>
                <p style="font-size: 1.0rem; margin: 4px 0; color: #a1a1a1;">Prejuízo garantido sobre risco: <strong>{roi_calculado:.1f}%</strong></p>
            </div>
            """, unsafe_allow_html=True)

    with st.expander("📖 Entendendo a Matemática da Cobertura (Hedging)"):
        st.write("""
        ### Como funciona o Hedging no Lay ao Empate?
        
        Quando você aposta em **Lay** (Contra) o Empate, você ganha se qualquer um dos times vencer o jogo.
        O principal risco é o jogo terminar empatado, o que custará a sua responsabilidade total: `Stake * (Odd - 1)`.
        
        **A oportunidade de fechar:**
        Assim que um dos times marca um gol, a probabilidade de empate cai drasticamente e as Odds do Empate sobem muito (ex: de `@3.40` para `@6.50`).
        
        Ao fazer uma aposta em **Back** (A favor) do Empate na nova odd alta no Live com a stake ideal calculada acima, você **cobre** a sua aposta inicial:
        * Se o jogo terminar **Home** ou **Away** (com vencedor), você ganha a aposta de Lay inicial e perde a aposta menor de Back. O saldo é positivo!
        * Se o jogo terminar **Empatado**, você perde a responsabilidade do Lay inicial, mas ganha a aposta de Back com a Odd alta. O saldo é exatamente o mesmo lucro positivo!
        
        Isso elimina completamente o risco do jogo até o final e garante o lucro imediatamente após o gol.
        """)

# =========================================
# ABA 3: ESTATÍSTICAS E INSIGHTS
# =========================================
with tab_insights:
    st.subheader("📊 Estatísticas Operacionais & Trader Insights")
    
    if len(historico) == 0:
        st.info("Nenhuma operação registrada no histórico operacional ainda. Registre seus primeiros Greens e Reds na aba 'Monitor EV+' para gerar relatórios de performance de inteligência de trading!")
    else:
        # 1. DOWNLOAD DO HISTÓRICO EM CSV
        csv = historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Histórico de Operações Completo (CSV)",
            data=csv,
            file_name=f"historico_operacoes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.write("")
        
        # 2. SEÇÃO DE INSIGHTS E GRÁFICOS
        col_ins_left, col_ins_right = st.columns([1, 1])
        
        with col_ins_left:
            st.markdown("### 🏆 Ligas Mais Lucrativas (Ganhos por Campeonato)")
            if "liga" in historico.columns and historico["liga"].notna().any():
                # Filtrar nulos da liga e agrupar
                historico_filtrado_liga = historico[historico["liga"].notna()]
                perf_liga = historico_filtrado_liga.groupby("liga")["lucro"].sum().reset_index()
                perf_liga = perf_liga.sort_values(by="lucro", ascending=False)
                
                st.bar_chart(
                    data=perf_liga,
                    x="liga",
                    y="lucro",
                    color="#92FE9D",
                    use_container_width=True
                )
            else:
                st.warning("Adicione novas entradas para carregar o gráfico por liga.")
                
        with col_ins_right:
            st.markdown("### 🎯 ROI por Faixa de Odds")
            def categorizar_odd(odd):
                if odd < 3.0:
                    return "1. Odds Baixas (< 3.0)"
                elif odd < 4.0:
                    return "2. Odds Médias (3.0 - 4.0)"
                elif odd < 5.0:
                    return "3. Odds Altas (4.0 - 5.0)"
                else:
                    return "4. Odds Super Altas (>= 5.0)"
                    
            historico_faixas = historico.copy()
            historico_faixas["faixa_odd"] = historico_faixas["odd"].apply(categorizar_odd)
            
            agg_faixas = historico_faixas.groupby("faixa_odd").agg(
                Quantidade=("id", "count"),
                Greens=("resultado", lambda x: (x == "GREEN").sum()),
                Reds=("resultado", lambda x: (x == "RED").sum()),
                Stake_Total=("stake", "sum"),
                Lucro_Liquido=("lucro", "sum")
            ).reset_index()
            
            # ROI de cada faixa
            agg_faixas["ROI %"] = (agg_faixas["Lucro_Liquido"] / agg_faixas["Stake_Total"]) * 100
            # Winrate de cada faixa
            agg_faixas["Winrate %"] = (agg_faixas["Greens"] / agg_faixas["Quantidade"]) * 100
            
            # Formatação
            agg_faixas_display = agg_faixas.copy()
            agg_faixas_display["Stake_Total"] = agg_faixas_display["Stake_Total"].map("R$ {:.2f}".format)
            agg_faixas_display["Lucro_Liquido"] = agg_faixas_display["Lucro_Liquido"].map("R$ {:+.2f}".format)
            agg_faixas_display["ROI %"] = agg_faixas_display["ROI %"].map("{:+.1f}%".format)
            agg_faixas_display["Winrate %"] = agg_faixas_display["Winrate %"].map("{:.1f}%".format)
            
            st.dataframe(
                agg_faixas_display,
                column_config={
                    "faixa_odd": "Faixa de Odds",
                    "Quantidade": "Entradas",
                    "Greens": "Greens",
                    "Reds": "Reds",
                    "Stake_Total": "Stake Total",
                    "Lucro_Liquido": "Lucro Líquido",
                    "ROI %": "ROI %",
                    "Winrate %": "Winrate %"
                },
                hide_index=True,
                use_container_width=True
            )
            
        # 3. CARD INSIGHT DE INTELIGÊNCIA ARTIFICIAL
        st.write("")
        st.subheader("💡 Insights Analíticos de Inteligência do Trader")
        
        melhor_faixa = None
        pior_faixa = None
        if len(agg_faixas) > 0:
            agg_faixas_sort = agg_faixas.sort_values(by="ROI %", ascending=False)
            melhor_faixa = agg_faixas_sort.iloc[0]
            pior_faixa = agg_faixas_sort.iloc[-1]
            
        best_league = None
        if "liga" in historico.columns and historico["liga"].notna().any():
            # recalculando o dataframe se houver ligas
            perf_liga_sort = perf_liga.sort_values(by="lucro", ascending=False)
            if len(perf_liga_sort) > 0:
                best_league = perf_liga_sort.iloc[0]

        insight_text = "### 🧠 Recomendações Operacionais baseadas no seu Histórico:\n"
        if melhor_faixa is not None and melhor_faixa["ROI %"] > 0:
            insight_text += f"* 🟢 **Faixa Altamente Vantajosa:** Sua performance é estatisticamente superior nas **{melhor_faixa['faixa_odd'][3:]}**, operando com um **ROI excelente de {melhor_faixa['ROI %']:.1f}%** e winrate de **{melhor_faixa['Winrate %']:.1f}%**. Recomendamos focar nestas oportunidades!\n"
        if pior_faixa is not None and pior_faixa["ROI %"] < 0:
            insight_text += f"* 🔴 **Ajuste Recomendado:** As **{pior_faixa['faixa_odd'][3:]}** apresentam **ROI negativo de {pior_faixa['ROI %']:.1f}%**. Sugerimos reavaliar o tamanho da stake para esse grupo ou aplicar filtros mais restritivos!\n"
        if best_league is not None and best_league["lucro"] > 0:
            insight_text += f"* 🏆 **Liga Ouro:** A liga **{best_league['liga']}** representa o seu mercado mais lucrativo, acumulando um saldo líquido de **R$ {best_league['lucro']:.2f}**.\n"
        else:
            insight_text += "* 📈 **Mapeamento:** Registre novas entradas em campeonatos variados. O algoritmo de performance mapeará automaticamente em qual liga você detém a maior taxa de Green!\n"
            
        st.markdown(f"""
        <div style="background-color: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px;">
            {insight_text}
        </div>
        """, unsafe_allow_html=True)
