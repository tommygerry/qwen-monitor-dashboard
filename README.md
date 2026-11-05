# Qwen Monitor Dashboard

Ein schlankes, responsives Dashboard für den Monitor eines lokalen **Strata**-Servers (Qwen-Modell auf Apple Silicon), das von Handy oder Laptop über Tailscale erreichbar ist — inklusive Live-Temperaturen und Leistung des Mac Studio via [macmon](https://github.com/vladkens/macmon).

## Warum?

Der Strata-Monitor ist nur auf der Server-Seite schön lesbar, und die API sendet keine CORS-Headers — eine direkte HTML-Seite auf dem Handy kann die Daten nicht direkt fetchen. Dieses Projekt stellt einen kleinen Proxy (nur Python-stdlib, keine Dependencies) daneben, der die Dashboard-HTML servt und die Daten endpunkte weiterreicht. Zusätzlich liefert Strata auf Apple Silicon keine GPU-/CPU-Temperaturen (psutil braucht root `powermetrics`) — die kommen von `macmon serve`.

## Architektur

```
Handy/Laptop-Browser
      │ http://<host>:8765
monitor.py  ──► GET /health, /metrics  → Strata (Strata-Server, z.B. :8080)
      │       GET /temps              → macmon serve (:9090/json)
```

- `monitor.py` — Server + CORS-Proxy (stdlib, Port 8765)
- `dashboard.html` — Single-File-Dashboard, Polling alle 1–10 s
- Anzeigen: Live tok/s, Decode-/Prefill-Ø, GPU-Auslastung, VRAM, RAM, Cache-Hit, Draft-Akzeptanz, letzte Anfragen, Die/GPU-Temperatur, SOC-/System-Leistung, Lüfter

## Voraussetzungen

- Python 3 (nur stdlib)
- Strata-Server mit `/health` und `/metrics`
- Für Temperaturen: `macmon` auf dem Mac Studio:
  ```bash
  brew install macmon        # tap: steipete/tap
  sudo macmon serve --install --sudo
  ```

## Start

```bash
python3 monitor.py
# Browser: http://localhost:8765
```

Konfiguration über Umgebungsvariablen:

| Variable     | Default                        |
|--------------|--------------------------------|
| `STRATA_URL` | `http://100.xx.yy.zz:8080`   |
| `MACMON_URL` | `http://100.xx.yy.zz:9090/json` |
| `PORT`       | `8765`                         |

Die IPs sind Tailscale-Adressen — einfach an die eigene Umgebung anpassen.

## Betrieb auf TrueNAS Scale (immer erreichbar)

Der Proxy kann dauerhaft auf der NAS laufen, damit das Dashboard auch lebt, wenn der Laptop schläft.

**Variante A — Custom App per Bind-Mount (kein Build nötig):**
1. Code auf ein Dataset kopieren, z. B. `/mnt/apps/qwen-monitor`
2. Apps → Discover Apps → **Custom App**:
   - Image: `python`, Tag: `3.12-alpine`
   - Container entrypoint arguments: `["monitor.py"]`
   - Path: Host `/mnt/apps/qwen-monitor` → Container `/app`
   - Port: `8765`
   - Environment: `STRATA_URL`, `MACMON_URL` (LAN-IPs des Mac Studio, falls beide im gleichen Netz)

**Variante B — eigenes Image bauen:**
```bash
docker build -t qwen-monitor .
```
dann in der Custom App `qwen-monitor:latest` als Image angeben.

Handy im WLAN öffnet dann `http://<truenas-lan-ip>:8765`. Wenn Strata/macmon nur über Tailscale erreichbar sind, installiere den offiziellen Tailscale-App auf TrueNAS — dann sieht die NAS das Mac Studio unter dessen 100.x-Adresse.

## macmon JSON-Felder (Referenz)

`temp.cpu_temp_avg`, `temp.gpu_temp_avg`, `cpu_power`, `gpu_power`, `all_power`, `sys_power`, `fans[].name/rpm`, `soc.chip_name`, `gpu_active_ratio`

## Lizenz

MIT
