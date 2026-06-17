import streamlit as st
import json
import psutil
import os

st.set_page_config(
    page_title="LTD Dashboard",
    layout="wide"
)

st.title("🌍 LTD BOT Dashboard")

# Heartbeat

if os.path.exists("heartbeat.json"):

    with open("heartbeat.json","r") as f:
        hb = json.load(f)

    st.success("BOT ONLINE")

    st.write(
        f"Última execução: {hb['last_run']}"
    )

else:

    st.error("BOT OFFLINE")

# CPU

cpu = psutil.cpu_percent()

# RAM

ram = psutil.virtual_memory().percent

col1,col2 = st.columns(2)

col1.metric(
    "CPU %",
    cpu
)

col2.metric(
    "RAM %",
    ram
)

# Logs

if os.path.exists("bot_trading.log"):

    with open(
        "bot_trading.log",
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        logs = f.readlines()

    st.text_area(
        "Últimos Logs",
        "".join(logs[-50:]),
        height=400
    )