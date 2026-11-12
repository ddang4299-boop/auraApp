"""Đăng nhập Google bằng OAuth 2.0 cho ứng dụng cài đặt.

Luồng (chuẩn RFC 8252 cho app native): mở trình duyệt hệ thống tới trang
đăng nhập của nhà cung cấp → người dùng đồng ý → nhà cung cấp chuyển hướng về
http://127.0.0.1:<cổng>/ nơi app đang lắng nghe → app đổi `code` lấy token
(PKCE) → gọi API lấy tên, email, ảnh đại diện.

Cấu hình trong file `.env` ở thư mục gốc (xem `.env.example`):
    GOOGLE_CLIENT_ID=...            # loại "Desktop app" trong Google Cloud Console
    GOOGLE_CLIENT_SECRET=...
    OAUTH_REDIRECT_PORT=8765        # cổng loopback nhận kết quả đăng nhập (tuỳ chọn)
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx

ROOT = Path(__file__).resolve().parent.parent
LOGIN_TIMEOUT = 180       # giây chờ người dùng đăng nhập trên trình duyệt


def _load_env() -> None:
    """Đọc file .env đơn giản (KEY=VALUE) vào biến môi trường nếu chưa có."""
    for path in (ROOT / ".env", Path.cwd() / ".env"):
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


_load_env()


@dataclass
class Profile:
    name: str = ""
    email: str = ""
    phone: str = ""
    avatar_url: str = ""
    provider: str = ""            # google | guest
    provider_id: str = ""
    birth_year: str = ""
    bio: str = ""
    linked: dict[str, str] = field(default_factory=dict)   # provider -> email/tên tài khoản liên kết

    @property
    def initials(self) -> str:
        parts = [w for w in self.name.split() if w]
        if not parts:
            return "A"
        return (parts[-1][0] if len(parts) == 1 else parts[0][0] + parts[-1][0]).upper()

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "Profile":
        p = cls()
        for k, v in (d or {}).items():
            if hasattr(p, k):
                setattr(p, k, v)
        return p


class AuthError(Exception):
    pass


class NotConfigured(AuthError):
    pass


@dataclass
class _ProviderSpec:
    name: str
    label: str
    auth_url: str
    token_url: str
    scope: str
    id_env: str
    secret_env: str
    use_pkce: bool


PROVIDERS = {
    "google": _ProviderSpec(
        "google", "Google", "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token", "openid email profile",
        "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", True),
}


def is_configured(provider: str) -> bool:
    spec = PROVIDERS[provider]
    return bool(os.environ.get(spec.id_env)) and bool(os.environ.get(spec.secret_env))


def _redirect_uri(provider: str, port: int) -> str:
    # Google (loại "Desktop app") chấp nhận mọi cổng loopback 127.0.0.1
    return f"http://127.0.0.1:{port}/"


_DONE_HTML = """<!doctype html><html lang="vi"><meta charset="utf-8">
<title>AURA</title><body style="font-family:system-ui;background:#F6F2E8;color:#2F2A26;
display:grid;place-items:center;height:100vh;margin:0"><div style="text-align:center">
<h1 style="font-family:Georgia,serif;color:#772F3D;letter-spacing:.05em">AURA</h1>
<p>{msg}</p><p style="color:#796E64">Bạn có thể đóng cửa sổ này và quay lại ứng dụng.</p>
</div></body></html>"""


async def _wait_for_code(port: int, state: str) -> str:
    """Mở máy chủ loopback, chờ trình duyệt chuyển hướng về kèm ?code=."""
    loop = asyncio.get_running_loop()
    result: asyncio.Future[str] = loop.create_future()

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            line = (await reader.readline()).decode("latin-1")
            while (await reader.readline()) not in (b"\r\n", b"\n", b""):
                pass
            target = line.split(" ")[1] if " " in line else "/"
            q = {k: v[-1] for k, v in parse_qs(urlsplit(target).query).items()}
            ok = "code" in q and q.get("state") == state
            msg = "Đăng nhập thành công." if ok else "Đăng nhập chưa hoàn tất."
            body = _DONE_HTML.format(msg=msg).encode("utf-8")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
                         + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
                         + body)
            await writer.drain()
            if not result.done():
                if ok:
                    result.set_result(q["code"])
                elif "error" in q:
                    result.set_exception(AuthError(q.get("error_description") or q["error"]))
        finally:
            writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", port)
    try:
        return await asyncio.wait_for(result, LOGIN_TIMEOUT)
    except asyncio.TimeoutError as e:
        raise AuthError("Hết thời gian chờ đăng nhập.") from e
    finally:
        server.close()


async def sign_in(provider: str, open_url) -> Profile:
    """Chạy toàn bộ luồng OAuth và trả về hồ sơ người dùng.

    `open_url(url)` là coroutine mở trình duyệt (vd. page.launch_url).
    """
    spec = PROVIDERS[provider]
    client_id = os.environ.get(spec.id_env, "")
    secret = os.environ.get(spec.secret_env, "")
    if not client_id or not secret:
        raise NotConfigured(f"Chưa cấu hình {spec.id_env} / {spec.secret_env} trong file .env")
    port = int(os.environ.get("OAUTH_REDIRECT_PORT", "8765"))
    redirect = _redirect_uri(provider, port)
    state = secrets.token_urlsafe(16)
    params = {"client_id": client_id, "redirect_uri": redirect, "response_type": "code",
              "scope": spec.scope, "state": state}
    verifier = ""
    if spec.use_pkce:
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")
        params |= {"code_challenge": challenge.decode(), "code_challenge_method": "S256",
                   "prompt": "select_account"}
    waiter = asyncio.create_task(_wait_for_code(port, state))
    await asyncio.sleep(0.05)
    await open_url(f"{spec.auth_url}?{urlencode(params)}")
    code = await waiter

    data = {"client_id": client_id, "client_secret": secret, "code": code,
            "redirect_uri": redirect}
    if spec.use_pkce:
        data |= {"grant_type": "authorization_code", "code_verifier": verifier}
    async with httpx.AsyncClient(timeout=20) as http:
        tok = (await http.post(spec.token_url, data=data)).json()
        if "access_token" not in tok:
            raise AuthError(tok.get("error_description") or "Không lấy được token Google.")
        u = (await http.get("https://openidconnect.googleapis.com/v1/userinfo",
                            headers={"Authorization": f"Bearer {tok['access_token']}"})).json()
        return Profile(name=u.get("name", ""), email=u.get("email", ""),
                       avatar_url=u.get("picture", ""), provider="google",
                       provider_id=str(u.get("sub", "")),
                       linked={"google": u.get("email", "")})
