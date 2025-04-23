import streamlit as st
import pandas as pd
import datetime
import time
from tinydb import TinyDB
import requests
import json
from streamlit_autorefresh import st_autorefresh

DB_PATH = 'system_info.json'
LOG_PATH = 'system_info_llm_log.md'

db = TinyDB(DB_PATH)
SystemData = db.table('data')

def collect_system_info():
    import platform
    import psutil

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    battery = psutil.sensors_battery()
    data = {
        'time': now,
        'os_info': f"{platform.system()} {platform.release()}",
        'processor': platform.processor(),
        'os_architecture': platform.architecture()[0],
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True),
        'ram': psutil.virtual_memory().total / (1024**3),
        'cpu_usage': psutil.cpu_percent(interval=0),
        'ram_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').total / (1024**3),
        'cpu_freq': psutil.cpu_freq().current,
        'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
        'battery_persentage': battery.percent if battery else None,
        'battery_is_charging': battery.power_plugged if battery else None
    }

    SystemData.insert(data)
    return data

def generate_llm_prompt(info):
    return f"""
Below is the latest system diagnostic data.

Last update: {info['time']}
Analyze it and answer the following:
1. Are there any signs of CPU, memory, or disk overload?
2. What could be the causes?
3. What actions do you recommend?

Data:
{json.dumps(info, indent=2)}
"""

def stream_llm_response(prompt):
    url = "http://127.0.0.1:11434/v1/chat/completions"
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": "llama3.2:1b",
        "stream": True,
        "messages": [{"role": "user", "content": prompt}]
    }

    with requests.post(url, headers=headers, json=data, stream=True) as response:
        for line in response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode("utf-8").strip()
                    if decoded_line.startswith("data:"):
                        decoded_line = decoded_line[len("data:"):].strip()
                    chunk = json.loads(decoded_line)
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        yield delta
                except Exception as e:
                    yield f"\n[Stream error: {e}]\n"

def load_recent_data(n=50):
    return SystemData.all()[-n:]

def main():
    st.set_page_config(page_title="System Monitor", layout="wide")
    st.title("System Monitor with LLM (Streaming)")

    # 🔁 Auto-refresh every 15 sec
    st_autorefresh(interval=15_000, key="data_refresh")

    info = collect_system_info()
    df = pd.DataFrame(load_recent_data())
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    df = df.sort_index()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("CPU Usage")
        st.line_chart(df['cpu_usage'])

    with col2:
        st.subheader("RAM Usage")
        st.line_chart(df['ram_usage'])

    with col3:
        st.subheader("Battery")
        if 'battery_persentage' in df:
            st.line_chart(df['battery_persentage'])
        else:
            st.info("No battery data.")

    st.subheader("LLM Analysis")
    prompt = generate_llm_prompt(info)
    analysis_placeholder = st.empty()
    full_analysis = ""

    for chunk in stream_llm_response(prompt):
        full_analysis += chunk
        analysis_placeholder.markdown(full_analysis)

    # Save to log
    with open(LOG_PATH, "w") as f:
        f.write(f"System Information Analysis ({info['time']}):\n\n{full_analysis}\n")

    st.subheader("Raw System Data")
    st.dataframe(df)

if __name__ == "__main__":
    main()
