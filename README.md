# 📡 API Health Monitor

CLI de Python que monitorea APIs continuamente, detecta caídas, mide latencia y genera un **dashboard HTML** con historial.

## ✨ Features

- ✅ Verifica que cada API responda con el status esperado
- ⚡ Mide latencia en milisegundos
- 🔄 Detecta si el contenido de la respuesta cambió
- 📉 Historial de caídas con timestamps
- 📊 Dashboard HTML con sparklines, uptime % y métricas por API
- ⏱️ Modo monitor: corre automáticamente cada X minutos

---

## 🚀 Instalación

```bash
git clone https://github.com/dabidpq/api-health-monitor
cd api-health-monitor

python -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

---

## ⚙️ Configurar APIs

Editá `apis.json` con las APIs que querés monitorear:

```json
[
  {
    "name": "Mi API",
    "url": "https://mi-api.com/health",
    "method": "GET",
    "expected_status": 200,
    "timeout": 10
  }
]
```

---

## ▶️ Uso

```bash
# Chequeo único + abre el reporte HTML
python main.py check

# Monitoreo continuo cada 5 minutos
python main.py monitor

# Monitoreo cada 2 minutos
python main.py monitor --interval 2

# Ver estado en la terminal sin HTML
python main.py status

# Ayuda
python main.py --help
```

---

## 🗂️ Estructura

```
api-health-monitor/
├── main.py              # CLI (Typer) — comandos check, monitor, status
├── apis.json            # Lista de APIs a monitorear
├── requirements.txt
├── src/
│   ├── checker.py       # Hace las requests y mide latencia/hash
│   ├── storage.py       # Guarda y lee el historial en JSON
│   └── reporter.py      # Genera el dashboard HTML
└── data/
    ├── history.json     # Historial de todos los chequeos
    └── report.html      # Último reporte generado
```

---

## 🛠️ Stack

| Herramienta | Uso |
|---|---|
| Python 3.10+ | Lenguaje base |
| requests | HTTP requests a las APIs |
| Typer | CLI con subcomandos |
| Rich | Output con tablas y colores |

---

## 📄 Licencia

MIT
