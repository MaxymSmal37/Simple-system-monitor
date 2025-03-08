import psutil
import platform
import datetime
import time
from rich.console import Console
from rich.table import Table
from tinydb import TinyDB
import matplotlib.pyplot as plt

db = TinyDB('system_info.json')
SystemData = db.table('data')   

timestamps = []
cpu_usages = []
ram_usages = []
disk_usages = []

delayTime = 1

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


console = Console()

def get_system_info():
    sysInfo = SystemInfo()

    sysInfo.collect()
    sysInfo.insert_into_db()

    table = Table(title=f"System Information {platform.node().split('.')[0]}", show_lines=True)
    table.add_column("Metrics", justify="left", style="blue", no_wrap=True)
    table.add_column("Value", justify="right", style="green")

  
    timestamps.append(sysInfo.timestamp.split(" ")[1]) 
    cpu_usages.append(sysInfo.cpu_usage)
    ram_usages.append(sysInfo.ram_usage)
    disk_usages.append(psutil.disk_usage('/').percent)


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

    return table

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

def monitor_system(delay):
    try:
        while True:
            console.clear()
            console.print(get_system_info())
            if len(timestamps) > 1 and len(timestamps) % 30 == 0:
                draw_chart()
            time.sleep(delay)
    except KeyboardInterrupt:
        console.print("\nEnd execution.")
    except:
        console.print("\nIt's looks something wrong.")

if __name__ == "__main__":
    monitor_system(delayTime)