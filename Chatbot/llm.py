"""
Adapter LLM. Engine chỉ cần 1 hàm: llm(system, user, max_tokens) -> str
Chọn nhà cung cấp bằng .env:  LLM_PROVIDER = gemini | groq | openrouter | anthropic
make_llm() trả None nếu thiếu key -> Engine tự chạy chế độ keyword offline.
"""
from __future__ import annotations

import os
import re
import time
from typing import Callable, Optional

try:  # tuỳ chọn: pip install python-dotenv
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LLMFn = Callable[[str, str, int], str]
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30"))   # giây; quá hạn thì báo lỗi (để chuyển provider dự phòng), không treo


def _is_timeout(e: Exception) -> bool:
    return "timeout" in (type(e).__name__ + str(e)).lower() or "timed out" in str(e).lower()


def _is_bad_config(e: Exception) -> bool:
    """Lỗi 400 = model không nhận kiểu cấu hình này (vd thinking_budget) -> đáng thử kiểu khác.
    Các lỗi còn lại (429 hết lượt, 503/504 quá tải, mạng, timeout) thử kiểu khác cũng vô ích."""
    s = str(e)
    return "400" in s or "INVALID_ARGUMENT" in s


class CircuitBreaker:
    """Bọc 1 LLM. Khi nó vừa quá tải / hết lượt / quá giờ thì "nghỉ" một lúc:
    trong lúc nghỉ, mọi lần gọi báo lỗi NGAY (0 giây) để engine dùng chế độ từ khoá offline,
    thay vì lượt nào người dùng cũng phải chờ hết LLM_TIMEOUT rồi mới được trả lời."""

    def __init__(self, llm, cooldown: float = 30.0):
        self.llm, self.cooldown = llm, cooldown
        self.label = getattr(llm, "label", type(llm).__name__)
        self.until = 0.0                      # thời điểm hết nghỉ

    def __call__(self, system: str, user: str, max_tokens: int = 450) -> str:
        wait = self.until - time.time()
        if wait > 0:
            raise RuntimeError(f"{self.label} đang tạm nghỉ {wait:.0f}s sau lỗi quá tải")
        try:
            return self.llm(system, user, max_tokens)
        except Exception as e:
            if not _is_bad_config(e):
                pause = self._pause_for(e)
                self.until = time.time() + pause
                how_long = f"{pause / 3600:.1f} giờ" if pause >= 3600 else f"{pause:.0f}s"
                print(f"[llm] {self.label} lỗi ({str(e)[:60]}...) -> tạm dùng offline {how_long}")
            raise

    def _pause_for(self, e: Exception) -> float:
        s = str(e)
        # Key sai / hết tín dụng: thử lại sau vài giây cũng vô ích -> nghỉ 1 giờ (đỡ tốn thời gian mỗi lượt)
        if re.search(r"\b40[13]\b|invalid api key|incorrect api key|insufficient_quota|no credits", s, re.I):
            return 3600.0
        # 429: Google báo phải chờ bao lâu (hết lượt/phút: vài chục giây; hết lượt/ngày: nhiều giờ)
        m = re.search(r"retryDelay'?\"?:\s*'?\"?(\d+)", s)
        if m:
            return float(m.group(1))
        # 429 của Groq: "Please try again in 4.11s" / "in 7m12.5s" / "in 450ms" -> nghỉ đúng chừng đó
        m = re.search(r"try again in ([\d.hms]+)", s)
        if m:
            unit = {"ms": 0.001, "h": 3600.0, "m": 60.0, "s": 1.0}
            wait = sum(float(n) * unit[u] for n, u in re.findall(r"([\d.]+)(ms|h|m|s)", m.group(1)))
            if wait > 0:
                return max(2.0, wait + 1.0)
        return self.cooldown


class GeminiLLM:
    """Google AI Studio (free tier). pip install google-genai"""

    def __init__(self, model: str, api_key: str, temperature: float = 0.2):
        from google import genai
        from google.genai import types
        try:
            # Google không nhận thời hạn dưới 10 giây (báo lỗi 400 "Minimum allowed deadline is 10s")
            self.client = genai.Client(api_key=api_key,
                                       http_options=types.HttpOptions(timeout=int(max(TIMEOUT, 10) * 1000)))
        except Exception:  # SDK cũ không có http_options
            self.client = genai.Client(api_key=api_key)
        self.model, self.temperature = model, temperature
        self.label = f"gemini/{model}"
        self._variant = 0          # nhớ kiểu cấu hình đã chạy được, lần sau dùng luôn

    def __call__(self, system: str, user: str, max_tokens: int = 450) -> str:
        from google.genai import types
        base = dict(system_instruction=system, temperature=self.temperature,
                    max_output_tokens=max_tokens + 1500)   # model "suy nghĩ" tính vào hạn mức: luôn chừa chỗ dư
        if "JSON" in system:       # prompt định tuyến: bắt model trả JSON chuẩn -> khỏi phải gọi lại vì lỗi đọc
            base["response_mime_type"] = "application/json"
        variants = (  # giảm thinking nếu được; SDK/model không hỗ trợ kiểu nào thì thử kiểu kế
            lambda: dict(base, thinking_config=types.ThinkingConfig(thinking_budget=0)),
            lambda: dict(base, thinking_config=types.ThinkingConfig(thinking_level="low")),
            lambda: dict(base),
        )
        last = None
        for i in range(self._variant, len(variants)):
            try:
                cfg = types.GenerateContentConfig(**variants[i]())
                r = self.client.models.generate_content(model=self.model, contents=user, config=cfg)
                if (r.text or "").strip():
                    self._variant = i
                    return r.text
                last = RuntimeError("Gemini trả về chuỗi rỗng (hết token suy nghĩ hoặc bị bộ lọc chặn)")
            except Exception as e:
                last = e
                if not _is_bad_config(e):   # quá tải / hết lượt / quá giờ: báo lỗi ngay, không thử tiếp
                    break
        raise last


