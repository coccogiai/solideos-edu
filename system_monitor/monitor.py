"""
시스템 리소스 모니터링 모듈
CPU, GPU, 메모리, 디스크, 네트워크 등 모든 시스템 리소스를 수집합니다.
"""

import psutil
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# GPU 모니터링 (선택적)
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Windows WMI (온도 센서용)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


class SystemMonitor:
    """시스템 리소스를 수집하는 모니터 클래스"""
    
    def __init__(self):
        self.prev_net_io = psutil.net_io_counters()
        self.prev_disk_io = psutil.disk_io_counters()
        self.prev_time = time.time()
        
        # WMI 초기화 (Windows 온도 센서)
        self.wmi_client = None
        if WMI_AVAILABLE:
            try:
                self.wmi_client = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            except Exception:
                try:
                    self.wmi_client = wmi.WMI(namespace="root\\WMI")
                except Exception:
                    self.wmi_client = None
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """CPU 정보 수집"""
        cpu_percent = psutil.cpu_percent(interval=0)
        cpu_percent_per_core = psutil.cpu_percent(interval=0, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        
        # CPU 온도 (Windows)
        cpu_temp = self._get_cpu_temperature()
        
        return {
            "usage_percent": cpu_percent,
            "per_core_percent": cpu_percent_per_core,
            "frequency_current": cpu_freq.current if cpu_freq else 0,
            "frequency_max": cpu_freq.max if cpu_freq else 0,
            "core_count_logical": cpu_count,
            "core_count_physical": cpu_count_physical,
            "temperature": cpu_temp
        }
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """CPU 온도 가져오기 (Windows)"""
        if self.wmi_client:
            try:
                sensors = self.wmi_client.Sensor()
                for sensor in sensors:
                    if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                        return float(sensor.Value)
            except Exception:
                pass
        
        # psutil을 통한 온도 (Linux/macOS)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if "core" in entry.label.lower() or "cpu" in name.lower():
                            return entry.current
        except Exception:
            pass
        
        return None
    
    def get_memory_info(self) -> Dict[str, Any]:
        """메모리(RAM) 정보 수집"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "usage_percent": mem.percent,
            "swap_total_gb": round(swap.total / (1024 ** 3), 2),
            "swap_used_gb": round(swap.used / (1024 ** 3), 2),
            "swap_percent": swap.percent
        }
    
    def get_disk_info(self) -> Dict[str, Any]:
        """디스크 정보 수집"""
        partitions = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "usage_percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
        
        # 디스크 I/O 속도 계산
        current_time = time.time()
        current_disk_io = psutil.disk_io_counters()
        time_delta = current_time - self.prev_time
        
        if time_delta > 0 and current_disk_io:
            read_speed = (current_disk_io.read_bytes - self.prev_disk_io.read_bytes) / time_delta
            write_speed = (current_disk_io.write_bytes - self.prev_disk_io.write_bytes) / time_delta
        else:
            read_speed = 0
            write_speed = 0
        
        self.prev_disk_io = current_disk_io
        
        return {
            "partitions": partitions,
            "io_read_speed_mbps": round(read_speed / (1024 ** 2), 2),
            "io_write_speed_mbps": round(write_speed / (1024 ** 2), 2)
        }
    
    def get_network_info(self) -> Dict[str, Any]:
        """네트워크 정보 수집"""
        current_time = time.time()
        current_net_io = psutil.net_io_counters()
        time_delta = current_time - self.prev_time
        
        if time_delta > 0:
            upload_speed = (current_net_io.bytes_sent - self.prev_net_io.bytes_sent) / time_delta
            download_speed = (current_net_io.bytes_recv - self.prev_net_io.bytes_recv) / time_delta
        else:
            upload_speed = 0
            download_speed = 0
        
        self.prev_net_io = current_net_io
        self.prev_time = current_time
        
        # 네트워크 인터페이스 정보
        interfaces = []
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for iface_name, addrs in net_if_addrs.items():
            stats = net_if_stats.get(iface_name)
            if stats and stats.isup:
                ip_addr = None
                for addr in addrs:
                    if addr.family.name == 'AF_INET':
                        ip_addr = addr.address
                        break
                if ip_addr:
                    interfaces.append({
                        "name": iface_name,
                        "ip": ip_addr,
                        "speed_mbps": stats.speed if stats.speed > 0 else None
                    })
        
        return {
            "upload_speed_mbps": round(upload_speed * 8 / (1024 ** 2), 2),
            "download_speed_mbps": round(download_speed * 8 / (1024 ** 2), 2),
            "upload_speed_kbps": round(upload_speed * 8 / 1024, 2),
            "download_speed_kbps": round(download_speed * 8 / 1024, 2),
            "total_sent_gb": round(current_net_io.bytes_sent / (1024 ** 3), 2),
            "total_recv_gb": round(current_net_io.bytes_recv / (1024 ** 3), 2),
            "interfaces": interfaces
        }
    
    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """GPU 정보 수집"""
        gpus = []
        
        if GPU_AVAILABLE:
            try:
                gpu_list = GPUtil.getGPUs()
                for gpu in gpu_list:
                    gpus.append({
                        "id": gpu.id,
                        "name": gpu.name,
                        "load_percent": round(gpu.load * 100, 1),
                        "memory_used_mb": round(gpu.memoryUsed, 1),
                        "memory_total_mb": round(gpu.memoryTotal, 1),
                        "memory_percent": round(gpu.memoryUtil * 100, 1) if gpu.memoryUtil else 0,
                        "temperature": gpu.temperature,
                        "driver": gpu.driver
                    })
            except Exception:
                pass
        
        return gpus
    
    def get_process_info(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """상위 N개 프로세스 정보"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu_percent": info['cpu_percent'] or 0,
                    "memory_percent": round(info['memory_percent'] or 0, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # CPU 사용량 기준 정렬
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:top_n]
    
    def get_system_info(self) -> Dict[str, Any]:
        """시스템 기본 정보"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime_hours": round(uptime.total_seconds() / 3600, 1),
            "platform": psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else "Unknown"
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """모든 시스템 통계 수집"""
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
            "gpu": self.get_gpu_info(),
            "processes": self.get_process_info(),
            "system": self.get_system_info()
        }


# 테스트용
if __name__ == "__main__":
    monitor = SystemMonitor()
    import json
    
    # 초기 데이터 수집 (속도 계산용)
    time.sleep(1)
    
    stats = monitor.get_all_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
