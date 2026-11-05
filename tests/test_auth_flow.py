"""Kiểm thử luồng OAuth Google (không cần mạng): trình duyệt & server Google được giả lập."""
import asyncio, os, sys
from urllib.parse import urlsplit, parse_qs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.update(GOOGLE_CLIENT_ID="test-id", GOOGLE_CLIENT_SECRET="test-secret", OAUTH_REDIRECT_PORT="8799")
import httpx
from aura import auth

async def main():
    real_client = httpx.AsyncClient

    def google(req: httpx.Request):
        if "token" in str(req.url):
            body = req.content.decode()
            assert "code=abc123" in body and "code_verifier=" in body, body
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(200, json={"sub": "42", "name": "Nguyễn Văn An",
                                         "email": "an@example.com", "picture": "https://x/y.jpg"})

    async def fake_browser(url):
        q = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
        print("auth host:", urlsplit(url).netloc, "| PKCE:", q.get("code_challenge_method"),
              "| redirect:", q["redirect_uri"], flush=True)
        async def hit():
            await asyncio.sleep(0.2)
            async with real_client() as c:      # trình duyệt gọi về loopback thật
                r = await c.get(q["redirect_uri"] + f"?code=abc123&state={q['state']}")
                print("callback page:", r.status_code, "ok" if "thành công" in r.text else "FAIL", flush=True)
        asyncio.get_running_loop().create_task(hit())

    auth.httpx.AsyncClient = lambda **kw: real_client(transport=httpx.MockTransport(google), **kw)
    p = await asyncio.wait_for(auth.sign_in("google", fake_browser), 20)
    print("profile:", p.name, "|", p.email, "|", p.initials, "|", p.linked, flush=True)
    assert p.email == "an@example.com" and p.initials == "NA"
    print("PASS")

asyncio.run(main())