class OpenAICompatLLM:
    """Groq / OpenRouter / bất kỳ API tương thích OpenAI. pip install openai"""

    def __init__(self, model: str, api_key: str, base_url: str, temperature: float = 0.2):
        from openai import OpenAI
        # max_retries=0: hết lượt (429) thì báo lỗi NGAY để chuyển sang model dự phòng, thay vì thư viện
        # tự ngồi chờ 10-20 giây rồi thử lại trong khi người dùng nhìn màn hình đứng.
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=TIMEOUT, max_retries=0)
        self.model, self.temperature = model, temperature
        self.label = f"{base_url.split('//')[1].split('/')[0]}/{model}"

    def __call__(self, system: str, user: str, max_tokens: int = 450) -> str:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        reasoning = any(k in self.model.lower() for k in ("gpt-oss", "qwen3", "deepseek-r1"))
        tries = [dict(max_tokens=max_tokens + 1500, extra_body={"reasoning_effort": "low"})] if reasoning else []
        tries.append(dict(max_tokens=max_tokens + (1500 if reasoning else 0)))
        last = None
        for kw in tries:
            try:
                r = self.client.chat.completions.create(model=self.model, temperature=self.temperature,
                                                        messages=msgs, **kw)
                out = r.choices[0].message.content or ""
                if out.strip():
                    return out
                last = RuntimeError("Model trả về chuỗi rỗng")
            except Exception as e:
                last = e
                if not _is_bad_config(e):
                    break
        raise last


class AnthropicLLM:
    """Claude (trả phí). pip install anthropic"""

    def __init__(self, model: str, api_key: Optional[str] = None, temperature: float = 0.2):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT, max_retries=1)
        self.model, self.temperature = model, temperature
        self.label = f"anthropic/{model}"

    def __call__(self, system: str, user: str, max_tokens: int = 450) -> str:
        r = self.client.messages.create(
            model=self.model, max_tokens=max_tokens, temperature=self.temperature,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in r.content if b.type == "text")


# provider -> (biến env chứa key, model mặc định, base_url nếu dùng OpenAI-compat)
PROVIDERS = {
    "gemini":     ("GEMINI_API_KEY",     "gemini-3.8-flash",            None),
    "groq":       ("GROQ_API_KEY",       "openai/gpt-oss-120b",         "https://api.groq.com/openai/v1"),
    # model miễn phí của OpenRouter có đuôi ":free" (~50 lượt/ngày nếu tài khoản chưa nạp tiền)
    "openrouter": ("OPENROUTER_API_KEY", "google/gemma-4-31b-it:free",  "https://openrouter.ai/api/v1"),
    # OpenAI tính phí theo lượt (cần nạp tín dụng ở platform.openai.com); gpt-4.1-mini nhanh, rẻ
    "openai":     ("OPENAI_API_KEY",     "gpt-4.1-mini",                "https://api.openai.com/v1"),
    "anthropic":  ("ANTHROPIC_API_KEY",  "claude-haiku-5-5",            None),
}
# Tên biến khác mà người dùng hay đặt cho cùng một key
KEY_ALIASES = {"OPENAI_API_KEY": ["CHAT_GPT_KEY", "CHATGPT_API_KEY"]}


class FallbackLLM:
    """Gọi lần lượt các LLM; cái trước lỗi (hết quota, rate limit, mạng...) thì thử cái sau."""

    def __init__(self, chain: list):
        self.chain = chain

    def __call__(self, system: str, user: str, max_tokens: int = 450) -> str:
        errors = []
        for llm in self.chain:
            try:
                return llm(system, user, max_tokens)
            except Exception as e:  # thử provider kế tiếp, nhưng nhớ lại lỗi để báo
                errors.append(f"[{getattr(llm, 'label', type(llm).__name__)}] {str(e)[:300]}")
        raise RuntimeError("Tất cả LLM đều lỗi:\n  " + "\n  ".join(errors))


