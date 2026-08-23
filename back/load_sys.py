from datetime import datetime

import psutil

def get_system_load():
    value_cpu = psutil.cpu_percent(interval=1)                                      #CPU
    value_ram_b = psutil.virtual_memory()                                             #RAM
    value_disk_b = psutil.disk_usage('/')                                              #SSD/HDD
    value_time = datetime.now() - datetime.fromtimestamp(psutil.boot_time())         #run_time

    return {
        "CPU": value_cpu,
        "RAM": value_ram_b.percent,
        "disk": value_disk_b.percent,
        "run_time": str(value_time).split('.')[0]
    }