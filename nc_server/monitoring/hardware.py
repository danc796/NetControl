import psutil
import logging

def get_hardware_info():
    """Monitor hardware metrics with improved drive handling"""
    try:
        disk_usage = {}

        # Safely collect disk usage information
        for partition in psutil.disk_partitions(all=False):
            try:
                # Only check fixed drives and skip removable drives
                if 'fixed' in partition.opts or partition.fstype == 'NTFS':
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = dict(usage._asdict())
            except Exception as e:
                logging.warning(f"Could not access drive {partition.mountpoint}: {e}")
                continue

        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_usage': dict(psutil.virtual_memory()._asdict()),
            'disk_usage': disk_usage,
            'network_io': dict(psutil.net_io_counters()._asdict())
        }
    except Exception as e:
        logging.error(f"Error gathering hardware info: {e}")
        return {
            'cpu_percent': 0,
            'memory_usage': {},
            'disk_usage': {},
            'network_io': {}
        }