#!/usr/bin/env python3
"""Веб-дашборд квоты Z.AI Coding Plan для главной страницы llmproxy.

Читает Z.AI API-ключ из config/config.yml Moon Bridge (proxy.anthropic.api_key)
и рендерит HTML-версию того же отчёта, что печатает `zai-limits` в консоль.
"""

from __future__ import annotations

import datetime as dt
import html
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from zai_limits import (
    PLATFORMS,
    fetch_json,
    fmt_countdown,
    fmt_ts,
    is_peak,
    limit_window_label,
    local_timezone,
)

CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "/config/config.yml"))
PORT = int(os.environ.get("PORT", "8081"))
PLATFORM = os.environ.get("ZAI_PLATFORM", "zai")
CACHE_TTL_SECONDS = 30

_cache_lock = threading.Lock()
_cache: dict = {"expires_at": 0.0, "html": None}


def read_api_key(config_path: Path) -> str:
    """Достаёт proxy.anthropic.api_key из простого config.yml Moon Bridge.

    Формат файла — плоский YAML без списков (см. config.example.yml), поэтому
    достаточно построчного regex-парсинга нужного поля без зависимости от PyYAML.
    """
    text = config_path.read_text()
    match = re.search(r'^\s*api_key:\s*"?([^"\n#]+)"?\s*$', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"proxy.anthropic.api_key не найден в {config_path}")
    return match.group(1).strip()


def render_bar(pct: int) -> str:
    clamped = max(0, min(100, pct))
    return f'<div class="bar"><div class="bar-fill" style="width:{clamped}%"></div></div>'


def render_limit(lim: dict, tz: dt.tzinfo) -> str:
    ltype = lim.get("type", "?")
    pct = int(lim.get("percentage", 0))
    reset_ms = lim.get("nextResetTime")

    if ltype == "TOKENS_LIMIT":
        title = "Модельные токены"
    elif ltype == "TIME_LIMIT":
        title = "MCP-инструменты (web-search / web-reader / zread)"
    else:
        title = ltype

    parts = [f'<section class="limit">', f'<h3>{html.escape(title)}</h3>']
    parts.append(render_bar(pct))
    parts.append(f'<p class="pct">{pct}%</p>')

    extra = []
    if "remaining" in lim and "currentValue" in lim:
        total = lim["remaining"] + lim["currentValue"]
        extra.append(f"{lim['remaining']}/{total}")
    if "usage" in lim:
        extra.append(f"usage={lim['usage']}")
    if extra:
        parts.append(f'<p class="meta">{html.escape(", ".join(extra))}</p>')

    parts.append(f'<p class="meta">окно: {html.escape(limit_window_label(lim))}</p>')

    reset_at = fmt_ts(reset_ms, tz)
    countdown = fmt_countdown(reset_ms)
    if reset_at and countdown:
        parts.append(f'<p class="meta">сброс: {html.escape(reset_at)} ({html.escape(countdown)})</p>')

    details = lim.get("usageDetails") or []
    if details:
        items = "".join(
            f'<li>{html.escape(str(d.get("modelCode", "?")))}: {html.escape(str(d["usage"]))}</li>'
            for d in details if d.get("usage")
        )
        if items:
            parts.append(f'<ul class="details">{items}</ul>')

    parts.append("</section>")
    return "".join(parts)


PAGE_TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Z.AI Coding Plan — квота</title>
<link rel="icon" href="/favicon.ico" type="image/svg+xml">
<meta http-equiv="refresh" content="60">
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 640px; margin: 2rem auto; padding: 0 1rem;
    background: #fff; color: #1a1a1a;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #111; color: #eee; }}
    .limit {{ background: #1c1c1c !important; border-color: #333 !important; }}
    .bar {{ background: #333 !important; }}
  }}
  h1 {{ font-size: 1.4rem; margin-bottom: 0.2rem; }}
  .sub {{ color: #888; margin-top: 0; font-size: 0.9rem; }}
  .peak {{ background: #fff3cd; color: #664d03; padding: 0.6rem 1rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }}
  .limit {{ background: #f7f7f8; border: 1px solid #e5e5e5; border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1rem; }}
  .limit h3 {{ margin: 0 0 0.6rem; font-size: 1rem; }}
  .bar {{ background: #e5e5e5; border-radius: 999px; height: 10px; overflow: hidden; }}
  .bar-fill {{ background: #4f7cff; height: 100%; }}
  .pct {{ font-weight: 600; margin: 0.4rem 0 0.2rem; }}
  .meta {{ color: #666; font-size: 0.85rem; margin: 0.1rem 0; }}
  .details {{ font-size: 0.8rem; color: #777; margin: 0.4rem 0 0; padding-left: 1.2rem; }}
  footer {{ color: #999; font-size: 0.75rem; margin-top: 2rem; }}
  a {{ color: inherit; }}
</style>
</head>
<body>
<h1>Z.AI Coding Plan — квота</h1>
<p class="sub">{platform_name}{tariff}</p>
{peak_banner}
{limits}
<footer>Обновлено: {updated_at} · автообновление раз в минуту · <a href="https://github.com/axisrow/zai-limits">zai-limits</a></footer>
</body>
</html>
"""


def render_page() -> str:
    api_key = read_api_key(CONFIG_PATH)
    endpoints = PLATFORMS[PLATFORM]
    data = fetch_json(endpoints["quota"], api_key)
    tz = local_timezone()

    if data is None:
        payload = {}
    else:
        payload = data.get("data", data) if isinstance(data.get("data", data), dict) else {}

    tariff = ""
    if payload.get("level"):
        tariff = f" · Тариф: {html.escape(payload['level'].upper())}"

    peak_banner = ""
    if is_peak():
        peak_banner = (
            '<div class="peak">⚠ Сейчас пиковое окно Z.AI (14:00-18:00 UTC+8 / '
            '09:00-13:00 МСК) — лимиты жёстче.</div>'
        )

    limits = payload.get("limits") or []
    if not limits:
        limits_html = "<p>Лимиты не вернулись — возможно пустое окно или неверный ключ.</p>"
    else:
        limits_html = "".join(render_limit(lim, tz) for lim in limits)

    return PAGE_TEMPLATE.format(
        platform_name=html.escape(endpoints["name"]),
        tariff=tariff,
        peak_banner=peak_banner,
        limits=limits_html,
        updated_at=dt.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
    )


def render_page_cached() -> str:
    now = time.monotonic()
    with _cache_lock:
        if _cache["html"] is not None and now < _cache["expires_at"]:
            return _cache["html"]
    try:
        page = render_page()
    except Exception as exc:  # noqa: BLE001 — показываем ошибку прямо на странице
        page = (
            "<!doctype html><html><body>"
            f"<h1>Ошибка получения квоты Z.AI</h1><pre>{html.escape(str(exc))}</pre>"
            "</body></html>"
        )
    with _cache_lock:
        _cache["html"] = page
        _cache["expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
    return page


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/favicon.ico":
            # Простая SVG favicon - синий квадрат с MB
            svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect fill="#4f7cff" width="64" height="64"/><text x="32" y="48" font-family="sans-serif" font-size="48" font-weight="bold" fill="white" text-anchor="middle">MB</text></svg>'
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(svg)))
            self.end_headers()
            self.wfile.write(svg)
            return

        if self.path not in ("/", "/index.html"):
            self.send_response(404)
            self.end_headers()
            return
        body = render_page_cached().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"zai-dashboard listening on 0.0.0.0:{PORT}, config={CONFIG_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
