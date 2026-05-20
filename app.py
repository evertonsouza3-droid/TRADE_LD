import streamlit as st
import pandas as pd
import requests
import sqlite3
from datetime import datetime
import json
import os

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
# BANCO DE DADOS (Conexão Segura e Migração)
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
# SESSION STATE (Inicialização e Estados)
# =========================================
config_carregada = carregar_configuracao()

if "banca_inicial" not in st.session_state:
    st.session_state.banca_inicial = 1000.0

if "api_football" not in st.session_state:
    st.session_state.api_football = config_carregada.get("api_football", "SUA_API_FOOTBALL")

if "api_odds" not in st.session_state:
    st.session_state.api_odds = config_carregada.get("api_odds", "SUA_API_ODDS")

if "telegram_token" not in st.session_state:
    st.session_state.telegram_token = config_carregada.get("telegram_token", "")

if "telegram_chat_id" not in st.session_state:
    st.session_state.telegram_chat_id = config_carregada.get("telegram_chat_id", "")

# Controle de formulários ativos nos cards de jogo
if "active_green_id" not in st.session_state:
    st.session_state.active_green_id = None

if "active_red_id" not in st.session_state:
    st.session_state.active_red_id = None

# =========================================
# SIDEBAR - CONFIGURAÇÃO E GESTÃO
# =========================================
st.sidebar.markdown("### ⚙️ Painel de Controle")

# 1. Configurações de Conectividade e Telegram
api_expander = st.sidebar.expander("🔌 APIs & Canal do Telegram", expanded=True)
with api_expander:
    api_football = st.text_input(
        "Football-Data Token",
        value=st.session_state.api_football if st.session_state.api_football != "SUA_API_FOOTBALL" else "",
        type="password",
        placeholder="Cole seu token do site football-data.org",
        help="Seu token X-Auth-Token"
    )
    
    api_odds = st.text_input(
        "The Odds API Key",
        value=st.session_state.api_odds if st.session_state.api_odds != "SUA_API_ODDS" else "",
        type="password",
        placeholder="Cole sua key do site the-odds-api.com",
        help="Sua chave apiKey"
    )
    
    st.markdown("---")
    st.markdown("💬 **Integração Telegram**")
    telegram_token = st.text_input(
        "Telegram Bot Token",
        value=st.session_state.telegram_token,
        type="password",
        placeholder="Token gerado pelo @BotFather",
        help="Token de acesso do seu bot"
    )
    telegram_chat_id = st.text_input(
        "Telegram Chat ID",
        value=st.session_state.telegram_chat_id,
        placeholder="ID do chat/canal receptor",
        help="O ID numérico do grupo ou canal privado"
    )
    
    if st.button("💾 Salvar Configurações", use_container_width=True):
        st.session_state.api_football = api_football if api_football else "SUA_API_FOOTBALL"
        st.session_state.api_odds = api_odds if api_odds else "SUA_API_ODDS"
        st.session_state.telegram_token = telegram_token
        st.session_state.telegram_chat_id = telegram_chat_id
        salvar_configuracao(st.session_state.api_football, st.session_state.api_odds, telegram_token, telegram_chat_id)
        st.success("Configurações salvas localmente!")
        st.rerun()

# 2. Gestão de Banca Avançada
banca_expander = st.sidebar.expander("💰 Gestão de Banca Real", expanded=True)
with banca_expander:
    banca_inicial = st.number_input(
        "Banca de Partida (R$)",
        min_value=10.0,
        max_value=1000000.0,
        value=st.session_state.banca_inicial,
        step=50.0,
        help="O capital total original que você colocou nas exchanges."
    )
    st.session_state.banca_inicial = banca_inicial

    tipo_juros = st.radio(
        "Cálculo de Juros",
        ["Flat Staking", "Juros Compostos"],
        help="Flat Staking calcula a stake base sobre a Banca Inicial. Juros Compostos recalcula dinamicamente sobre a Banca Atual Corrente."
    )
    
    tipo_gestao = st.radio(
        "Método de Gestão",
        ["Stake Fixa", "Risco Fixo (Responsabilidade Limitada)"],
        help="Stake Fixa: Stake recomendada é fixa em % da banca. Risco Fixo: A responsabilidade (risco máximo do Lay) é rigidamente limitada a % da banca, adaptando a stake em cada odd."
    )

    stake_percentual = st.slider(
        "Porcentagem de Gestão %",
        min_value=1.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="O risco ou stake base como percentual da banca selecionada."
    )
    
    comissao = st.number_input(
        "Comissão da Exchange (%)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.5,
        help="Taxa cobrada pela Betfair/Fulltbet sobre seus lucros líquidos (descontada na gravação de Greens)."
    )

# 3. Parametrização do Modelo
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

