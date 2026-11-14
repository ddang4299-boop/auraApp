"""Điều hướng, trạng thái và vòng đời ứng dụng AURA."""
from __future__ import annotations

import asyncio
import importlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import flet as ft

from . import auth
from .auth import Profile
from .data import DEFAULT_ID, PAINTINGS
from .socratic import (Message, ScriptedSocraticEngine, SocraticEngine, message_from_dict,
                       message_to_dict)
from .theme import BG, FONTS, GUTTER, INK, MAX_W, MUTED, PRIMARY
from .ui import FRAME_W, T, compact, snack

PREFS_KEY = "aura.profile"
# Cuộc trò chuyện được cất trong bộ nhớ của trình duyệt (localStorage, qua SharedPreferences):
# lỡ tải lại trang (F5), máy chủ khởi động lại hay mở lại app thì vẫn nói tiếp được đúng chỗ cũ.
CHATS_KEY = "aura.chats"
CHATS_VERSION = 1
ASK_KEY = "aura.ask"                   # cuộc hỏi đáp ở tab "Hỏi Aura"
SAVED_KEY = "aura.saved"               # tranh đã lưu (dấu trang)
SCAN_HINT_KEY = "aura.scan_hint"       # "off" = đã tắt bong bóng "Quét tranh ngay" trên nút Scan
ASK_KEEP = 60                          # chỉ cất ngần này tin gần nhất của "Hỏi Aura"
APP_VERSION = "1.2.0"

# Các tab trên thanh điều hướng: mở tab thì giữ sẵn Trang chủ ở đáy stack (xem _show).
# /scan không phải tab: màn kết quả quét chồng lên màn đang xem, quay lại là về đúng chỗ cũ.
ROOT_ROUTES = {"/", "/home", "/gallery", "/saved", "/ask", "/settings"}
SCAN_MAX_BYTES = 25 * 1024 * 1024      # ảnh lớn hơn thì từ chối (ảnh điện thoại thường 2-12 MB)
UPLOAD_WAIT = 120                      # chờ tải ảnh lên tối đa ngần này giây
# Bản web lúc mới mở hay báo bề rộng tạm (vd 164px). Điện thoại thật rộng ít nhất ~320px,
# nên hẹp hơn TEMP_W thì coi là chưa biết khổ màn hình (xem AuraApp._waiting_width).
TEMP_W = 300
WIDTH_WAIT = 1.5


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
class AskState:
    """Tab "Hỏi Aura": mỗi tin là một dict JSON được (cất thẳng vào bộ nhớ trình duyệt).
    {"role": "user"|"aura", "text", "painting", "identified", "topic", "source", "confidence"}"""
    messages: list[dict] = field(default_factory=list)
    thinking: bool = False


@dataclass
class ScanState:
    """Màn Scan (chỉ giữ trong phiên đang mở, không cất vào trình duyệt). Xem screens/scan.py."""
    phase: str = "ready"               # ready | working | result
    result: object | None = None       # vision.ScanResult của lần quét gần nhất
    error: str | None = None           # too_big | upload | bad_image | unavailable
    declined: bool = False             # người dùng bấm "Không phải" ở câu "Có phải bức này không?"
    job: int = 0                       # tăng mỗi lần quét mới / huỷ: kết quả của lượt cũ bị bỏ qua
    step: int = 0                      # 0 đang gửi ảnh, 1 đang nhận diện
    started: float = 0.0               # lúc bắt đầu lượt quét (time.monotonic)
    step_at: float = 0.0               # lúc chuyển sang bước nhận diện
    screen: object | None = None       # màn /scan đang dựng (để cập nhật tại chỗ)


