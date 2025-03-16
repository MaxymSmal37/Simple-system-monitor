import psutil
import platform
import datetime
import time
import threading
from rich.console import Console
from rich.table import Table

delayTime = 1
console = Console()

class SystemInfo:
    def __init__(self):
        self.lock = threading.Lock()
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
        self.battery_percentage = None
        self.battery_is_charging = None
        self.thread = threading.Thread(target=self.collect, daemon=True)
        self.thread.start()

    def collect(self):
        """Постійне оновлення системної інформації в окремому потоці"""
        while True:
            with self.lock:
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
                battery = psutil.sensors_battery()
                if battery:
                    self.battery_percentage = battery.percent
                    self.battery_is_charging = battery.power_plugged
                else:
                    self.battery_percentage = "N/A"
                    self.battery_is_charging = "N/A"

            time.sleep(delayTime) 

def get_system_info(sys_info):
    with sys_info.lock:
        table = Table(title=f"System Information {platform.node().split('.')[0]}", show_lines=True)
        table.add_column("Metrics", justify="left", style="blue", no_wrap=True)
        table.add_column("Value", justify="right", style="green")

        table.add_row("Current time", sys_info.timestamp)
        table.add_row("Boot Time", sys_info.boot_time)
        table.add_row("Operating System", str(sys_info.os_info) + " " + str(sys_info.os_architecture))
        table.add_row("Processor", sys_info.processor)
        table.add_row("CPU Cores", str(sys_info.cores))
        table.add_row("CPU Threads", str(sys_info.threads))
        table.add_row("CPU frequency (MHz)", f"{sys_info.cpu_freq}")
        table.add_row("RAM (GB)", f"{sys_info.ram:.2f} GB")
        table.add_row("Disk Space (GB)", f"{sys_info.disk_usage:.2f} GB")
        table.add_row("Battery charging percent", f"{sys_info.battery_percentage}")
        table.add_row("Battery charging", "Charging" if sys_info.battery_is_charging else "Unplugged")

        return table

def monitor_system(sys_info):
    try:
        while True:
            console.clear()
            console.print(get_system_info(sys_info))
            time.sleep(delayTime)
    except KeyboardInterrupt:
        console.print("\nEnd execution.")
    except Exception as e:
        console.print(f"\nSomething went wrong: {e}")

if __name__ == "__main__":
    sys_info = SystemInfo() 
    monitor_system(sys_info)