# 4. Ações e Reset de Segurança
danger_expander = st.sidebar.expander("⚠️ Segurança & Reset", expanded=False)
with danger_expander:
    confirm_reset = st.checkbox("Desejo limpar todo o histórico")
    if st.button("Resetar Histórico", type="secondary"):
        if confirm_reset:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM operacoes")
                conn.commit()
            st.success("Histórico zerado com sucesso!")
            st.rerun()
        else:
            st.error("Marque a caixa de confirmação!")

# =========================================
# LÓGICA DO MODELO MATEMÁTICO & TELEGRAM
# =========================================
def prob_mercado(odd):
    return round((1 / odd) * 100, 2)

def modelo_empate(media_gols_ajustada):
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
# CARREGAMENTO E ANÁLISE DE HISTÓRICO
# =========================================
with sqlite3.connect(DB_NAME) as conn:
    historico = pd.read_sql_query("SELECT * FROM operacoes ORDER BY id ASC", conn)

greens = len(historico[historico["resultado"] == "GREEN"])
reds = len(historico[historico["resultado"] == "RED"])
operacoes_totais = greens + reds

# Lucro Acumulado
lucro_total = historico["lucro"].sum() if len(historico) > 0 else 0.0

# Banca Atualizada
banca_atual = banca_inicial + lucro_total

# Cálculo da Banca para Dimensionamento de Stakes
banca_calculo = banca_atual if tipo_juros == "Juros Compostos" else banca_inicial

# Winrate e ROI
if operacoes_totais > 0:
    winrate = (greens / operacoes_totais) * 100
    stake_total_acumulada = historico["stake"].sum()
    roi = (lucro_total / stake_total_acumulada) * 100 if stake_total_acumulada > 0 else 0.0
else:
    winrate = 0.0
    roi = 0.0

# =========================================
# DASHBOARD DE KPIS GERAIS
# =========================================
kpi_cols = st.columns(5)

kpi_cols[0].metric(
    "💰 Banca Inicial",
    f"R$ {banca_inicial:.2f}",
    help="O seu capital inicial de partida configurado."
)
kpi_cols[1].metric(
    "🔄 Banca Atual Corrente",
    f"R$ {banca_atual:.2f}",
    delta=f"{lucro_total:+.2f} R$" if operacoes_totais > 0 else None,
    delta_color="normal" if lucro_total >= 0 else "inverse",
    help="O saldo atualizado da sua banca (Banca Inicial + Lucros Acumulados)."
)
kpi_cols[2].metric(
    "✅ Greens / ❌ Reds",
    f"{greens} G / {reds} R",
    help="Relação de entradas vencedoras e perdedoras."
)
kpi_cols[3].metric(
    "🎯 Winrate",
    f"{winrate:.1f}%",
    help="Percentual de vitórias com base no histórico."
)
kpi_cols[4].metric(
    "📊 ROI do Histórico",
    f"{roi:+.1f}%",
    help="Retorno sobre o capital total investido (Stake Total acumulada)."
)

st.write("")

