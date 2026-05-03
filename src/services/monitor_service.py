import psutil
import asyncio
from typing import Dict, Optional
from datetime import datetime
from src.utils.logger import logger


class MonitorService:
    """Service for system monitoring"""

    def __init__(self):
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0
        }

    async def get_system_stats(self) -> Dict:
        """
        Get current system statistics

        Returns:
            Dict with CPU, memory, disk stats
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 ** 3)  # GB
            memory_used = memory.used / (1024 ** 3)  # GB
            memory_percent = memory.percent

            # Disk
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024 ** 3)  # GB
            disk_used = disk.used / (1024 ** 3)  # GB
            disk_percent = disk.percent

            # Network
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent / (1024 ** 2)  # MB
            bytes_recv = net_io.bytes_recv / (1024 ** 2)  # MB

            # Uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            stats = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'total_gb': round(memory_total, 2),
                    'used_gb': round(memory_used, 2),
                    'percent': memory_percent
                },
                'disk': {
                    'total_gb': round(disk_total, 2),
                    'used_gb': round(disk_used, 2),
                    'percent': disk_percent
                },
                'network': {
                    'sent_mb': round(bytes_sent, 2),
                    'recv_mb': round(bytes_recv, 2)
                },
                'uptime': str(uptime).split('.')[0]  # Remove microseconds
            }

            logger.info(f"System stats collected: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%")
            return stats

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            raise

    async def get_docker_stats(self) -> Optional[Dict]:
        """
        Get Docker container statistics

        Returns:
            Dict with container stats or None if Docker not available
        """
        try:
            import docker
            client = docker.from_env()

            containers = client.containers.list()
            container_stats = []

            for container in containers:
                stats = container.stats(stream=False)

                # Calculate CPU percentage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0

                # Memory
                memory_usage = stats['memory_stats'].get('usage', 0) / (1024 ** 2)  # MB
                memory_limit = stats['memory_stats'].get('limit', 0) / (1024 ** 2)  # MB
                memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0

                container_stats.append({
                    'name': container.name,
                    'status': container.status,
                    'cpu_percent': round(cpu_percent, 2),
                    'memory_mb': round(memory_usage, 2),
                    'memory_percent': round(memory_percent, 2)
                })

            logger.info(f"Docker stats collected for {len(containers)} containers")
            return {
                'containers': container_stats,
                'total_containers': len(containers)
            }

        except ImportError:
            logger.warning("Docker library not available")
            return None
        except Exception as e:
            logger.error(f"Error getting Docker stats: {e}")
            return None

    async def check_alerts(self, stats: Dict) -> list:
        """
        Check if any metrics exceed thresholds

        Args:
            stats: System statistics dict

        Returns:
            List of alert messages
        """
        alerts = []

        # CPU alert
        if stats['cpu']['percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append(f"⚠️ CPU usage high: {stats['cpu']['percent']}%")

        # Memory alert
        if stats['memory']['percent'] > self.alert_thresholds['memory_percent']:
            alerts.append(f"⚠️ Memory usage high: {stats['memory']['percent']}%")

        # Disk alert
        if stats['disk']['percent'] > self.alert_thresholds['disk_percent']:
            alerts.append(f"⚠️ Disk usage high: {stats['disk']['percent']}%")

        if alerts:
            logger.warning(f"Alerts triggered: {alerts}")

        return alerts

    def set_threshold(self, metric: str, value: float) -> bool:
        """
        Set alert threshold for a metric

        Args:
            metric: Metric name (cpu_percent, memory_percent, disk_percent)
            value: Threshold value (0-100)

        Returns:
            True if successful
        """
        if metric not in self.alert_thresholds:
            return False

        if not 0 <= value <= 100:
            return False

        self.alert_thresholds[metric] = value
        logger.info(f"Threshold updated: {metric} = {value}%")
        return True

    def get_thresholds(self) -> Dict:
        """Get current alert thresholds"""
        return self.alert_thresholds.copy()


# Global monitor service instance
monitor_service = MonitorService()
