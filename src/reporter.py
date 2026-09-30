import webbrowser
from datetime import datetime
from pathlib import Path


def _latency_color(ms):
    if ms is None:
        return "#6b7280"
    if ms < 300:
        return "#22c55e"
    if ms < 800:
        return "#f59e0b"
    return "#ef4444"


def _status_badge(is_up, status_code, error):
    if error:
        return f'<span class="badge badge-down">ERROR</span>'
    if is_up:
        return f'<span class="badge badge-up">{status_code} UP</span>'
    return f'<span class="badge badge-down">{status_code or "—"} DOWN</span>'


def _sparkline(records):
    """Mini gráfico SVG de latencia de los últimos 20 registros."""
    points = [r["latency_ms"] for r in records[-20:] if r.get("latency_ms") is not None]
    if len(points) < 2:
        return "<span style='color:#6b7280;font-size:12px'>Sin datos</span>"

    w, h = 120, 30
    max_v = max(points) or 1
    coords = []
    for i, v in enumerate(points):
        x = i * (w / (len(points) - 1))
        y = h - (v / max_v) * h
        coords.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(coords)
    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">
      <polyline points="{polyline}" fill="none" stroke="#6366f1" stroke-width="2" stroke-linejoin="round"/>
    </svg>'''


def _history_rows(records):
    rows = ""
    for r in reversed(records[-10:]):
        ts = r["timestamp"].replace("T", " ").split(".")[0]
        status = "✅" if r.get("is_up") else "❌"
        latency = f"{r['latency_ms']} ms" if r.get("latency_ms") else "—"
        changed = "⚠️ Sí" if r.get("content_changed") else "No"
        error = r.get("error") or "—"
        rows += f"""
        <tr>
          <td>{ts}</td>
          <td>{status} {r.get('status_code') or error}</td>
          <td>{latency}</td>
          <td>{changed}</td>
        </tr>"""
    return rows


def generate_report(summaries: list, output_path: str = "data/report.html", open_browser: bool = True):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(summaries)
    up_count = sum(1 for s in summaries if s["is_up"])
    down_count = total - up_count

    cards = ""
    for s in summaries:
        latency_color = _latency_color(s["latency_ms"])
        badge = _status_badge(s["is_up"], s["status_code"], s["error"])
        sparkline = _sparkline(s["records"])
        history = _history_rows(s["records"])
        card_border = "#22c55e" if s["is_up"] else "#ef4444"

        cards += f"""
        <div class="card" style="border-top: 4px solid {card_border}">
          <div class="card-header">
            <div>
              <div class="api-name">{s['name']}</div>
              <div class="api-url">{s['url']}</div>
            </div>
            {badge}
          </div>

          <div class="metrics">
            <div class="metric">
              <div class="metric-value" style="color:{latency_color}">
                {f"{s['latency_ms']} ms" if s['latency_ms'] else "—"}
              </div>
              <div class="metric-label">Latencia actual</div>
            </div>
            <div class="metric">
              <div class="metric-value">{f"{s['avg_latency_ms']} ms" if s['avg_latency_ms'] else "—"}</div>
              <div class="metric-label">Latencia promedio</div>
            </div>
            <div class="metric">
              <div class="metric-value" style="color:#22c55e">{s['uptime_pct']}%</div>
              <div class="metric-label">Uptime</div>
            </div>
            <div class="metric">
              <div class="metric-value" style="color:#ef4444">{s['downtime_events']}</div>
              <div class="metric-label">Caídas</div>
            </div>
            <div class="metric">
              <div class="metric-value" style="color:#f59e0b">{s['content_changes']}</div>
              <div class="metric-label">Cambios de contenido</div>
            </div>
          </div>

          <div class="sparkline-section">
            <div class="sparkline-label">Latencia (últimas mediciones)</div>
            {sparkline}
          </div>

          <details>
            <summary>Últimas 10 mediciones</summary>
            <table class="history-table">
              <thead><tr><th>Timestamp</th><th>Status</th><th>Latencia</th><th>Contenido cambió</th></tr></thead>
              <tbody>{history}</tbody>
            </table>
          </details>

          <div class="last-checked">Última verificación: {s['last_checked'].replace('T',' ').split('.')[0]} UTC</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>API Health Monitor</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }}

    header {{ background: #1e293b; padding: 24px 32px; border-bottom: 1px solid #334155; }}
    header h1 {{ font-size: 22px; font-weight: 700; color: #f8fafc; }}
    header p {{ color: #94a3b8; font-size: 13px; margin-top: 4px; }}

    .summary-bar {{ display: flex; gap: 16px; padding: 20px 32px; background: #1e293b; border-bottom: 1px solid #334155; }}
    .summary-pill {{ padding: 6px 16px; border-radius: 999px; font-size: 13px; font-weight: 600; }}
    .pill-total {{ background: #334155; color: #e2e8f0; }}
    .pill-up {{ background: #14532d; color: #4ade80; }}
    .pill-down {{ background: #7f1d1d; color: #f87171; }}

    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; padding: 28px 32px; }}

    .card {{ background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
    .api-name {{ font-size: 16px; font-weight: 700; color: #f8fafc; }}
    .api-url {{ font-size: 12px; color: #64748b; margin-top: 2px; word-break: break-all; }}

    .badge {{ padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }}
    .badge-up {{ background: #14532d; color: #4ade80; }}
    .badge-down {{ background: #7f1d1d; color: #f87171; }}

    .metrics {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }}
    .metric {{ background: #0f172a; border-radius: 8px; padding: 10px 14px; flex: 1; min-width: 80px; }}
    .metric-value {{ font-size: 18px; font-weight: 700; }}
    .metric-label {{ font-size: 11px; color: #64748b; margin-top: 2px; }}

    .sparkline-section {{ margin-bottom: 16px; }}
    .sparkline-label {{ font-size: 11px; color: #64748b; margin-bottom: 4px; }}

    details {{ margin-bottom: 12px; }}
    summary {{ cursor: pointer; font-size: 13px; color: #94a3b8; padding: 6px 0; user-select: none; }}
    summary:hover {{ color: #e2e8f0; }}

    .history-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }}
    .history-table th {{ text-align: left; padding: 6px 8px; color: #64748b; border-bottom: 1px solid #334155; }}
    .history-table td {{ padding: 6px 8px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
    .history-table tr:hover td {{ background: #0f172a; }}

    .last-checked {{ font-size: 11px; color: #475569; margin-top: 8px; }}

    footer {{ text-align: center; padding: 20px; color: #475569; font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>📡 API Health Monitor</h1>
    <p>Reporte generado: {now}</p>
  </header>

  <div class="summary-bar">
    <span class="summary-pill pill-total">Total: {total}</span>
    <span class="summary-pill pill-up">✅ Activas: {up_count}</span>
    <span class="summary-pill pill-down">❌ Caídas: {down_count}</span>
  </div>

  <div class="grid">
    {cards}
  </div>

  <footer>API Health Monitor · Datos almacenados localmente en data/history.json</footer>
</body>
</html>"""

    Path(output_path).parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    if open_browser:
        webbrowser.open(f"file://{Path(output_path).resolve()}")

    return output_path
