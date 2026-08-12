"""Small authenticated web product for memory controls and crisis actions."""

from __future__ import annotations

import argparse
import html
import os
import sqlite3
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from .auth import AuthService, AuthSession
from .config import load_dotenv
from .crisis_resources import get_crisis_resource_card, render_crisis_card_html
from .privacy import MemoryScope
from .secure_store import EncryptedMemoryStore, load_master_key


STYLE = """
body{font:16px system-ui;max-width:860px;margin:40px auto;padding:0 20px;color:#18302b}
nav{display:flex;gap:16px}.panel,.crisis-card{padding:20px;border:1px solid #bdd4cc;border-radius:14px;margin:20px 0}
input,select,button{font:inherit;padding:9px;margin:4px}button,.crisis-action{background:#176b5b;color:white;border:0;border-radius:8px;text-decoration:none;display:inline-block;padding:10px 14px}
.danger{background:#a32727}.muted{color:#58706a}.crisis-actions{display:flex;gap:10px;flex-wrap:wrap}
"""


class PsychoWebApp:
    def __init__(self, auth: AuthService, memory: EncryptedMemoryStore) -> None:
        self.auth, self.memory = auth, memory

    def __call__(self, environ: dict, start_response):
        method, path = environ.get("REQUEST_METHOD", "GET"), environ.get("PATH_INFO", "/")
        headers = [("Content-Type", "text/html; charset=utf-8"),
                   ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
                   ("Referrer-Policy", "no-referrer"),
                   ("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")]
        if path == "/health":
            return self._respond(start_response, "200 OK", headers, "ok", content_type="text/plain")
        if path == "/login":
            if method == "POST":
                form = self._form(environ)
                try:
                    session = self.auth.login(form.get("user_id", ""), form.get("password", ""),
                                              client_id=environ.get("REMOTE_ADDR", "local"))
                except PermissionError:
                    return self._page(start_response, "401 Unauthorized", headers, "登录失败", self._login("用户名或密码不正确。"))
                headers.append(("Set-Cookie", f"session={session.token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600"))
                headers.append(("Location", "/"))
                return self._respond(start_response, "303 See Other", headers, "")
            return self._page(start_response, "200 OK", headers, "登录", self._login())
        session = self._session(environ)
        if not session:
            headers.append(("Location", "/login"))
            return self._respond(start_response, "303 See Other", headers, "")
        if method == "POST":
            form = self._form(environ)
            try:
                self.auth.require_csrf(session, form.get("csrf", ""))
            except PermissionError:
                return self._page(start_response, "403 Forbidden", headers, "请求被拒绝", "CSRF 校验失败。")
            if path == "/memory/consent":
                scopes = {MemoryScope(item) for item in form.get("scopes", "").split(",") if item}
                self.memory.grant_consent(session.user_id, scopes, policy_version="2026-08-12")
            elif path == "/memory/add":
                self.memory.remember(session.user_id, MemoryScope(form["scope"]), form["value"])
            elif path == "/memory/delete":
                self.memory.delete_item(session.user_id, form.get("item_id", ""))
            elif path == "/memory/delete-all":
                self.memory.delete_all(session.user_id)
            elif path == "/logout":
                self.auth.logout(session.token)
                headers.extend([("Set-Cookie", "session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"), ("Location", "/login")])
                return self._respond(start_response, "303 See Other", headers, "")
            headers.append(("Location", "/memory"))
            return self._respond(start_response, "303 See Other", headers, "")
        if path == "/crisis":
            query = parse_qs(environ.get("QUERY_STRING", ""))
            locale = query.get("locale", ["zh-CN"])[0]
            body = render_crisis_card_html(get_crisis_resource_card(locale))
            return self._page(start_response, "200 OK", headers, "危机支持", body, session)
        if path == "/memory/export":
            return self._respond(start_response, "200 OK", headers,
                                 self.memory.export(session.user_id), content_type="application/json; charset=utf-8")
        if path == "/memory":
            return self._page(start_response, "200 OK", headers, "记忆与同意", self._memory(session), session)
        body = """<section class=panel><h2>这是 AI 心理支持工具</h2><p>它不是心理医生，也不提供诊断。你可以随时查看、导出或删除长期记忆。</p><p><a href='/memory'>管理记忆</a> · <a href='/crisis?locale=zh-CN'>打开本地化危机支持</a></p></section>"""
        return self._page(start_response, "200 OK", headers, "Psycho Agent", body, session)

    def _session(self, environ: dict) -> AuthSession | None:
        cookie = SimpleCookie(environ.get("HTTP_COOKIE", ""))
        token = cookie.get("session")
        if not token:
            return None
        try:
            return self.auth.authenticate(token.value)
        except PermissionError:
            return None

    @staticmethod
    def _form(environ: dict) -> dict[str, str]:
        try:
            length = min(int(environ.get("CONTENT_LENGTH") or 0), 32_768)
        except ValueError:
            length = 0
        values = parse_qs(environ["wsgi.input"].read(length).decode("utf-8"), keep_blank_values=True)
        return {key: items[-1] for key, items in values.items()}

    def _memory(self, session: AuthSession) -> str:
        items = "".join(
            f"<li><b>{html.escape(item['scope'])}</b>: {html.escape(item['value'])} "
            f"<form method=post action='/memory/delete' style='display:inline'><input type=hidden name=csrf value='{session.csrf_token}'><input type=hidden name=item_id value='{item['item_id']}'><button class=danger>删除</button></form></li>"
            for item in self.memory.view(session.user_id)
        ) or "<li class=muted>暂无已保存记忆</li>"
        scopes = ",".join(scope.value for scope in MemoryScope)
        return f"""<section class=panel><h2>明确同意</h2><p>此演示一次启用四类最小化记忆；撤销/逐范围控制可由存储 API 执行。</p><form method=post action='/memory/consent'><input type=hidden name=csrf value='{session.csrf_token}'><input type=hidden name=scopes value='{scopes}'><button>同意保存</button></form></section><section class=panel><h2>添加记忆</h2><form method=post action='/memory/add'><input type=hidden name=csrf value='{session.csrf_token}'><select name=scope>{''.join(f'<option>{s.value}</option>' for s in MemoryScope)}</select><input required name=value maxlength=500><button>保存</button></form><h3>已保存</h3><ul>{items}</ul><p><a href='/memory/export'>导出 JSON</a></p><form method=post action='/memory/delete-all'><input type=hidden name=csrf value='{session.csrf_token}'><button class=danger>撤销同意并全部删除</button></form></section>"""

    @staticmethod
    def _login(error: str = "") -> str:
        return f"<section class=panel><p class=danger>{html.escape(error)}</p><form method=post><label>用户 <input name=user_id required></label><label>密码 <input type=password name=password required></label><button>登录</button></form></section>"

    def _page(self, start_response, status: str, headers: list, title: str, body: str,
              session: AuthSession | None = None):
        nav = ""
        if session:
            nav = f"<nav><a href='/'>首页</a><a href='/memory'>记忆</a><a href='/crisis?locale=zh-CN'>危机支持</a><form method=post action='/logout'><input type=hidden name=csrf value='{session.csrf_token}'><button>退出</button></form></nav>"
        document = f"<!doctype html><html lang=zh-CN><meta charset=utf-8><meta name=viewport content='width=device-width'><title>{html.escape(title)}</title><style>{STYLE}</style><body>{nav}<h1>{html.escape(title)}</h1>{body}</body></html>"
        return self._respond(start_response, status, headers, document)

    @staticmethod
    def _respond(start_response, status: str, headers: list, body: str,
                 content_type: str | None = None):
        if content_type:
            headers = [(k, v) for k, v in headers if k.lower() != "content-type"] + [("Content-Type", content_type)]
        payload = body.encode("utf-8")
        start_response(status, headers + [("Content-Length", str(len(payload)))])
        return [payload]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Psycho Agent web prototype")
    parser.add_argument("--database", default="data/psycho_agent.sqlite3")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    load_dotenv()
    password = os.environ.get("PSYCHO_AGENT_ADMIN_PASSWORD", "")
    if len(password) < 12:
        raise SystemExit("Set PSYCHO_AGENT_ADMIN_PASSWORD to at least 12 characters.")
    auth = AuthService(args.database)
    try:
        auth.create_user("local-admin", password, role="admin")
    except sqlite3.IntegrityError:
        pass
    app = PsychoWebApp(auth, EncryptedMemoryStore(args.database, load_master_key()))
    print(f"Local prototype: http://{args.host}:{args.port} (user: local-admin)")
    make_server(args.host, args.port, app).serve_forever()


if __name__ == "__main__":
    main()
