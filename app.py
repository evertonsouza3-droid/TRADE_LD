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
# BANCO DE DADOS (Conexão Segura com context manager)
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
        conn.commit()

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
    return {"api_football": "SUA_API_FOOTBALL", "api_odds": "SUA_API_ODDS"}

def salvar_configuracao(api_football, api_odds):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api_football": api_football, "api_odds": api_odds}, f)
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

# =========================================
# SIDEBAR - CONFIGURAÇÃO E GESTÃO
# =========================================
st.sidebar.markdown("### ⚙️ Painel de Controle")

# 1. Configurações de API e Conectividade
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
        
        if st.button("💾 Salvar Chaves", use_container_width=True, help="Salva suas chaves localmente para não precisar digitá-las novamente."):
            st.session_state.api_football = api_football
            st.session_state.api_odds = api_odds
            salvar_configuracao(api_football, api_odds)
            st.success("Chaves salvas localmente com sucesso!")
            st.rerun()
            
        # Garante a atualização em tempo real se o usuário apenas colar
        st.session_state.api_football = api_football
        st.session_state.api_odds = api_odds
    else:
        st.info("💡 Modo simulado ativo! Dados dinâmicos de alta qualidade gerados localmente.")

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
# LÓGICA DO MODELO MATEMÁTICO
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
# DASHBOARD DE KPIS
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

