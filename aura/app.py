"""Điều hướng, trạng thái và vòng đời ứng dụng AURA."""
from __future__ import annotations

import asyncio
import importlib
import json
import os
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit

import flet as ft

from . import auth
from .auth import Profile
from .data import DEFAULT_ID, PAINTINGS
from .socratic import (Message, ScriptedSocraticEngine, SocraticEngine, message_from_dict,
                       message_to_dict)
from .theme import BG, FONTS, GUTTER, INK, MAX_W, MUTED, PRIMARY
from .ui import FRAME_W, T, snack

PREFS_KEY = "aura.profile"
# Cuộc trò chuyện được cất trong bộ nhớ của trình duyệt (localStorage, qua SharedPreferences):
# lỡ tải lại trang (F5), máy chủ khởi động lại hay mở lại app thì vẫn nói tiếp được đúng chỗ cũ.
CHATS_KEY = "aura.chats"
CHATS_VERSION = 1
APP_VERSION = "1.0.0"

ROOT_ROUTES = {"/", "/home", "/gallery", "/saved"}


@dataclass
class QuizState:
    answers: dict[int, int] = field(default_factory=dict)   # câu -> đáp án đã chọn
    current: int = 0
    phase: str = "answering"           # answering | retry | graded
    feeling: int | None = None
    note: str = ""


@dataclass
class ChatState:
    messages: list[Message] = field(default_factory=list)
    stage: int = 0
    thinking: bool = False
    starting: bool = False             # đang lấy lời chào đầu (tránh lấy 2 lần khi màn được dựng lại)
    picked: dict[int, int] = field(default_factory=dict)     # index tin nhắn -> gợi ý đã chọn
    asked: list[str] = field(default_factory=list)           # câu hỏi nhanh (quick prompt) đã bấm


@dataclass
class AppState:
    profile: Profile | None = None
    saved: set[str] = field(default_factory=set)
    quizzes: dict[str, QuizState] = field(default_factory=dict)
    chats: dict[str, ChatState] = field(default_factory=dict)

    def quiz(self, pid: str) -> QuizState:
        return self.quizzes.setdefault(pid, QuizState())

    def chat(self, pid: str) -> ChatState:
        return self.chats.setdefault(pid, ChatState())


# (tiền tố đường dẫn, module, hàm)
ROUTES = [
    ("/home", "home", "build"),
    ("/gallery", "gallery", "build"),
    ("/saved", "gallery", "saved"),
    ("/painting/", "painting", "build"),
    ("/chat/", "chat", "build"),
    ("/detail/", "detail", "build"),
    ("/quiz/", "quiz", "build"),
    ("/result/", "result", "build"),
    ("/profile", "profile", "build"),
    ("/timeline", "topics", "timeline"),
    ("/concepts", "topics", "concepts"),
    ("/topic/", "topics", "build"),
    ("/sources/", "sources", "build"),
    ("/", "auth", "welcome"),
]


