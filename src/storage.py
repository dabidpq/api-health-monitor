import json
from pathlib import Path

HISTORY_FILE = Path("data/history.json")
MAX_RECORDS_PER_API = 100  # Máximo de registros por API para no crecer infinito


def load_history() -> dict:
    """Carga el historial completo desde disco."""
    if not HISTORY_FILE.exists():
        return {}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history: dict):
    """Guarda el historial completo en disco."""
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def append_result(result: dict):
    """
    Agrega un nuevo resultado al historial de su API.
    Detecta si el contenido cambió respecto al último registro.
    """
    history = load_history()
    name = result["name"]

    if name not in history:
        history[name] = []

    records = history[name]

    # Detectar cambio de contenido
    content_changed = False
    if records and result["content_hash"]:
        last_hash = records[-1].get("content_hash")
        if last_hash and last_hash != result["content_hash"]:
            content_changed = True

    result["content_changed"] = content_changed

    # Agregar y recortar si excede el máximo
    records.append(result)
    history[name] = records[-MAX_RECORDS_PER_API:]

    save_history(history)
    return history


def get_summary(history: dict) -> list:
    """
    Retorna un resumen por API: último estado, uptime %, latencia promedio,
    total de caídas y si el contenido cambió recientemente.
    """
    summaries = []

    for name, records in history.items():
        if not records:
            continue

        last = records[-1]
        total = len(records)
        up_count = sum(1 for r in records if r.get("is_up"))
        uptime_pct = round((up_count / total) * 100, 1) if total else 0

        latencies = [r["latency_ms"] for r in records if r.get("latency_ms") is not None]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None

        downtime_events = sum(1 for r in records if not r.get("is_up"))
        content_changes = sum(1 for r in records if r.get("content_changed"))

        summaries.append({
            "name": name,
            "url": last["url"],
            "is_up": last.get("is_up", False),
            "status_code": last.get("status_code"),
            "latency_ms": last.get("latency_ms"),
            "avg_latency_ms": avg_latency,
            "uptime_pct": uptime_pct,
            "downtime_events": downtime_events,
            "content_changes": content_changes,
            "last_checked": last["timestamp"],
            "error": last.get("error"),
            "records": records,
        })

    return summaries
