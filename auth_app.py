#!/usr/bin/env python3
"""TSL Rewards — гейт доступа.
Отдаёт статику сайта ТОЛЬКО при валидной сессии. Вход — Telegram Login Widget:
проверяем подпись данных бот-токеном (HMAC-SHA256) + сверяем username с allowlist.
Без внешних зависимостей (только stdlib)."""
import os, time, hmac, hashlib, base64, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from http.cookies import SimpleCookie

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_NAME  = os.environ.get("BOT_NAME", "tsl_skills_bot")
SECRET    = os.environ.get("SESSION_SECRET", "dev-only-secret").encode()
ALLOWED   = {u.strip().lower().lstrip("@") for u in os.environ.get("ALLOWED_USERNAMES", "").split(",") if u.strip()}
SITE      = os.environ.get("SITE_DIR", "/app/site")
TTL       = 7 * 24 * 3600
COOKIE    = "tslr_session"

for ext, t in [(".js", "text/javascript"), (".mjs", "text/javascript"), (".css", "text/css"),
               (".ttf", "font/ttf"), (".woff2", "font/woff2"), (".png", "image/png"),
               (".svg", "image/svg+xml"), (".json", "application/json"), (".ico", "image/x-icon")]:
    mimetypes.add_type(t, ext)


def make_cookie(username):
    exp = str(int(time.time()) + TTL)
    sig = hmac.new(SECRET, f"{username}|{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{username}|{exp}|{sig}".encode()).decode()


def check_cookie(val):
    try:
        username, exp, sig = base64.urlsafe_b64decode(val.encode()).decode().rsplit("|", 2)
        if int(exp) < time.time():
            return None
        good = hmac.new(SECRET, f"{username}|{exp}".encode(), hashlib.sha256).hexdigest()
        return username if hmac.compare_digest(good, sig) else None
    except Exception:
        return None


def verify_telegram(qs):
    data = {k: v[0] for k, v in qs.items()}
    h = data.pop("hash", None)
    if not h or not BOT_TOKEN:
        return None
    dcs = "\n".join(f"{k}={data[k]}" for k in sorted(data))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calc = hmac.new(secret_key, dcs.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, h):
        return None
    if time.time() - int(data.get("auth_date", "0")) > 86400:
        return None
    return (data.get("username") or "").lower()


LOGIN = """<!doctype html><html lang=ru><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>TSL · вход</title>
<style>html,body{margin:0;height:100%}body{background:#091321;color:#aebfd0;
font-family:system-ui,-apple-system,'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center}
.c{text-align:center;max-width:430px;padding:24px}h1{color:#fff;font-size:30px;margin:0 0 14px;letter-spacing:-.02em}
p{color:#8aa0b8;line-height:1.55}.e{color:#f0888a;margin-top:16px;font-size:14px}.w{margin-top:24px}</style></head>
<body><div class=c><h1>TSL · вход для команды</h1>
<p>Лидерборды и каталог скиллов — только для сотрудников TSL. Войди рабочим Telegram.</p>
<div class=w><script async src="https://telegram.org/js/telegram-widget.js?22"
 data-telegram-login="__BOT__" data-size="large" data-userpic="false"
 data-auth-url="/auth/telegram" data-request-access="write"></script></div>
__ERR__</div></body></html>"""


class H(BaseHTTPRequestHandler):
    server_version = "tslr"
    def log_message(self, *a):
        pass

    def _send(self, code, body=b"", ctype="text/html; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _user(self):
        c = SimpleCookie(self.headers.get("Cookie", ""))
        return check_cookie(c[COOKIE].value) if COOKIE in c else None

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        if path == "/healthz":
            return self._send(200, b"ok", "text/plain")
        if path == "/login":
            err = '<p class=e>Этой телеги нет в списке команды — обратись к CEO.</p>' if parse_qs(u.query).get("e") else ""
            return self._send(200, LOGIN.replace("__BOT__", BOT_NAME).replace("__ERR__", err).encode())
        if path == "/auth/telegram":
            username = verify_telegram(parse_qs(u.query))
            if not username or username not in ALLOWED:
                return self._send(302, extra=[("Location", "/login?e=1")])
            ck = f"{COOKIE}={make_cookie(username)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age={TTL}"
            return self._send(302, extra=[("Location", "/"), ("Set-Cookie", ck)])
        if path == "/logout":
            return self._send(302, extra=[("Location", "/login"), ("Set-Cookie", f"{COOKIE}=; Path=/; Max-Age=0")])
        # всё остальное — статика, только для авторизованных
        if not self._user():
            return self._send(302, extra=[("Location", "/login")])
        rel = path.lstrip("/") or "index.html"
        fp = os.path.normpath(os.path.join(SITE, rel))
        if not fp.startswith(SITE + os.sep) and fp != SITE or not os.path.isfile(fp):
            fp = os.path.join(SITE, "index.html")
        try:
            with open(fp, "rb") as f:
                data = f.read()
        except OSError:
            return self._send(404, b"not found", "text/plain")
        ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
        return self._send(200, data, ctype)


if __name__ == "__main__":
    print(f"tslr gate: {len(ALLOWED)} allowed, token={'set' if BOT_TOKEN else 'MISSING'}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
