"""Điều hướng, trạng thái và vòng đời ứng dụng AURA."""
from __future__ import annotations

import asyncio
import importlib
import json
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit

import flet as ft

from . import auth
from .auth import Profile
from .socratic import Message, ScriptedSocraticEngine, SocraticEngine
from .theme import BG, FONTS, GUTTER, INK, MUTED, PRIMARY
from .ui import T, snack

PREFS_KEY = "aura.profile"
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
    picked: dict[int, int] = field(default_factory=dict)     # index tin nhắn -> gợi ý đã chọn


@dataclass
class AppState:
    phone: str = ""
    profile: Profile | None = None
    saved: set[str] = field(default_factory=lambda: {"arnolfini"})
    quizzes: dict[str, QuizState] = field(default_factory=dict)
    chats: dict[str, ChatState] = field(default_factory=dict)

    def quiz(self, pid: str) -> QuizState:
        return self.quizzes.setdefault(pid, QuizState())

    def chat(self, pid: str) -> ChatState:
        return self.chats.setdefault(pid, ChatState())


# (tiền tố đường dẫn, module, hàm)
ROUTES = [
    ("/login/phone", "auth", "phone"),
    ("/login/otp", "auth", "otp"),
    ("/home", "home", "build"),
    ("/gallery", "gallery", "build"),
    ("/saved", "gallery", "saved"),
    ("/painting/", "painting", "build"),
    ("/chat/", "chat", "build"),
    ("/detail/", "detail", "build"),
    ("/quiz/", "quiz", "build"),
    ("/result/", "result", "build"),
    ("/profile", "profile", "build"),
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
        page.theme = ft.Theme(font_family="Inter", color_scheme_seed=PRIMARY,
                              scaffold_bgcolor=BG)
        page.on_route_change = self._on_route_change
        page.on_view_pop = self._on_view_pop
        # Dịch vụ của Flet: lưu trữ cục bộ và mở trình duyệt/URL.
        self.prefs = ft.SharedPreferences()
        self.launcher = ft.UrlLauncher()
        page.views.clear()
        self._on_route_change(None)
        page.run_task(self._restore_session)

    # ---- kích thước -----------------------------------------------------------
    @property
    def width(self) -> float:
        w = self.page.width
        return float(w) if w else 402.0

    @property
    def content_width(self) -> float:
        return self.width - 2 * GUTTER

    # ---- điều hướng -------------------------------------------------------------
    def go(self, route: str) -> None:
        self.page.run_task(self.page.push_route, route)

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
        if path.startswith("/login/otp"):
            return "/login/phone"
        if path.startswith("/login"):
            return "/"
        if path.startswith(("/chat/", "/detail/", "/quiz/", "/result/")):
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
                mod = importlib.import_module(f".screens.{module}", __package__)
                view = getattr(mod, fn)(self, query, *args)
                view.route = route
                return view
        mod = importlib.import_module(".screens.auth", __package__)
        return mod.welcome(self, {})

    def rebuild(self) -> None:
        """Dựng lại màn hình hiện tại (sau khi đổi trạng thái lớn)."""
        views = self.page.views
        if views:
            views[-1] = self._build(views[-1].route)
            self.page.update()

    def _on_route_change(self, e) -> None:
        route = self.page.route or "/"
        views = self.page.views
        for i in range(len(views) - 1, -1, -1):          # quay lại màn đã có trong stack
            if views[i].route == route:
                del views[i + 1:]
                self.page.update()
                return
        if urlsplit(route).path in ROOT_ROUTES:
            views.clear()
        views.append(self._build(route))
        self.page.update()

    async def _on_view_pop(self, e) -> None:
        if len(self.page.views) > 1:
            self.page.views.pop()
            await self.page.push_route(self.page.views[-1].route)

    # ---- tiện ích -----------------------------------------------------------------
    def toggle_saved(self, pid: str) -> bool:
        saved = self.state.saved
        if pid in saved:
            saved.remove(pid)
            snack(self.page, "Đã bỏ khỏi mục Đã lưu.")
        else:
            saved.add(pid)
            snack(self.page, "Đã lưu tranh.")
        return pid in saved

    # ---- tài khoản ----------------------------------------------------------------
    @property
    def profile(self) -> Profile:
        if self.state.profile is None:
            self.state.profile = Profile(name="Khách", provider="guest")
        return self.state.profile

    async def _restore_session(self) -> None:
        """Tự đăng nhập lại nếu đã lưu hồ sơ ở lần trước."""
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
        if urlsplit(self.page.route or "/").path == "/":
            await self.page.push_route("/home")

    async def save_profile(self) -> None:
        try:
            await self.prefs.set(PREFS_KEY, json.dumps(self.profile.to_dict(), ensure_ascii=False))
        except Exception:
            pass

    def complete_sign_in(self, profile: Profile) -> None:
        self.state.profile = profile
        self.signed_in = True
        self.page.run_task(self.save_profile)
        self.go("/home") 

    def social_login(self, provider: str, *, link: bool = False) -> None:
        """Đăng nhập (hoặc liên kết thêm) tài khoản Google/Facebook."""
        self.page.run_task(self._social_login, provider, link)

    async def _social_login(self, provider: str, link: bool) -> None:
        label = auth.PROVIDERS[provider].label
        if not auth.is_configured(provider):
            self._not_configured_dialog(provider, link)
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
                      f"ở thư mục dự án (xem README, mục Đăng nhập). Trong lúc chờ, bạn có thể "
                      f"dùng thử bằng hồ sơ mẫu.", 13, 400, MUTED),
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

    def phone_sign_in(self) -> None:
        prof = self.state.profile or Profile(provider="phone")
        prof.phone = "+84 " + self.state.phone if self.state.phone else prof.phone
        prof.name = prof.name or "Bạn"
        self.complete_sign_in(prof)

    def sign_out(self) -> None:
        async def _do():
            try:
                await self.prefs.remove(PREFS_KEY)
            except Exception:
                pass
            self.state = AppState()
            self.signed_in = False
            self.page.views.clear()
            await self.page.push_route("/")
            if not self.page.views:
                self._on_route_change(None)
        self.page.run_task(_do)

    def open_url(self, url: str) -> None:
        if not url.startswith("http"):
            url = "https://" + url
        self.page.run_task(self.launcher.launch_url, url)
