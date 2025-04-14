import streamlit as st
import pandas as pd
from tinydb import TinyDB
import os

DB_PATH = 'system_info.json'
LOG_PATH = 'system_info_llm_log.md'

def load_data(n=50):
    db = TinyDB(DB_PATH)
    table = db.table('data')
    return table.all()[-n:] if table else []

def main():
    st.set_page_config(page_title="System Monitor", layout="wide")
    st.title("System Information Dashboard")

    data = load_data()
    if not data:
        st.warning("No system data found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    df = df.sort_index()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("CPU Usage")
        st.line_chart(df['cpu_usage'], use_container_width=True)

    with col2:
        st.subheader("RAM Usage")
        st.line_chart(df['ram_usage'], use_container_width=True)

    with col3:
        st.subheader("Battery Pesantage")
        if 'battery_persentage' in df:
            st.line_chart(df['battery_persentage'], use_container_width=True)
        else:
            st.info("Battery data not available.")

    # Аналіз з Markdown
    st.subheader("Ollama LLM Analysis")
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            st.markdown(f.read())
    else:
        st.info("LLM analysis log not found.")


    # Таблиця з усіма записами
    st.subheader("All Recent System Data")
    st.dataframe(df)

if __name__ == "__main__":
    main()