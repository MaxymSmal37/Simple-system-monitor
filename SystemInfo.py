import psutil
import platform
import datetime
import time
from rich.console import Console
from rich.table import Table
from tinydb import TinyDB
import matplotlib.pyplot as plt
import requests
import json
import os

db = TinyDB('system_info.json')
SystemData = db.table('data')   

timestamps = []
cpu_usages = []
ram_usages = []
disk_usages = []

delayTime = 1
logDelayTime = 30

class SystemInfo:
    def __init__(self):
        self.timestamp = None
        self.os_info = None
        self.os_architecture = None
        self.processor = None
        self.cores = None
        self.threads = None
        self.ram = None
        self.cpu_usage = None
        self.cpu_freq = None
        self.cpu_temp = None
        self.ram_usage = None
        self.disk_usage = None
        self.boot_time = None
        self.battery_persentage = None
        self.battery_is_charging  = None

    def collect(self):
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.os_info = f"{platform.system()} {platform.release()}"
        self.processor = platform.processor()
        self.os_architecture = platform.architecture()[0] 
        self.cores = psutil.cpu_count(logical=False)
        self.threads = psutil.cpu_count(logical=True)
        self.ram = psutil.virtual_memory().total / (1024**3)
        self.cpu_usage = psutil.cpu_percent(interval=0)
        self.ram_usage = psutil.virtual_memory().percent
        self.disk_usage = psutil.disk_usage('/').total / (1024**3)
        self.cpu_freq = psutil.cpu_freq().current
        self.boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")  
        self.battery_persentage =  psutil.sensors_battery().percent
        self.battery_is_charging =  psutil.sensors_battery().power_plugged

    def insert_into_db(self):  
        try:
            SystemData.insert({
            'time': self.timestamp,
            'os_info': self.os_info,
            'processor': self.processor,
            'os_architecture': self.os_architecture,
            'cores': self.cores,
            'threads': self.threads,
            'ram': self.ram,
            'cpu_usage': self.cpu_usage,
            'cpu_freq': self.cpu_freq,
            'ram_usage': self.ram_usage,
            'disk_usage': self.disk_usage,
            'boot_time': self.boot_time,
            'battery_persentage': self.battery_persentage,
            'battery_is_charging': self.battery_is_charging
        })

        except Exception as e:
            print(f"Error inserting data into database: {e}")

def get_data_from_db():
    data = SystemData.all()[-1]  # Get the most recent entry
    return data

def generate_llm_prompt(sysInfo):
    prompt = f"""
Below is the latest system diagnostic data.

Last update: {sysInfo['time']}
Analyze it and answer the following questions:
1. Are there any signs of CPU, memory, or disk overload?
2. What are the possible causes of the problems you are experiencing?
3. What actions do you recommend to improve system performance?

Data:
{{
"Timestamp": "{sysInfo['time']}",
"Operating System": "{sysInfo['os_info']} {sysInfo['os_architecture']}",
"Processor": "{sysInfo['processor']}",
"CPU Cores": {sysInfo['cores']},
"CPU Threads": {sysInfo['threads']},
"CPU Frequency (MHz)": {sysInfo['cpu_freq']},
"CPU Usage (%)": {sysInfo['cpu_usage']},
"RAM (GB)": {sysInfo['ram']:.2f},
"RAM Usage (%)": {sysInfo['ram_usage']},
"Disk Space (GB)": {sysInfo['disk_usage']:.2f},
"Boot Time": "{sysInfo['boot_time']}",
"Battery Percentage": {sysInfo['battery_persentage']},
"Charging": {"true" if sysInfo['battery_is_charging'] else "false"}
}}
"""
    return prompt.strip()

def query_ollama(prompt):
    url = "http://127.0.0.1:11434/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "model": "llama3.2:1b", 
        "messages": [{"role": "system", "content": prompt}],
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        response_data = response.json()
        analysis_raw = response_data['choices'][0]['message']['content']
        analysis = analysis_raw.replace("<|start_header_id|>", "").replace("<|end_header_id|>", "")
        return analysis
    else:
        return "Error: Unable to get response from Ollama API."

log_file_path = "system_info_llm_log.md"

def write_to_log(content, analysis):
    with open(log_file_path, "w") as log_file:
        log_file.write(f"System Information and Analysis (Updated: {content['time']}):\n")
        log_file.write(f"Ollama Analysis:\n{analysis}\n")

def display_table(sysInfo):
    table = Table(title=f"System Information {platform.node().split('.')[0]}", show_lines=True)
    table.add_column("Metrics", justify="left", style="blue", no_wrap=True)
    table.add_column("Value", justify="right", style="green")

    table.add_row("Current time", sysInfo.timestamp)
    table.add_row("Boot Time", f"{sysInfo.boot_time}")
    table.add_row("Operating System", str(sysInfo.os_info) + " " + str(sysInfo.os_architecture))
    table.add_row("Processor", sysInfo.processor)
    table.add_row("CPU Cores", str(sysInfo.cores))
    table.add_row("CPU Threads", str(sysInfo.threads))
    table.add_row("CPU frequency (MHz)", f"{sysInfo.cpu_freq}")
    table.add_row("RAM (GB)", f"{sysInfo.ram:.2f} GB")
    table.add_row("Disk Space (GB)", f"{sysInfo.disk_usage:.2f} GB")
    table.add_row("Battery charging percent", f"{sysInfo.battery_persentage:} ")
    table.add_row("Battery charging", "Charging" if sysInfo.battery_is_charging else "Unplugged")
    
    console = Console()
    console.print(table)

def draw_chart():    
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, cpu_usages, label="CPU Usage (%)", color='red', marker='o')
    plt.plot(timestamps, ram_usages, label="Memory Usage (%)", color='blue', marker='o')
    plt.plot(timestamps, disk_usages, label="Disk Usage (%)", color='green', marker='o')

    plt.xlabel('Time')
    plt.ylabel('Usage (%)')
    plt.title('System Resource')
    plt.xticks(rotation=90)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.show()
def monitor_system():
    try:
        last_update_time = time.time() 
        while True:
            sysInfo = SystemInfo()
            sysInfo.collect()  
            sysInfo.insert_into_db()

            data = get_data_from_db()

            display_table(sysInfo)

            if time.time() - last_update_time >= logDelayTime:
                last_update_time = time.time() 

                llm_prompt = generate_llm_prompt(data)
                analysis = query_ollama(llm_prompt)

                write_to_log(data, analysis) 

            time.sleep(delayTime)

    except KeyboardInterrupt:
        console.print("\nEnd execution.")
    except:
        console.print("\nIt's looks something wrong.")

if __name__ == "__main__":
    monitor_system()
