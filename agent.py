import requests
import subprocess
import time
import json
from datetime import datetime, timezone

def ping(host):
    cmd = ["ping", "-n", "4", host]  # Windows: -n; Linux: use -c
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return {
        "host": host,
        "time": datetime.now(timezone.utc).isoformat(),
        "status": "success" if proc.returncode == 0 else "fail",
        "output": proc.stdout
    }

def http_test(url):
    try:
        r = requests.get(url, timeout=5)
        return {
            "url": url,
            "status_code": r.status_code,
            "time": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "time": datetime.now(timezone.utc).isoformat()
        }

def tracert(host):
    cmd = ["tracert", host]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return {
            "host": host,
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "success" if proc.returncode == 0 else "fail",
            "output": proc.stdout
        }
    except FileNotFoundError as e:
        return {
            "host": host,
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "output": str(e)
        }

def pathping(host):
    cmd = ["pathping", "-q", "5", "-h", "10", host]  # limit queries and hops
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
        return {
            "host": host,
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "success" if proc.returncode == 0 else "fail",
            "output": proc.stdout
        }
    except FileNotFoundError as e:
        return {
            "host": host,
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "output": str(e)
        }
    except subprocess.TimeoutExpired:
        return {
            "host": host,
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "timeout",
            "output": "Pathping timed out"
        }

def discover_path_mtu(host):
    mtu = 1472  # 1472 + 28 (ICMP header) = 1500
    step = 10
    min_mtu = 500
    while mtu > min_mtu:
        cmd = ["ping", "-f", "-l", str(mtu), host]  # Windows: -f for DF, -l for size
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "Packet needs to be fragmented" in proc.stdout or "Packet needs to be fragmented but DF set" in proc.stdout:
            mtu -= step
        else:
            break
    return {
        "host": host,
        "path_mtu": mtu,
        "time": datetime.now(timezone.utc).isoformat()
    }

def send_report(data, endpoint):
    try:
        r = requests.post(endpoint, json=data, timeout=10)
        print("Report sent, status:", r.status_code)
    except Exception as e:
        print("Failed to send report:", e)

if __name__ == '__main__':
    SERVER_ENDPOINT = "https://psjitha.pythonanywhere.com/report"
    TARGETS = ["203.99.44.1"]
    URLS = ["https://google.com"]

    while True:
        report = {
            "agent_id": "agent-100",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ping": [ping(host) for host in TARGETS],
            "http": [http_test(url) for url in URLS],
            "tracert": [tracert(host) for host in TARGETS],
            "pathping": [pathping(host) for host in TARGETS],
            "path_mtu": [discover_path_mtu(host) for host in TARGETS]
        }
        send_report(report, SERVER_ENDPOINT)
        time.sleep(60)