# =========================================
# ABAS DO DASHBOARD
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
            st.subheader("📈 Curva de Crescimento (Banca ao Longo do Tempo)")
            historico_acumulado = historico.copy()
            historico_acumulado["banca_acumulada"] = banca_inicial + historico_acumulado["lucro"].cumsum()
            
            ponto_inicial = pd.DataFrame([{
                "id": 0, "data": "Início", "jogo": "Capital Inicial", "liga": "START",
                "odd": 0.0, "stake": 0.0, "responsabilidade": 0.0,
                "resultado": "START", "lucro": 0.0, "banca_acumulada": banca_inicial
            }])
            df_plot = pd.concat([ponto_inicial, historico_acumulado], ignore_index=True)
            
            st.line_chart(
                data=df_plot,
                x="id",
                y="banca_acumulada",
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

    # Verificação de Chaves de API
    chaves_configuradas = (st.session_state.api_football != "SUA_API_FOOTBALL") and (st.session_state.api_odds != "SUA_API_ODDS")

    if not chaves_configuradas:
        st.info("👋 **Bem-vindo ao Trader LD PRO!** Para começar a operar de forma real, configure suas chaves de API na barra lateral esquerda.")
        st.markdown("""
        ### 🔌 Como obter suas chaves de API gratuitas:
        
        1. **Chave de Jogos (Football-Data):**
           * Cadastre-se em [football-data.org](https://www.football-data.org) (plano gratuito).
           * Eles enviarão um token por e-mail (Token de API).
           * Cole esse token no campo **Football-Data Token** na barra lateral.
        
        2. **Chave de Odds (The Odds API):**
           * Cadastre-se gratuitamente em [the-odds-api.com](https://the-odds-api.com) para obter acesso a odds de futebol de diversas casas de apostas.
           * Cole sua chave no campo **The Odds API Key** na barra lateral.
        
        3. Clique em **💾 Salvar Configurações**. O feed de jogos reais aparecerá aqui instantaneamente!
        """)
    else:
        st.subheader("⚽ Monitor de Oportunidades em Tempo Real")
        
        # Filtros de Busca e Exibição
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

        try:
            # Chamadas Reais de API
            headers = {"X-Auth-Token": st.session_state.api_football}
            session = requests.Session()
            session.trust_env = False
            
            # 1. Requisição das Partidas Real
            response = session.get(
                "https://api.football-data.org/v4/matches?status=SCHEDULED",
                headers=headers,
                timeout=20
            )
            if response.status_code != 200:
                raise Exception(f"Erro na API Football-Data ({response.status_code}): {response.text}")
            dados = response.json()
            
            # 2. Requisição das Odds Real
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

            # Processamento
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
                    
                # Cálculos com base nas Odds encontradas
                p_mercado = prob_mercado(odd)
                p_modelo = modelo_empate(media_gols)
                edge = round(p_mercado - p_modelo, 2)
                
                # CÁLCULO DA STAKE BASE DINÂMICA
                if tipo_gestao == "Stake Fixa":
                    # Stake base = % fixo da banca de cálculo
                    stake_inicial_recomendada = banca_calculo * (stake_percentual / 100)
                    stake_real = stake_ajustada(stake_inicial_recomendada, odd)
                    responsabilidade = round(stake_real * (odd - 1), 2)
                else:
                    # Risco Fixo: Responsabilidade (risco máximo) é fixa em % da banca de cálculo
                    responsabilidade_limite = banca_calculo * (stake_percentual / 100)
                    # Stake = responsabilidade / (odd - 1)
                    stake_inicial_recomendada = responsabilidade_limite / (odd - 1) if odd > 1 else 0.0
                    stake_real = stake_ajustada(stake_inicial_recomendada, odd)
                    responsabilidade = round(stake_real * (odd - 1), 2)
                
                ev = calcular_ev(stake_real, odd, p_modelo)
                
                # Filtros
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

            # Ordenação
            if sort_by == "Maior EV+":
                oportunidades = sorted(oportunidades, key=lambda x: x["ev"], reverse=True)
            elif sort_by == "Maior Edge":
                oportunidades = sorted(oportunidades, key=lambda x: x["edge"], reverse=True)
            elif sort_by == "Mais Cedo":
                oportunidades = sorted(oportunidades, key=lambda x: x["horario"])
            elif sort_by == "Menor Odd Empate":
                oportunidades = sorted(oportunidades, key=lambda x: x["odd"])

            # Exibição
            if len(oportunidades) == 0:
                st.info("Nenhum confronto EV+ atende aos filtros configurados neste momento.")
            else:
                st.write(f"Encontrados **{len(oportunidades)}** confrontos reais EV+ para Lay ao Empate:")
                
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
                            st.metric("Stake Recomendada", f"R$ {op['stake_real']:.2f}", help="Stake ajustada de acordo com seu método de gestão de risco selecionado.")
                            st.metric("Responsabilidade Máxima", f"R$ {op['responsabilidade']:.2f}", help="Risco máximo em caso de Red sem cashout.")

                        # Ações
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
                                    st.error("Configure suas credenciais do Telegram na barra lateral esquerda!")
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
                                        st.success("Sinal enviado ao Telegram!")
                                    else:
                                        st.error(f"Erro no envio: {msg_status}")

                        # Botões que abrem os formulários de gravação reais
                        with action_cols[2]:
                            if st.button(f"✅ REGISTRAR GREEN", key=f"btn_green_{m_id}", use_container_width=True):
                                st.session_state.active_green_id = m_id
                                st.session_state.active_red_id = None
                                st.rerun()

                        with action_cols[3]:
                            if st.button(f"❌ REGISTRAR RED", key=f"btn_red_{m_id}", use_container_width=True):
                                st.session_state.active_red_id = m_id
                                st.session_state.active_green_id = None
                                st.rerun()

                        # 🟢 FORMULÁRIO DE CONFIRMAÇÃO DE GREEN REAL
                        if st.session_state.active_green_id == m_id:
                            st.write("")
                            with st.form(key=f"form_green_{m_id}"):
                                st.markdown("### ✏️ Confirmar Lucro Real do Green")
                                st.markdown("Insira o lucro bruto real que você obteve no mercado. A taxa de comissão da exchange será deduzida automaticamente.")
                                
                                # Sugerimos a stake_real como lucro bruto padrão
                                lucro_bruto_real = st.number_input(
                                    "Lucro Bruto Obtido (R$)",
                                    min_value=0.0,
                                    value=float(op["stake_real"]),
                                    step=1.0,
                                    key=f"val_green_{m_id}"
                                )
                                
                                comissao_deduzida = lucro_bruto_real * (comissao / 100)
                                lucro_liquido_real = lucro_bruto_real - comissao_deduzida
                                
                                st.markdown(f"🔹 **Taxa da Exchange ({comissao}%):** `R$ {comissao_deduzida:.2f}`")
                                st.markdown(f"🟩 **Lucro Líquido Real Gravado:** **R$ {lucro_liquido_real:.2f}**")
                                
                                form_cols = st.columns([1, 1])
                                with form_cols[0]:
                                    if st.form_submit_button("Salvar no Histórico Operacional", use_container_width=True):
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
                                                lucro_liquido_real
                                            ))
                                            conn.commit()
                                        st.session_state.active_green_id = None
                                        st.success("Green registrado!")
                                        st.rerun()
                                        
                                with form_cols[1]:
                                    if st.form_submit_button("Cancelar", use_container_width=True):
                                        st.session_state.active_green_id = None
                                        st.rerun()

                        # 🔴 FORMULÁRIO DE CONFIRMAÇÃO DE RED REAL
                        if st.session_state.active_red_id == m_id:
                            st.write("")
                            with st.form(key=f"form_red_{m_id}"):
                                st.markdown("### ✏️ Confirmar Prejuízo Real do Red")
                                st.markdown("Insira o prejuízo real final sofrido nesta operação (geralmente menor do que a responsabilidade inteira devido a cashout tardio).")
                                
                                # Sugerimos a responsabilidade máxima como prejuízo bruto padrão
                                prejuizo_real_usuario = st.number_input(
                                    "Prejuízo Sofrido (R$)",
                                    min_value=0.0,
                                    value=float(op["responsabilidade"]),
                                    step=1.0,
                                    key=f"val_red_{m_id}"
                                )
                                
                                st.markdown(f"🟥 **Prejuízo Líquido Real Gravado:** **R$ -{prejuizo_real_usuario:.2f}**")
                                
                                form_cols = st.columns([1, 1])
                                with form_cols[0]:
                                    if st.form_submit_button("Salvar no Histórico Operacional", use_container_width=True):
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
                                                -prejuizo_real_usuario
                                            ))
                                            conn.commit()
                                        st.session_state.active_red_id = None
                                        st.success("Red registrado!")
                                        st.rerun()
                                        
                                with form_cols[1]:
                                    if st.form_submit_button("Cancelar", use_container_width=True):
                                        st.session_state.active_red_id = None
                                        st.rerun()

            # Operações recentes exibidas na base
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
                        "lucro": "Lucro Líquido Real"
                    },
                    hide_index=True
                )
            else:
                st.info("Nenhuma entrada registrada na tabela de histórico ainda.")

        except Exception as e:
            st.error("🚨 Erro crítico de inicialização ou no processamento de APIs.")
            st.markdown(f"**Detalhes do erro:** `{str(e)}`")
            st.markdown("""
            💡 **Dica:** Confirme se suas chaves e plano de chamadas de API do **The Odds API** e **Football-Data** estão corretos e salvos na barra lateral esquerda.
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
        st.markdown("#### 📥 Aposta Original (Lay)")
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
            perf_liga_sort = perf_liga.sort_values(by="lucro", ascending=False)
            if len(perf_liga_sort) > 0:
                best_league = perf_liga_sort.iloc[0]

        insight_text = "### 🧠 Recomendações Operacionais baseadas no seu Histórico:\n"
        if melhor_faixa is not None and melhor_faixa["ROI %"] > 0:
            insight_text += f"* 🟢 **Faixa Altamente Vantajosa:** Sua performance é estatisticamente superior nas **{melhor_faixa['faixa_odd'][3:]}**, operando com um **ROI excelente de {melhor_faixa['ROI %']:.1f}%** e winrate de **{melhor_faixa['Winrate %']:.1f}%**. Recomendamos priorizar entradas nessa faixa!\n"
        if pior_faixa is not None and pior_faixa["ROI %"] < 0:
            insight_text += f"* 🔴 **Ajuste Recomendado:** As **{pior_faixa['faixa_odd'][3:]}** apresentam **ROI de {pior_faixa['ROI %']:.1f}%**. Sugerimos limitar sua stake nessas odds altas para reduzir drawdowns!\n"
        if best_league is not None and best_league["lucro"] > 0:
            insight_text += f"* 🏆 **Liga Ouro:** A liga **{best_league['liga']}** representa o seu mercado mais lucrativo, acumulando um saldo líquido real de **R$ {best_league['lucro']:.2f}**.\n"
        else:
            insight_text += "* 📈 **Mapeamento:** Registre novas entradas de greens e reds. O algoritmo inteligente mapeará automaticamente o seu ROI real em cada campeonato!\n"
            
        st.markdown(f"""
        <div style="background-color: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px;">
            {insight_text}
        </div>
        """, unsafe_allow_html=True)