# =========================================
# DASHBOARD DE GRÁFICOS ANALÍTICOS
# =========================================
if operacoes_totais > 0:
    st.write("")
    graph_cols = st.columns([7, 3])
    
    with graph_cols[0]:
        st.subheader("📈 Curva de Crescimento (Lucro Acumulado)")
        # Calculando o lucro acumulado passo a passo
        historico_acumulado = historico.copy()
        historico_acumulado["lucro_acumulado"] = historico_acumulado["lucro"].cumsum()
        
        # Inserindo ponto de partida zero para o gráfico ficar bonito
        ponto_inicial = pd.DataFrame([{
            "id": 0, "data": "Início", "jogo": "Capital Inicial",
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
        st.subheader("📊 Distribuição")
        # Gráfico em barras ou KPIs analíticos complementares
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

# =========================================
# FILTROS E BUSCA DE JOGOS
# =========================================
st.subheader("⚽ Monitor de Oportunidades (Lay ao Empate EV+)")

filter_cols = st.columns([4, 3, 3, 2])
with filter_cols[0]:
    search_query = st.text_input("🔍 Buscar por Time ou Liga", "", help="Filtre os jogos por nome de time ou campeonato.")
with filter_cols[1]:
    min_odd_filter = st.slider("Filtro Odd Mínima do Empate", 2.0, 8.0, 2.5, step=0.1)
with filter_cols[2]:
    min_ev_filter = st.slider("Filtro EV Mínimo (R$)", 0.0, 100.0, 0.0, step=1.0)
with filter_cols[3]:
    sort_by = st.selectbox(
        "Ordenar por",
        ["Maior EV+", "Maior Edge", "Mais Cedo", "Menor Odd Empate"]
    )

# =========================================
# CAPTURA DE DADOS (API vs Simulador)
# =========================================
dados = None
odds_data = None

try:
    if st.session_state.api_mode == "Simulador (Demo)":
        # Carrega dados simulados dinâmicos
        dados, odds_data = mock_data.generate_mock_data()
    else:
        # Modo API Real - Requisição de Partidas
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
        
        # Modo API Real - Requisição de Odds
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

    # Mapeamento das odds nos mesmos formatos
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

    # Processamento e filtragem das partidas
    oportunidades = []

    for partida in dados.get("matches", []):
        casa = partida["homeTeam"]["name"]
        fora = partida["awayTeam"]["name"]
        liga = partida["competition"]["name"]
        horario_utc = partida["utcDate"] # Ex: "2026-05-19T20:45:00Z"
        
        # Parser amigável do horário
        try:
            dt = datetime.strptime(horario_utc, "%Y-%m-%dT%H:%M:%SZ")
            horario = dt.strftime("%H:%M")
        except:
            horario = horario_utc[11:16]
            
        jogo = f"{casa} x {fora}"
        odd = None
        
        # Encontrar Odds via Match Flexível
        for nome_odds, odd_valor in odds_dict.items():
            nome_lower = nome_odds.lower()
            if casa.lower() in nome_lower and fora.lower() in nome_lower:
                odd = odd_valor
                break
                
        if not odd:
            continue
            
        # Cálculos de EV e probabilidades
        p_mercado = prob_mercado(odd)
        p_modelo = modelo_empate(media_gols)
        edge = round(p_mercado - p_modelo, 2)
        
        stake_real = stake_ajustada(stake_base, odd)
        responsabilidade = round(stake_real * (odd - 1), 2)
        ev = calcular_ev(stake_real, odd, p_modelo)
        
        # Filtros de Dashboard
        if ev <= 0:
            continue # Mantém o foco no EV+
        if odd < min_odd_filter:
            continue
        if ev < min_ev_filter:
            continue
            
        # Filtro de Busca por texto (Case Insensitive)
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

    # Ordenação dinâmica das oportunidades encontradas
    if sort_by == "Maior EV+":
        oportunidades = sorted(oportunidades, key=lambda x: x["ev"], reverse=True)
    elif sort_by == "Maior Edge":
        oportunidades = sorted(oportunidades, key=lambda x: x["edge"], reverse=True)
    elif sort_by == "Mais Cedo":
        oportunidades = sorted(oportunidades, key=lambda x: x["horario"])
    elif sort_by == "Menor Odd Empate":
        oportunidades = sorted(oportunidades, key=lambda x: x["odd"])

    # Exibição dos cartões de oportunidades
    if len(oportunidades) == 0:
        st.info("Nenhum jogo EV+ encontrado com os parâmetros e filtros atuais. Experimente ajustar a Média de Gols ou limpar os filtros.")
    else:
        st.write(f"Exibindo **{len(oportunidades)}** oportunidades de entrada Lay ao Empate:")
        
        for op in oportunidades:
            # ID único de match para evitar colisão nos botões
            m_id = op["id"]
            
            with st.container(border=True):
                a, b, c = st.columns([3.5, 2, 2.5])
                
                with a:
                    st.markdown(f"### ⚽ {op['jogo']}")
                    st.markdown(f"🏆 `{op['liga']}` • 🕒 Horário: **{op['horario']}**")
                    
                    # Estratégia pré-definida de Lay Draw
                    st.markdown("""
                    <div style="background-color: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #00C9FF;">
                        🎯 <strong>Entrada:</strong> Próximo aos 10min de jogo (se empatado)<br>
                        🚪 <strong>Saída (Cashout):</strong> Imediatamente após o primeiro gol
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    
                with b:
                    st.metric("Odd Empate (Lay)", f"{op['odd']:.2f}")
                    st.metric("Edge Modelo vs Mercado", f"{op['edge']:+.2f}%", help="Diferença entre probabilidade do mercado e nosso modelo quantitativo.")
                    
                with c:
                    st.metric("Stake Ajustada", f"R$ {op['stake_real']:.2f}", help="Stake reduzida proporcionalmente para odds altas (controle de drawdown).")
                    st.metric("Responsabilidade", f"R$ {op['responsabilidade']:.2f}", help="Risco máximo da operação (Stake x (Odd - 1)).")

                # Linha de Ações: Abertura e Registro
                action_cols = st.columns([3, 2, 2])
                
                with action_cols[0]:
                    st.link_button(
                        "🔥 Abrir Exchange Fulltbet",
                        f"https://fulltbet.bet",
                        use_container_width=True
                    )
                    
                with action_cols[1]:
                    # Botão Green estilizado com ID de partida único
                    if st.button(f"✅ Registrar GREEN", key=f"green_btn_{m_id}", use_container_width=True):
                        lucro = op["stake_real"]
                        with sqlite3.connect(DB_NAME) as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                            INSERT INTO operacoes (data, jogo, odd, stake, responsabilidade, resultado, lucro)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                op["jogo"],
                                op["odd"],
                                op["stake_real"],
                                op["responsabilidade"],
                                "GREEN",
                                lucro
                            ))
                            conn.commit()
                        st.success(f"Green em {op['jogo']} registrado com sucesso!")
                        st.rerun()
                        
                with action_cols[2]:
                    # Botão Red estilizado com ID de partida único
                    if st.button(f"❌ Registrar RED", key=f"red_btn_{m_id}", use_container_width=True):
                        prejuizo = -op["responsabilidade"]
                        with sqlite3.connect(DB_NAME) as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                            INSERT INTO operacoes (data, jogo, odd, stake, responsabilidade, resultado, lucro)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                op["jogo"],
                                op["odd"],
                                op["stake_real"],
                                op["responsabilidade"],
                                "RED",
                                prejuizo
                            ))
                            conn.commit()
                        st.error(f"Red em {op['jogo']} registrado com prejuízo.")
                        st.rerun()

    # =====================================
    # EXIBIÇÃO DA TABELA DE HISTÓRICO
    # =====================================
    st.write("---")
    st.subheader("📋 Histórico Completo de Operações")
    
    if len(historico) > 0:
        # Formatar dataframe para ficar legível e premium
        df_formatado = historico.copy()
        
        # Ordenar decrescente para mostrar as últimas primeiro
        df_formatado = df_formatado.sort_values(by="id", ascending=False)
        
        # Mapeamento estético do resultado
        df_formatado["resultado"] = df_formatado["resultado"].apply(lambda r: "✅ GREEN" if r == "GREEN" else ("❌ RED" if r == "RED" else r))
        
        # Formatação de Moeda
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
                "odd": "Odd do Empate",
                "stake": "Stake Real",
                "responsabilidade": "Responsabilidade",
                "resultado": "Resultado",
                "lucro": "Lucro Líquido"
            },
            hide_index=True
        )
    else:
        st.info("Nenhuma operação registrada no histórico operacional ainda. Registre suas primeiras entradas usando os botões acima!")

except Exception as e:
    st.error("🚨 Erro crítico de inicialização ou no processamento de APIs.")
    st.markdown(f"**Detalhes do erro:** `{str(e)}`")
    st.markdown("""
    💡 **Dica:** Certifique-se de que selecionou o modo **Simulador (Demo)** na barra lateral caso não tenha chaves válidas configuradas nas APIs. 
    Se você ativou a **API Real**, confira se suas chaves e plano de chamadas de API estão ativos e corretos.
    """)