@dataclass
class AppState:
    profile: Profile | None = None
    saved: set[str] = field(default_factory=set)
    quizzes: dict[str, QuizState] = field(default_factory=dict)
    chats: dict[str, ChatState] = field(default_factory=dict)
    ask: AskState = field(default_factory=AskState)
    scan: ScanState = field(default_factory=ScanState)
    gallery_tab: str = "all"           # Kho tranh đang mở phần nào: "all" | "saved"

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
    ("/ask", "ask", "build"),
    ("/scan", "scan", "build"),
    ("/settings", "settings", "build"),
    ("/about", "settings", "about"),
    ("/privacy", "settings", "privacy"),
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
        # Bề rộng tạm thì CHƯA dựng màn (máy chủ 0,1 CPU dựng hai lần mất thêm ~1 giây): chờ trình duyệt
        # báo bề rộng thật rồi dựng một lần; quá WIDTH_WAIT giây không thấy báo thì dựng luôn.
        self._waiting_width = self.page_width < TEMP_W
        self._first_route = page.route or "/"
        # Dịch vụ của Flet: lưu trữ cục bộ và mở trình duyệt/URL.
        self.prefs = ft.SharedPreferences()
        self.launcher = ft.UrlLauncher()
        # Hộp chọn ảnh cho Scan; bản web hiện khung quét trực tiếp (assets/aura-scan.js).
        # Xem pick_action / receive_photo và screens/scan.py.
        self.picker = ft.FilePicker(on_upload=self._on_upload, on_result=self._on_pick_result)
        self._uploads: dict[str, asyncio.Future] = {}
        # Bong bóng "Quét tranh ngay" trên nút Scan: None = chưa đọc xong bộ nhớ trình duyệt (dựng sẵn
        # nhưng ẩn), True = hiện, False = người dùng đã tắt. _hints: các bong bóng đang nằm trên màn.
        self.scan_hint: bool | None = None
        self._hints: list[ft.Control] = []
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
        if self._waiting_width:
            page.views.append(ft.View(route=self._first_route, bgcolor=BG))    # nền trống trong lúc chờ
            page.update()
            page.run_task(self._width_fallback)
        else:
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
        if path in ("/profile", "/about", "/privacy"):
            return "/settings"
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
            view = builder(self, query, *args)
        finally:
            FRAME_W.reset(token)
        compact(view)                  # bỏ các control khoảng trống trước khi gửi đi (giảm RAM, xem ui.compact)
        return view

    def rebuild(self) -> None:
        """Dựng lại màn hình hiện tại (sau khi đổi trạng thái lớn)."""
        views = self.page.views
        if views and not self._waiting_width:
            views[-1] = self._build(views[-1].route)
            self.page.update()

    def _end_wait(self) -> None:
        """Đã biết bề rộng thật (hoặc chờ quá lâu): dựng màn đầu tiên đúng một lần."""
        if not self._waiting_width:
            return
        self._waiting_width = False
        self._laid_out_width = self.page_width
        self.page.views.clear()
        self._show(self._first_route)

    async def _width_fallback(self) -> None:
        await asyncio.sleep(WIDTH_WAIT)
        self._end_wait()

    def _on_resize(self, e) -> None:
        if self._waiting_width:
            if self.page_width >= TEMP_W:
                self._end_wait()
            return
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
        if self._waiting_width:          # chưa biết khổ màn hình: nhớ màn cần mở, dựng khi biết
            self._first_route = route
            return
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
            snack(self.page, "Đã lưu tranh. Xem lại trong Kho tranh › Đã lưu.")
        self.touch()
        self.page.run_task(self._write_pref, SAVED_KEY, json.dumps(sorted(saved)))
        return pid in saved

    # ---- tài khoản ----------------------------------------------------------------
    @property
    def profile(self) -> Profile:
        if self.state.profile is None:
            self.state.profile = Profile(name="Khách", provider="guest")
        return self.state.profile

    async def _restore_session(self) -> None:
        """Đọc lại cuộc trò chuyện đang dở, tự đăng nhập lại nếu đã lưu hồ sơ, rồi mở hướng dẫn cho người mới."""
        try:
            await self._restore_chats()
            await self._restore_local()
        finally:
            self._chats_ready.set()
        try:
            await self._restore_profile()
        finally:
            await asyncio.sleep(0.6)       # để màn đầu tiên hiện xong rồi mới mở hộp hướng dẫn
            from .screens import onboarding
            await onboarding.maybe_show(self)

    async def _restore_profile(self) -> None:
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

    async def _restore_local(self) -> None:
        """Đọc lại tranh đã lưu và cuộc hỏi đáp ở tab "Hỏi Aura" (dữ liệu hỏng thì bỏ qua)."""
        try:
            raw = await self.prefs.get(SAVED_KEY)
            ids = json.loads(raw) if raw else []
            if isinstance(ids, list) and not self.state.saved:
                self.state.saved = {i for i in ids if i in PAINTINGS}
                self.touch()
                # màn đang hiện đã dựng trước khi đọc xong (vd mở thẳng /saved ở tab mới): vẽ lại cho đúng
                path = urlsplit(self.page.views[-1].route if self.page.views else "/").path
                if self.state.saved and (path in ("/gallery", "/saved", "/settings", "/profile")
                                         or path.startswith("/painting/")):
                    self.rebuild()
        except Exception as e:
            print(f"[app] Bỏ danh sách tranh đã lưu: {e}")
        try:
            raw = await self.prefs.get(ASK_KEY)
            data = json.loads(raw) if raw else None
            msgs = data.get("messages") if isinstance(data, dict) and data.get("v") == 1 else None
            if isinstance(msgs, list) and not self.state.ask.messages:
                self.state.ask.messages = [m for m in msgs if isinstance(m, dict)
                                           and m.get("role") in ("user", "aura") and isinstance(m.get("text"), str)]
        except Exception as e:
            print(f"[app] Bỏ cuộc hỏi đáp đã lưu: {e}")
        try:
            raw = await self.prefs.get(SCAN_HINT_KEY)
        except Exception:
            raw = None
        if self.scan_hint is None:
            self.scan_hint = raw != "off"
            if self.scan_hint:
                await self._reveal_hints()

    def save_ask(self) -> None:
        msgs = self.state.ask.messages[-ASK_KEEP:]
        self.page.run_task(self._write_pref, ASK_KEY, json.dumps({"v": 1, "messages": msgs}, ensure_ascii=False))

    # ---- Scan: bong bóng gợi ý "Quét tranh ngay" ---------------------------------
    def keep_hint(self, bubble: ft.Control) -> None:
        """nav_bar báo có một bong bóng mới trên màn (chỉ giữ vài cái gần nhất: màn cũ đã bị thay)."""
        self._hints = self._hints[-5:] + [bubble]

    async def _reveal_hints(self) -> None:
        """Vừa biết là cần hiện bong bóng: hiện dần các bong bóng đã dựng sẵn (đang ẩn) trên màn."""
        hints = [b for b in self._hints if not b.visible]
        for b in hints:
            b.visible, b.opacity, b.offset = True, 0, ft.Offset(0, 0.25)
        self._update_all(hints)
        await asyncio.sleep(0.08)
        for b in hints:
            b.opacity, b.offset = 1, ft.Offset(0, 0)
        self._update_all(hints)

    def scan_tapped(self, e=None) -> None:
        """Nút Scan vừa được bấm (khung quét đã tự mở trên trình duyệt nhờ `action`): tắt bong bóng gợi ý và
        nạp sẵn bộ nhận diện trong lúc người dùng ngắm."""
        self.dismiss_scan_hint()
        from .screens import scan
        self.page.run_task(scan.warm)

    def dismiss_scan_hint(self, e=None) -> None:
        """Bấm vào bong bóng (hoặc dùng Scan lần đầu): tắt hẳn, lần sau không hiện nữa."""
        if self.scan_hint is False:
            return
        self.scan_hint = False
        self.page.run_task(self._write_pref, SCAN_HINT_KEY, "off")
        hints, self._hints = self._hints, []
        for b in hints:
            b.opacity, b.offset = 0, ft.Offset(0, 0.2)
        self._update_all(hints)

        async def _gone():
            await asyncio.sleep(0.3)
            for b in hints:
                b.visible = False
            self._update_all(hints)
        self.page.run_task(_gone)

    @staticmethod
    def _update_all(controls: list[ft.Control]) -> None:
        for c in controls:
            try:
                c.update()
            except Exception:            # màn chứa bong bóng đã bị thay
                pass

    # ---- Scan: lấy ảnh người dùng chụp / chọn --------------------------------
    def pick_action(self) -> ft.PickFiles:
        """Gắn vào nút Scan / nút chụp (thuộc tính `action`): TRÌNH DUYỆT mở hộp chọn ảnh ngay trong cú chạm,
        không đợi hỏi máy chủ Python. Safari trên iPhone chỉ cho mở hộp chọn tệp trong lúc đang xử lý cú chạm,
        nên cách gọi pick_files từ Python (phải đi một vòng qua máy chủ) bị Safari lặng lẽ chặn.
        Bản web: assets/aura-scan.js đón lệnh này và hiện khung quét có camera trực tiếp + nút Thư viện ảnh.
        App trên máy: hộp chọn ảnh của hệ điều hành. Ảnh chọn xong (hoặc huỷ) về _on_pick_result."""
        # bản web chạy không có thư mục nhận ảnh (vd `flet run --web`): đọc ảnh thẳng qua kết nối
        with_data = bool(self.page.web and not os.environ.get("AURA_UPLOAD_DIR"))
        # cancel_upload_on_window_blur=False: mở camera làm trang web mất tiêu điểm; để mặc định (True)
        # thì Flet coi đó là người dùng huỷ và bỏ luôn ảnh vừa chụp.
        return ft.PickFiles(self.picker, dialog_title="Chọn ảnh bức tranh", file_type=ft.FilePickerFileType.IMAGE,
                            with_data=with_data, cancel_upload_on_window_blur=False)

    async def _on_pick_result(self, e) -> None:
        from .screens import scan
        await scan.on_photo(self, e.files[0] if e.files else None)

    async def receive_photo(self, f) -> bytes:
        """Lấy nội dung ảnh vừa chọn.
        - App trên máy tính/điện thoại: đọc thẳng tệp.
        - Bản web: trình duyệt gửi ảnh lên máy chủ qua một đường dẫn có chữ ký, sống 5 phút. Ảnh nằm
          tạm trong thư mục tạm, đọc xong là xoá ngay (cả ảnh sót lại từ lần trước, quá 10 phút)."""
        if f.bytes:
            return f.bytes
        if f.path:
            return await asyncio.to_thread(Path(f.path).read_bytes)
        folder = os.environ.get("AURA_UPLOAD_DIR")
        if not folder:
            raise RuntimeError("chưa cấu hình thư mục nhận ảnh")
        await asyncio.to_thread(_sweep_uploads, folder)
        name = f"scan_{uuid.uuid4().hex}"
        dest = Path(folder) / name
        fut = asyncio.get_running_loop().create_future()
        self._uploads[f.name] = fut
        try:
            await self.picker.upload([ft.FilePickerUploadFile(upload_url=self.page.get_upload_url(name, 300),
                                                              id=f.id, name=f.name)])
            await asyncio.wait_for(fut, UPLOAD_WAIT)
            return await asyncio.to_thread(dest.read_bytes)
        finally:
            if self._uploads.get(f.name) is fut:       # chỉ gỡ lượt chờ của chính mình
                del self._uploads[f.name]
            dest.unlink(missing_ok=True)

    async def _on_upload(self, e) -> None:
        """Trình duyệt báo tiến độ gửi ảnh: 1.0 = xong, có error = lỗi."""
        fut = self._uploads.get(e.file_name)
        if fut is None and len(self._uploads) == 1:
            fut = next(iter(self._uploads.values()))
        if fut is None or fut.done():
            return
        if e.error:
            fut.set_exception(RuntimeError(e.error))
        elif e.progress is not None and e.progress >= 1:
            fut.set_result(None)

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
            # máy dùng chung: người sau không thấy hồ sơ, cuộc trò chuyện, tranh đã lưu của người trước
            for key in (PREFS_KEY, CHATS_KEY, ASK_KEY, SAVED_KEY):
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


def _sweep_uploads(folder: str, older_than: float = 600) -> None:
    """Xoá ảnh Scan sót lại trong thư mục tạm (vd người dùng đóng trang giữa chừng)."""
    now = time.time()
    try:
        for p in Path(folder).glob("scan_*"):
            if now - p.stat().st_mtime > older_than:
                p.unlink(missing_ok=True)
    except OSError:
        pass
