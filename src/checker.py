import hashlib
import time
import requests
from datetime import datetime, timezone


def check_api(api: dict) -> dict:
    """
    Hace una request a la API y retorna un dict con todos los resultados.
    """
    name = api["name"]
    url = api["url"]
    method = api.get("method", "GET").upper()
    expected_status = api.get("expected_status", 200)
    timeout = api.get("timeout", 10)

    result = {
        "name": name,
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": None,
        "latency_ms": None,
        "is_up": False,
        "expected_status": expected_status,
        "content_hash": None,
        "error": None,
    }

    try:
        start = time.perf_counter()
        response = requests.request(method, url, timeout=timeout)
        elapsed = time.perf_counter() - start

        result["status_code"] = response.status_code
        result["latency_ms"] = round(elapsed * 1000, 2)
        result["is_up"] = response.status_code == expected_status

        # Hash del contenido para detectar cambios
        content = response.text.strip()
        result["content_hash"] = hashlib.md5(content.encode()).hexdigest()

    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection error"
    except Exception as e:
        result["error"] = str(e)

    return result