def _keys(key_env: str) -> list:
    """Mọi key của một provider: KEY, KEY_2, KEY_3... (và tên thay thế trong KEY_ALIASES).
    Mỗi tài khoản Groq / Google có hạn mức riêng, nên thêm key của tài khoản khác = thêm sức chịu tải."""
    found = []
    for name in [key_env] + KEY_ALIASES.get(key_env, []):
        for suffix in [""] + [f"_{i}" for i in range(2, 10)]:
            v = (os.getenv(name + suffix) or "").strip()
            if v and v not in found:
                found.append(v)
    return found


def _build_all(provider: str) -> list:
    """provider = "groq" (model mặc định / <PROVIDER>_MODEL) hoặc "groq:openai/gpt-oss-20b" (chỉ rõ model).
    Trả về 1 LLM cho mỗi key của provider đó (theo thứ tự KEY, KEY_2, ...)."""
    provider, _, pinned = provider.strip().partition(":")
    provider = provider.lower()
    if provider not in PROVIDERS:
        raise ValueError(f"Provider không hợp lệ: {provider}. Chọn: {list(PROVIDERS)}")
    key_env, default_model, base_url = PROVIDERS[provider]
    model = pinned.strip() or os.getenv(f"{provider.upper()}_MODEL") or default_model
    if not model:
        raise ValueError(f"{provider} cần đặt {provider.upper()}_MODEL trong .env (vd model có đuôi ':free').")
    out = []
    for i, key in enumerate(_keys(key_env), 1):
        if provider == "gemini":
            m = GeminiLLM(model, key)
        elif provider == "anthropic":
            m = AnthropicLLM(model, key)
        else:
            m = OpenAICompatLLM(model, key, base_url)
        if i > 1:
            m.label += f" (key {i})"
        out.append(m)
    return out


def _build(provider: str) -> Optional[LLMFn]:
    """Như _build_all nhưng chỉ lấy key đầu tiên (dùng cho chẩn đoán)."""
    ms = _build_all(provider)
    return ms[0] if ms else None


def make_llm() -> Optional[LLMFn]:
    """LLM_PROVIDER = provider chính, LLM_FALLBACK = các provider dự phòng, cách nhau dấu phẩy
    (vd "groq:openai/gpt-oss-20b,gemini"). Có thể để trống. Provider có nhiều key (GROQ_API_KEY, GROQ_API_KEY_2...)
    thì thử lần lượt từng key trước khi sang provider kế.
    Provider nào thiếu key thì bị bỏ qua; không còn cái nào -> None (engine chạy keyword offline)."""
    names = [os.getenv("LLM_PROVIDER", "gemini")] + os.getenv("LLM_FALLBACK", "").split(",")
    chain = []
    for n in names:
        if not n.strip():
            continue
        try:
            ms = _build_all(n)
        except (ImportError, ValueError) as e:   # thiếu thư viện / cấu hình sai: bỏ qua provider này
            print(f"[llm] Bỏ qua provider '{n}': {e}")
            continue
        chain += [CircuitBreaker(m) for m in ms]
    if not chain:
        return None
    return chain[0] if len(chain) == 1 else FallbackLLM(chain)


def _diagnose() -> None:
    """python -m Chatbot.llm : thử từng provider có key, in lỗi thật và danh sách model dùng được."""
    found = False
    for name, (key_env, default_model, base_url) in PROVIDERS.items():
        if not os.getenv(key_env):
            continue
        found = True
        model = os.getenv(f"{name.upper()}_MODEL") or default_model
        print(f"\n=== {name}  (model đang dùng: {model or 'CHƯA ĐẶT'}) ===", flush=True)
        print(f"  đang gọi thử (tối đa {TIMEOUT:.0f}s)...", flush=True)
        t0 = time.time()
        try:
            llm = _build(name)
            print("  trả lời:", repr(llm("Trả lời đúng 1 từ.", "Chào bạn", 20).strip()[:60]),
                  f"-> OK ({time.time() - t0:.1f}s)", flush=True)
        except Exception as e:
            print(f"  LỖI sau {time.time() - t0:.1f}s:", str(e)[:400], flush=True)
        try:  # liệt kê model tài khoản này dùng được
            if name == "gemini":
                from google import genai
                client = genai.Client(api_key=os.getenv(key_env))   # phải giữ biến, nếu không client bị đóng khi đang duyệt
                ms = [m.name.replace("models/", "") for m in client.models.list()
                      if "generateContent" in (getattr(m, "supported_actions", None) or ["generateContent"])]
            elif name == "anthropic":
                continue
            else:
                from openai import OpenAI
                ms = [m.id for m in OpenAI(api_key=os.getenv(key_env), base_url=base_url).models.list().data]
            print(f"  model dùng được ({len(ms)}):", ", ".join(sorted(ms)[:40]))
            print(f"  -> chọn 1 tên rồi đặt {name.upper()}_MODEL=<tên> trong .env")
        except Exception as e:
            print("  không liệt kê được model:", str(e)[:200])
    if not found:
        print("Chưa có key nào trong .env (GEMINI_API_KEY / GROQ_API_KEY ...).")


if __name__ == "__main__":
    _diagnose()