class AuraApp:
    def __init__(self, page: ft.Page, engine: SocraticEngine | None = None):
        self.page = page
        self.engine: SocraticEngine = engine or ScriptedSocraticEngine()
        self.state = AppState()
        self.signed_in = False

        page.title = "AURA"
        page.fonts = FONTS
        page.bgcolor = BG
        page.padding = 0
        page.spacing = 0
        page.theme_mode = ft.ThemeMode.LIGHT
        # Chuyển màn: iPhone/Mac trượt ngang kiểu iOS (vuốt mép trái để quay lại);
        # Android/máy tính: mờ dần vào kiểu phòng trưng bày (Flutter tự chạy hiệu ứng, không tốn máy chủ).
        slide = ft.PageTransitionTheme.CUPERTINO
        fade = ft.PageTransitionTheme.FADE_FORWARDS
        page.theme = ft.Theme(font_family="Inter", color_scheme_seed=PRIMARY,
                              scaffold_bgcolor=BG,
                              page_transitions=ft.PageTransitionsTheme(
                                  android=fade, ios=slide, macos=slide, windows=fade,
                                  linux=fade))
        page.on_route_change = self._on_route_change
        page.on_view_pop = self._on_view_pop
        # Bản web: người dùng bấm F5 thì Flet nối lại ĐÚNG phiên đang chạy trên máy chủ (dữ liệu còn nguyên)
        # nhưng trình duyệt vẽ lại từ đầu, vị trí cuộn về 0. Màn đang mở (vd chat) gắn hàm vào on_reconnect
        # để xử lý lúc đó (chat: cuộn về tin nhắn cuối).
        self.on_reconnect = None
        page.on_connect = self._on_connect
        # Lúc mới mở, trình duyệt/điện thoại có thể báo bề rộng tạm (vd 164px) rồi mới báo bề rộng
        # thật: khi bề rộng đổi thì dựng lại các màn để ảnh/lưới tính theo đúng khổ màn hình.
        self._laid_out_width = self.page_width
        page.on_resize = self._on_resize
        # Dịch vụ của Flet: lưu trữ cục bộ và mở trình duyệt/URL.
        self.prefs = ft.SharedPreferences()
        self.launcher = ft.UrlLauncher()
        # Điều hướng nhanh (xem go / _on_route_change):
        #   _epoch  tăng khi dữ liệu dùng chung đổi (hồ sơ, tranh đã lưu) -> màn cũ trong stack dựng lại
        #   _url    đường dẫn trình duyệt đang hiện (mình đã đẩy hoặc trình duyệt báo về)
        #   _echo   đường dẫn mình vừa đẩy, chờ trình duyệt báo lại -> bỏ qua vì màn đã dựng sẵn
        self._epoch = 0
        self._url = page.route or "/"
        self._echo: list[str] = []
        # Bức tranh đang xem: các nút "Tác phẩm", "Hỏi Aura", "Tư liệu" trên thanh điều hướng mở tranh này.
        self.current_pid = DEFAULT_ID
        # Báo cho màn chat biết đã đọc xong cuộc trò chuyện cất từ lần trước (xem _restore_chats).
        self._chats_ready = asyncio.Event()
        page.views.clear()
        self._on_route_change(None)
        page.run_task(self._restore_session)

    # ---- kích thước -----------------------------------------------------------
    @property
    def page_width(self) -> float:
        """Bề rộng thật của cửa sổ / màn hình."""
        w = self.page.width
        return float(w) if w else 402.0

    @property
    def width(self) -> float:
        """Bề rộng cột nội dung: cả màn hình trên điện thoại, tối đa MAX_W trên máy tính."""
        return min(self.page_width, MAX_W)

    @property
    def content_width(self) -> float:
        return self.width - 2 * GUTTER

    # ---- điều hướng -------------------------------------------------------------
    def go(self, route: str) -> None:
        """Chuyển màn. Dựng màn mới NGAY rồi mới báo trình duyệt đổi địa chỉ.

        Trước đây chỉ đẩy địa chỉ (push_route) rồi chờ trình duyệt báo lại mới dựng màn: mỗi lần
        bấm mất hai lượt đi-về máy chủ. Giờ chỉ còn một lượt."""
        self._show(route)
        self._sync_url(route)

    def _sync_url(self, route: str) -> None:
        if route != self._url:
            self._url = route
            self._echo.append(route)
            self.page.run_task(self.page.push_route, route)

    def touch(self) -> None:
        """Đánh dấu dữ liệu dùng chung vừa đổi: các màn cũ trong stack sẽ dựng lại khi quay về."""
        self._epoch += 1

    def back(self) -> None:
        views = self.page.views
        if len(views) > 1:
            views.pop()
            self.go(views[-1].route)
        else:
            self.go(self._parent(views[-1].route if views else "/"))

    def back_handler(self, e=None) -> None:
        self.back()

    @staticmethod
    def _parent(route: str) -> str:
        path = urlsplit(route).path
        if path.startswith(("/chat/", "/detail/", "/quiz/", "/result/", "/sources/")):
            return "/painting/" + path.split("/")[2]
        if path.startswith("/painting/"):
            return "/gallery"
        return "/home"

    def _build(self, route: str) -> ft.View:
        parts = urlsplit(route)
        path = parts.path or "/"
        query = {k: v[-1] for k, v in parse_qs(parts.query).items()}
        for prefix, module, fn in ROUTES:
            if path == prefix or (prefix.endswith("/") and prefix != "/" and path.startswith(prefix)):
                args = [a for a in path[len(prefix):].split("/") if a] if prefix.endswith("/") else []
                if args and args[0] in PAINTINGS:     # màn của một bức tranh: nhớ tranh đang xem
                    self.current_pid = args[0]
                mod = importlib.import_module(f".screens.{module}", __package__)
                view = self._framed(getattr(mod, fn), query, *args)
                view.route = route
                view.data = self._epoch
                return view
        mod = importlib.import_module(".screens.auth", __package__)
        view = self._framed(mod.welcome, {})
        view.data = self._epoch
        return view

    def _framed(self, builder, query, *args) -> ft.View:
        """Dựng màn với bề rộng cột đúng khổ màn hình (ui.screen đọc FRAME_W)."""
        token = FRAME_W.set(self.width if self.page_width > MAX_W else None)
        try:
            return builder(self, query, *args)
        finally:
            FRAME_W.reset(token)

    def rebuild(self) -> None:
        """Dựng lại màn hình hiện tại (sau khi đổi trạng thái lớn)."""
        views = self.page.views
        if views:
            views[-1] = self._build(views[-1].route)
            self.page.update()

    def _on_resize(self, e) -> None:
        if abs(self.page_width - self._laid_out_width) < 1:     # chỉ đổi chiều cao (vd bật bàn phím)
            return
        self._laid_out_width = self.page_width
        views = self.page.views
        for i, v in enumerate(list(views)):
            views[i] = self._build(v.route)
        self.page.update()

    def _on_route_change(self, e) -> None:
        route = self.page.route or "/"
        if route in self._echo:        # trình duyệt báo lại địa chỉ do go() đẩy: màn đã dựng sẵn
            del self._echo[:self._echo.index(route) + 1]
            return
        self._url = route              # người dùng bấm Back/Forward của trình duyệt, mở link...
        self._show(route)

    def _show(self, route: str) -> None:
        views = self.page.views
        for i in range(len(views) - 1, -1, -1):          # quay lại màn đã có trong stack: chỉ gỡ
            if views[i].route == route:                  # các màn phía trên, không gửi lại cả màn
                del views[i + 1:]
                if views[i].data != self._epoch:         # dữ liệu đã đổi từ lúc dựng: dựng lại
                    views[i] = self._build(route)
                self.page.update()
                return
        path = urlsplit(route).path
        if path in ROOT_ROUTES:
            # Tab chính: giữ sẵn Trang chủ ở đáy stack, để bấm "Khám phá" chỉ cần gỡ màn trên
            # (gửi rất ít) thay vì dựng và gửi lại cả trang chủ dài.
            home = views[0] if views and views[0].route == "/home" and path != "/" else None
            views.clear()
            if home is not None:
                views.append(home)
        views.append(self._build(route))
        self.page.update()

    async def _on_connect(self, e) -> None:
        hook = self.on_reconnect
        if hook is not None:
            try:
                await hook()
            except Exception as ex:
                print(f"[app] on_reconnect lỗi: {ex}")

    async def _on_view_pop(self, e) -> None:
        if len(self.page.views) > 1:
            self.page.views.pop()
            self.page.update()
            self._sync_url(self.page.views[-1].route)

    # ---- tiện ích -----------------------------------------------------------------
    def toggle_saved(self, pid: str) -> bool:
        saved = self.state.saved
        if pid in saved:
            saved.remove(pid)
            snack(self.page, "Đã bỏ khỏi mục Đã lưu.")
        else:
            saved.add(pid)
            snack(self.page, "Đã lưu tranh.")
        self.touch()
        return pid in saved

    # ---- tài khoản ----------------------------------------------------------------
    @property
    def profile(self) -> Profile:
        if self.state.profile is None:
            self.state.profile = Profile(name="Khách", provider="guest")
        return self.state.profile

    async def _restore_session(self) -> None:
        """Đọc lại cuộc trò chuyện đang dở, rồi tự đăng nhập lại nếu đã lưu hồ sơ ở lần trước."""
        try:
            await self._restore_chats()
        finally:
            self._chats_ready.set()
        try:
            raw = await self.prefs.get(PREFS_KEY)
        except Exception:
            raw = None
        if not raw:
            return
        try:
            self.state.profile = Profile.from_dict(json.loads(raw))
        except (ValueError, TypeError):
            return
        self.signed_in = True
        self.touch()
        if urlsplit(self.page.route or "/").path == "/":
            self.go("/home")

    # ---- lưu cuộc trò chuyện ------------------------------------------------------
    async def wait_chats(self, timeout: float = 4.0) -> None:
        """Màn chat chờ đọc xong cuộc trò chuyện cũ (tối đa vài giây) rồi mới quyết định chào mới."""
        try:
            await asyncio.wait_for(self._chats_ready.wait(), timeout)
        except asyncio.TimeoutError:
            pass

    def save_chats(self) -> None:
        """Cất các cuộc trò chuyện (gọi sau mỗi lượt). Chỉ cất tranh mà engine xuất được trạng thái,
        để khi đọc lại, lời trên màn hình và chỗ đang đứng trong kịch bản luôn khớp nhau."""
        export = getattr(self.engine, "export_session", None)
        if export is None:
            return
        chats = {}
        for pid, st in self.state.chats.items():
            eng = export(pid) if st.messages else None
            if eng is None:
                continue
            chats[pid] = {"messages": [message_to_dict(m) for m in st.messages], "stage": st.stage,
                          "picked": {str(k): v for k, v in st.picked.items()}, "asked": st.asked,
                          "engine": eng}
        raw = json.dumps({"v": CHATS_VERSION, "chats": chats}, ensure_ascii=False)
        self.page.run_task(self._write_pref, CHATS_KEY, raw)

    async def _write_pref(self, key: str, raw: str) -> None:
        try:
            await self.prefs.set(key, raw)
        except Exception as e:        # trình duyệt chặn bộ nhớ (chế độ ẩn danh...): app vẫn chạy bình thường
            print(f"[app] Không lưu được {key}: {e}")

    async def _restore_chats(self) -> None:
        importer = getattr(self.engine, "import_session", None)
        if importer is None:
            return
        try:
            raw = await self.prefs.get(CHATS_KEY)
            data = json.loads(raw) if raw else None
        except Exception:
            data = None
        if not isinstance(data, dict) or data.get("v") != CHATS_VERSION:
            return
        for pid, c in (data.get("chats") or {}).items():
            st = self.state.chats.get(pid)
            if pid not in PAINTINGS or (st is not None and st.messages):   # đang chat dở trong phiên này
                continue
            try:
                messages = [message_from_dict(m) for m in c["messages"]]
                # kịch bản đã đổi (bản cập nhật mới) thì engine từ chối: bỏ bản cũ, chào lại từ đầu
                if not messages or not importer(PAINTINGS[pid], c.get("engine")):
                    continue
                st = self.state.chat(pid)
                st.messages = messages
                st.stage = int(c.get("stage") or 0)
                st.picked = {int(k): int(v) for k, v in (c.get("picked") or {}).items()}
                st.asked = [str(x) for x in c.get("asked") or []]
            except Exception as e:    # dữ liệu hỏng: bỏ qua, không làm hỏng app
                print(f"[app] Bỏ cuộc trò chuyện đã lưu của {pid}: {e}")

    def reset_chat(self, pid: str) -> None:
        """Bắt đầu lại cuộc trò chuyện của một tranh từ đầu."""
        self.state.chats.pop(pid, None)
        reset = getattr(self.engine, "reset", None)
        if reset is not None:
            reset(pid)
        self.save_chats()

    async def save_profile(self) -> None:
        self.touch()               # tên / ảnh đại diện có thể đã đổi
        try:
            await self.prefs.set(PREFS_KEY, json.dumps(self.profile.to_dict(), ensure_ascii=False))
        except Exception:
            pass

    def complete_sign_in(self, profile: Profile) -> None:
        self.state.profile = profile
        self.signed_in = True
        self.touch()
        self.page.run_task(self.save_profile)
        self.go("/home") 

    def social_login(self, provider: str, *, link: bool = False) -> None:
        """Đăng nhập (hoặc liên kết) tài khoản Google."""
        self.page.run_task(self._social_login, provider, link)

    async def _social_login(self, provider: str, link: bool) -> None:
        label = auth.PROVIDERS[provider].label
        if not auth.is_configured(provider):
            self._not_configured_dialog(provider, link)
            return
        if self.page.web:                 # bản web / máy chủ (Render): chuyển hướng tới trang Google
            await self._web_login(provider, link)
            return
        snack(self.page, f"Đang mở trình duyệt để đăng nhập {label}…")
        try:
            prof = await auth.sign_in(provider, self.launcher.launch_url)
        except auth.AuthError as e:
            snack(self.page, f"Đăng nhập {label} chưa thành công: {e}")
            return
        except Exception as e:      # lỗi mạng...
            snack(self.page, f"Không kết nối được tới {label}: {e}")
            return
        await self._apply_login(provider, prof, link)

    # ---- đăng nhập trên bản web (chạy trên máy chủ) ------------------------------
    def _public_url(self) -> str:
        """Địa chỉ công khai của app. Render tự đặt RENDER_EXTERNAL_URL; nơi khác đặt PUBLIC_URL."""
        url = os.environ.get("PUBLIC_URL") or os.environ.get("RENDER_EXTERNAL_URL") or self.page.url or ""
        return url.rstrip("/")

    async def _web_login(self, provider: str, link: bool) -> None:
        """Cả tab chuyển sang trang đăng nhập Google (không mở popup vì Safari hay chặn).
        Đăng nhập xong Google trả về <địa chỉ app>/oauth_callback, Flet nối lại đúng phiên này
        và gọi _on_web_login. Địa chỉ đó phải được khai trong "Authorized redirect URIs"."""
        from flet.auth.providers import GoogleOAuthProvider
        spec = auth.PROVIDERS[provider]
        oauth = GoogleOAuthProvider(
            client_id=os.environ[spec.id_env], client_secret=os.environ[spec.secret_env],
            redirect_url=f"{self._public_url()}/oauth_callback")
        self._web_login_link = link
        self.page.on_login = self._on_web_login

        async def open_here(url: str) -> None:
            await self.launcher.launch_url(url, web_only_window_name="_self")

        snack(self.page, f"Đang chuyển tới trang đăng nhập {spec.label}…")
        await self.page.login(oauth, redirect_to_page=True, on_open_authorization_url=open_here)

    async def _on_web_login(self, e) -> None:
        if e.error:
            snack(self.page, f"Đăng nhập Google chưa thành công: {e.error_description or e.error}")
            return
        u = dict((self.page.auth.user if self.page.auth else None) or {})
        email = u.get("email", "")
        prof = Profile(name=u.get("name", ""), email=email, avatar_url=u.get("picture", ""),
                       provider="google", provider_id=str(u.get("sub", "")), linked={"google": email})
        await self._apply_login("google", prof, getattr(self, "_web_login_link", False))

    async def _apply_login(self, provider: str, prof: Profile, link: bool) -> None:
        """Đăng nhập xong: tạo phiên mới, hoặc gắn tài khoản vào hồ sơ đang dùng (liên kết)."""
        label = auth.PROVIDERS[provider].label
        if link and self.state.profile is not None:
            cur = self.state.profile
            cur.linked[provider] = prof.linked.get(provider, prof.email)
            cur.email = cur.email or prof.email
            cur.avatar_url = cur.avatar_url or prof.avatar_url
            if cur.name in ("", "Khách", "Bạn"):
                cur.name = prof.name
            await self.save_profile()
            snack(self.page, f"Đã liên kết tài khoản {label}.")
            self.rebuild()
        else:
            self.complete_sign_in(prof)

    def _not_configured_dialog(self, provider: str, link: bool) -> None:
        spec = auth.PROVIDERS[provider]
        dlg = ft.AlertDialog(
            bgcolor=BG,
            title=T(f"Chưa cấu hình đăng nhập {spec.label}", 21, serif=True),
            content=T(f"Để đăng nhập thật, thêm {spec.id_env} và {spec.secret_env} vào file .env "
                      f"(chạy trên máy) hoặc mục Environment trên Render (bản web). Trong lúc chờ, "
                      f"bạn có thể dùng thử bằng hồ sơ mẫu.", 13, 400, MUTED),
            actions=[
                ft.TextButton(content=T("Đóng", 13, 600, MUTED),
                              on_click=lambda e: self.page.pop_dialog()),
                ft.TextButton(content=T("Dùng thử", 13, 600, PRIMARY),
                              on_click=lambda e: self._demo_login(provider, link)),
            ],
        )
        self.page.show_dialog(dlg)

    def _demo_login(self, provider: str, link: bool) -> None:
        self.page.pop_dialog()
        label = auth.PROVIDERS[provider].label
        demo = Profile(name="Người xem AURA", email=f"demo.{provider}@aura.app", provider=provider,
                       linked={provider: f"demo.{provider}@aura.app (thử)"})
        if link and self.state.profile is not None:
            self.state.profile.linked[provider] = demo.linked[provider]
            self.page.run_task(self.save_profile)
            snack(self.page, f"Đã liên kết thử tài khoản {label}.")
            self.rebuild()
        else:
            self.complete_sign_in(demo)

    def sign_out(self) -> None:
        async def _do():
            for key in (PREFS_KEY, CHATS_KEY):     # máy dùng chung: người sau không thấy cuộc trò chuyện cũ
                try:
                    await self.prefs.remove(key)
                except Exception:
                    pass
            for pid in list(self.state.chats):
                reset = getattr(self.engine, "reset", None)
                if reset is not None:
                    reset(pid)
            self.state = AppState()
            self.signed_in = False
            self.touch()
            self.page.views.clear()
            self.go("/")
        self.page.run_task(_do)

    def open_url(self, url: str) -> None:
        if not url.startswith("http"):
            url = "https://" + url
        self.page.run_task(self.launcher.launch_url, url)
