import psutil
import platform
import datetime
import time
import traceback
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
console = Console()

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
        self.ram_usage = None
        self.disk_usage = None
        self.boot_time = None
        self.battery_persentage = None
        self.battery_is_charging = None

    def collect(self):
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.os_info = f"{platform.system()} {platform.release()}"
        self.os_architecture = platform.architecture()[0]
        self.processor = platform.processor() or "Unknown"
        self.cores = psutil.cpu_count(logical=False)
        self.threads = psutil.cpu_count(logical=True)
        self.ram = psutil.virtual_memory().total / (1024**3)
        self.cpu_usage = psutil.cpu_percent(interval=0)
        self.ram_usage = psutil.virtual_memory().percent

        try:
            self.disk_usage = psutil.disk_usage('/').total / (1024**3)
        except Exception:
            self.disk_usage = None

        cpu_freq = psutil.cpu_freq()
        self.cpu_freq = cpu_freq.current if cpu_freq else None

        try:
            self.boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            self.boot_time = "N/A"

        battery = psutil.sensors_battery()
        if battery:
            self.battery_persentage = battery.percent
            self.battery_is_charging = battery.power_plugged
        else:
            self.battery_persentage = None
            self.battery_is_charging = None

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
            console.print(f"[red]DB Error:[/red] {e}")

def get_system_info():
    sysInfo = SystemInfo()

    sysInfo.collect()
    sysInfo.insert_into_db()

    table = Table(title=f"System Information - {platform.node()}", show_lines=True)
    table.add_column("Metrics", justify="left", style="blue", no_wrap=True)
    table.add_column("Value", justify="right", style="green")

    timestamps.append(sysInfo.timestamp.split(" ")[1]) 
    cpu_usages.append(sysInfo.cpu_usage or 0)
    ram_usages.append(sysInfo.ram_usage or 0)
    disk_usages.append(psutil.disk_usage('/').percent if sysInfo.disk_usage else 0)

    table.add_row("Current time", sysInfo.timestamp)
    table.add_row("Boot Time", sysInfo.boot_time)
    table.add_row("Operating System", f"{sysInfo.os_info} ({sysInfo.os_architecture})")
    table.add_row("Processor", sysInfo.processor)
    table.add_row("CPU Cores", str(sysInfo.cores))
    table.add_row("CPU Threads", str(sysInfo.threads))
    table.add_row("CPU Frequency (MHz)", f"{sysInfo.cpu_freq:.2f}" if sysInfo.cpu_freq else "N/A")
    table.add_row("RAM (GB)", f"{sysInfo.ram:.2f}")
    table.add_row("Disk Space (GB)", f"{sysInfo.disk_usage:.2f}" if sysInfo.disk_usage else "N/A")
    table.add_row("Battery Percent", f"{sysInfo.battery_persentage}%" if sysInfo.battery_persentage is not None else "N/A")
    table.add_row("Battery Charging", "Charging" if sysInfo.battery_is_charging else "Unplugged" if sysInfo.battery_is_charging is not None else "N/A")

    return table

def draw_chart():    
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, cpu_usages, label="CPU Usage (%)", color='red', marker='o')
    plt.plot(timestamps, ram_usages, label="Memory Usage (%)", color='blue', marker='o')
    plt.plot(timestamps, disk_usages, label="Disk Usage (%)", color='green', marker='o')

    plt.xlabel('Time')
    plt.ylabel('Usage (%)')
    plt.title('System Resource Usage')
    plt.xticks(rotation=90)
    plt.legend(loc="upper left")
    plt.tight_layout()
    # Comment this out in Docker unless you're forwarding display
    # plt.show()
    plt.savefig("resource_chart.png")

def monitor_system(delay):
    try:
        while True:
            console.clear()
            console.print(get_system_info())
            if len(timestamps) > 1 and len(timestamps) % 30 == 0:
                draw_chart()
            time.sleep(delay)
    except KeyboardInterrupt:
        console.print("\n[bold red]Execution stopped by user.[/bold red]")
    except Exception as e:
        console.print(f"[red]Something went wrong:[/red] {e}")
        traceback.print_exc()

if __name__ == "__main__":
    monitor_system(delayTime)
