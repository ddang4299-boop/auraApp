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
        # 429: Google báo phải chờ bao lâu (hết lượt/phút: vài chục giây; hết lượt/ngày: nhiều giờ)
        m = re.search(r"retryDelay'?\"?:\s*'?\"?(\d+)", str(e))
        return float(m.group(1)) if m else self.cooldown


class GeminiLLM:
    """Google AI Studio (free tier). pip install google-genai"""

    def __init__(self, model: str, api_key: str, temperature: float = 0.2):
        from google import genai
        from google.genai import types
        try:
            self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=int(TIMEOUT * 1000)))
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
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=TIMEOUT, max_retries=1)
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
    "gemini":     ("GEMINI_API_KEY",     "gemini-3.8-flash",        None),
    "groq":       ("GROQ_API_KEY",       "openai/gpt-oss-120b",     "https://api.groq.com/openai/v1"),
    "openrouter": ("OPENROUTER_API_KEY", "",                        "https://openrouter.ai/api/v1"),
    "anthropic":  ("ANTHROPIC_API_KEY",  "claude-haiku-5-5",        None),
}


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


def _build(provider: str) -> Optional[LLMFn]:
    provider = provider.strip().lower()
    if provider not in PROVIDERS:
        raise ValueError(f"Provider không hợp lệ: {provider}. Chọn: {list(PROVIDERS)}")
    key_env, default_model, base_url = PROVIDERS[provider]
    key = os.getenv(key_env)
    if not key:
        return None
    # LLM_MODEL chỉ áp cho provider chính; fallback luôn dùng model mặc định (hoặc <PROVIDER>_MODEL)
    model = os.getenv(f"{provider.upper()}_MODEL") or default_model
    if not model:
        raise ValueError(f"{provider} cần đặt {provider.upper()}_MODEL trong .env (vd model có đuôi ':free').")
    if provider == "gemini":
        return GeminiLLM(model, key)
    if provider == "anthropic":
        return AnthropicLLM(model, key)
    return OpenAICompatLLM(model, key, base_url)


def make_llm() -> Optional[LLMFn]:
    """LLM_PROVIDER = provider chính, LLM_FALLBACK = provider dự phòng (có thể để trống).
    Provider nào thiếu key thì bị bỏ qua; không còn cái nào -> None (engine chạy keyword offline)."""
    names = [os.getenv("LLM_PROVIDER", "gemini")] + [os.getenv("LLM_FALLBACK", "")]
    chain = []
    for n in names:
        if not n.strip():
            continue
        try:
            m = _build(n)
        except (ImportError, ValueError) as e:   # thiếu thư viện / cấu hình sai: bỏ qua provider này
            print(f"[llm] Bỏ qua provider '{n}': {e}")
            continue
        if m:
            chain.append(CircuitBreaker(m))
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