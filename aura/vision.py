"""Scan ảnh tác phẩm: nhận ra bức tranh trong ảnh người dùng chụp bằng cách "nhớ điểm".

Cách làm (so khớp điểm đặc trưng, không cần huấn luyện model):
1. Với mỗi bức trong Kho tranh, tìm sẵn khoảng 1.500 "điểm đáng nhớ" (SIFT): góc mắt, nếp áo, mép tay...
   Mỗi điểm có một dãy số mô tả vùng nhỏ quanh nó, gần như không đổi khi ảnh bị xoay, phóng to/thu nhỏ
   hay đổi độ sáng. Mỗi bức được nhớ ở 3 mức nét (nét, hơi mờ, mờ) để ảnh chụp bị mờ vẫn có cái mà khớp.
2. Ảnh chụp cũng được tìm điểm như vậy, rồi ghép từng điểm với điểm giống nhất trên tranh gốc
   (phép thử tỉ lệ Lowe: chỉ giữ cặp mà cặp tốt nhất hơn hẳn cặp tốt nhì).
3. RANSAC tìm phép chiếu phối cảnh (homography) mà nhiều cặp tuân theo nhất. Ghép nhầm ngẫu nhiên
   gần như không bao giờ nhất quán với cùng một phép chiếu, nên số cặp tuân theo ("inliers") là thước
   đo đáng tin. Kiểm thêm: 4 góc tranh chiếu lên ảnh chụp phải là tứ giác lồi, kích thước hợp lý.
4. Quyết định: đủ nhiều inliers và hơn hẳn bức đứng thứ hai -> "sure"; ít hơn nhưng vẫn nổi bật
   -> "ask" (hỏi lại người dùng "Có phải bức này không?"); còn lại -> "none" (không đoán bừa).

Nhờ chỉ cần một phần các điểm khớp, ảnh chụp thiếu góc, chụp nghiêng, đứng xa hay lóa đèn vẫn nhận
ra được. Ảnh mờ/rung nặng thì chi tiết đã mất, nên trả "none" và gợi ý chụp lại.
Thêm nữa: phép chiếu cho biết ảnh chụp ứng với vùng nào trên tranh -> đoán chi tiết người dùng đang
chĩa máy vào (so với Detail.crop trong data.py).

OpenCV (gói opencv-python-headless) chỉ được nạp khi Scan được dùng lần đầu, nên không làm app khởi
động chậm hơn. Thiếu gói này thì available() trả False và màn Scan báo chưa sẵn sàng.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

LONG_SIDE = 800              # thu nhỏ ảnh về cạnh dài 800px trước khi tìm điểm (nhanh, và đỡ mờ/nhiễu)
N_FEATURES = 1500
REF_BLURS = (0, 2.5, 5)      # các mức "nhớ" của tranh gốc: nét, hơi mờ, mờ
RATIO = 0.75                 # phép thử tỉ lệ Lowe
SURE_INLIERS = 20            # từ thử nghiệm: ảnh KHÔNG thuộc Kho cao nhất chỉ 7 inliers
ASK_INLIERS = 10
BLUR_VAR = 30.0              # độ nét (phương sai Laplacian) dưới mức này -> ảnh nhiều khả năng bị mờ/rung
DETAIL_MAX_COVER = 0.5       # ảnh chụp phủ dưới 50% bức tranh mới tính là "đang chụp một chi tiết"
QUERY_SIZES = (LONG_SIDE, 400)
RANK = {"none": 0, "ask": 1, "sure": 2}


@dataclass
class ScanResult:
    status: str                       # "sure" | "ask" | "none" | "bad_image" | "unavailable"
    painting: str | None = None
    detail: str | None = None         # key của Detail người dùng đang chĩa máy vào (nếu đoán được)
    inliers: int = 0
    second: int = 0
    blurry: bool = False
    thumb: bytes | None = None        # ảnh chụp thu nhỏ (JPEG) để hiện lại cho người dùng
    thumb_aspect: float = 1.0         # rộng / cao của ảnh thu nhỏ
    ms: int = 0


def available() -> bool:
    """Có cài OpenCV + numpy không. Chỉ DÒ, không nạp (nạp cv2 tốn ~15 MB RAM và vài giây CPU trên máy
    chủ yếu: để dành tới lúc thật sự quét, và làm trong luồng phụ để giao diện không đứng)."""
    from importlib.util import find_spec
    try:
        return find_spec("cv2") is not None and find_spec("numpy") is not None
    except (ImportError, ValueError):
        return False


_cv_ready = False


def _cv():
    """Nạp OpenCV một lần. Chạy 1 luồng: máy chủ chỉ có 0,1 CPU, nhiều luồng không nhanh hơn mà còn
    tốn RAM và giành CPU của các phiên khác."""
    global _cv_ready
    import cv2
    if not _cv_ready:
        cv2.setNumThreads(1)
        _cv_ready = True
    return cv2


def _trim_memory() -> None:
    """Linux: trả phần RAM vừa giải phóng (ảnh, ma trận tạm) về cho hệ điều hành ngay."""
    if os.name != "posix":
        return
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def _sha1(path: str) -> str:
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def _config_tag() -> str:
    """Tệp điểm tính sẵn chỉ dùng được khi cấu hình giống hệt."""
    cv2 = _cv()
    return f"v1|{LONG_SIDE}|{N_FEATURES}|{REF_BLURS}|{cv2.__version__.split('.')[0]}"


class Recognizer:
    """Bộ nhận diện dùng chung cho cả máy chủ (mọi phiên). An toàn khi gọi từ nhiều luồng."""

    def __init__(self, paintings, assets_dir: str, refs_file: str | None = None):
        self._paintings = list(paintings)
        self._assets = assets_dir
        self._refs_file = refs_file
        self._refs = None             # [(pid, pts Nx2 float32, descriptors float32, (h, w))]
        self._lock = threading.Lock()

    @property
    def ready(self) -> bool:
        return self._refs is not None

    def warm(self) -> None:
        """Nạp điểm đặc trưng của các bức tranh gốc (một lần).

        Đọc từ tệp tính sẵn (aura/scan_refs.npz, tạo bằng `python -m aura.vision`): gần như tức thì.
        Bức nào chưa có trong tệp, hoặc ảnh đã đổi (so mã sha1), thì tự tính lại: ~0,2 giây CPU mỗi bức
        (trên máy chủ 0,1 CPU là vài giây), nên nhớ chạy lại lệnh trên mỗi khi thêm/đổi ảnh tranh."""
        if self._refs is not None:
            return
        with self._lock:
            if self._refs is not None:
                return
            t0 = time.perf_counter()
            stored = self._load_file()
            refs, fresh = [], 0
            for p in self._paintings:
                path = os.path.join(self._assets, p.image)
                got = stored.get(p.id)
                if got is None or got[0] != _sha1(path):
                    got = (None, self._compute(path))
                    fresh += 1
                refs += [(p.id, pts, des, shape) for pts, des, shape in got[1]]
            self._refs = refs
            print(f"[scan] đã nhớ {len(refs)} bản của {len(self._paintings)} bức "
                  f"({fresh} bức tính mới) trong {(time.perf_counter() - t0) * 1000:.0f} ms")

    def _compute(self, path: str) -> list:
        cv2 = _cv()
        import numpy as np
        img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[scan] không đọc được ảnh gốc {path}")
            return []
        img = _shrink(img)
        sift = cv2.SIFT_create(nfeatures=N_FEATURES)
        out = []
        for blur in REF_BLURS:
            g = cv2.GaussianBlur(img, (0, 0), blur) if blur else img
            kp, des = sift.detectAndCompute(g, None)
            if des is not None and len(kp) >= 8:
                out.append((np.float32([k.pt for k in kp]), des.astype(np.float32), g.shape[:2]))
        return out

    def _load_file(self) -> dict:
        """{pid: (sha1 ảnh gốc, [(pts, des, shape)...])} từ tệp tính sẵn; tệp thiếu/hỏng/khác cấu hình -> {}."""
        if not self._refs_file or not os.path.exists(self._refs_file):
            return {}
        _cv()
        import numpy as np
        try:
            with np.load(self._refs_file, allow_pickle=False) as z:
                if str(z["config"]) != _config_tag():
                    print("[scan] tệp điểm tính sẵn khác cấu hình, tính lại")
                    return {}
                out: dict = {}
                for pid, sha, n_levels in zip(z["pids"], z["shas"], z["levels"]):
                    levels = []
                    for k in range(int(n_levels)):
                        key = f"{pid}__{k}"
                        h, w = (int(x) for x in z[key + "__shape"])
                        levels.append((z[key + "__pts"].astype(np.float32),
                                       z[key + "__des"].astype(np.float32), (h, w)))
                    out[str(pid)] = (str(sha), levels)
                return out
        except Exception as e:
            print(f"[scan] không đọc được tệp điểm tính sẵn: {e}")
            return {}

    def save_file(self, path: str) -> None:
        """Tính điểm của mọi bức và ghi ra tệp (descriptor SIFT là số nguyên 0-255 -> lưu 1 byte, không mất gì)."""
        import numpy as np
        arrays = {"config": np.array(_config_tag())}
        pids, shas, levels = [], [], []
        for p in self._paintings:
            src = os.path.join(self._assets, p.image)
            got = self._compute(src)
            pids.append(p.id)
            shas.append(_sha1(src))
            levels.append(len(got))
            for k, (pts, des, shape) in enumerate(got):
                key = f"{p.id}__{k}"
                arrays[key + "__pts"] = pts.astype(np.float32)
                arrays[key + "__des"] = np.clip(np.rint(des), 0, 255).astype(np.uint8)
                arrays[key + "__shape"] = np.array(shape, np.int32)
        arrays.update(pids=np.array(pids), shas=np.array(shas), levels=np.array(levels, np.int32))
        np.savez_compressed(path, **arrays)

    def recognize(self, data: bytes) -> ScanResult:
        t0 = time.perf_counter()
        try:
            cv2 = _cv()
            import numpy  # noqa: F401
        except Exception:
            return ScanResult("unavailable")
        try:
            return self._recognize(cv2, data, t0)
        finally:
            _trim_memory()

    def _recognize(self, cv2, data: bytes, t0: float) -> ScanResult:
        self.warm()
        color = _decode(data)
        if color is None:
            return ScanResult("bad_image")
        th = _shrink(color, 240)
        ok, buf = cv2.imencode(".jpg", th, [cv2.IMWRITE_JPEG_QUALITY, 75])
        thumb = buf.tobytes() if ok else None
        gray_full = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
        del color
        gray = _shrink(gray_full)
        blurry = cv2.Laplacian(gray, cv2.CV_64F).var() < BLUR_VAR
        res = ScanResult("none", blurry=blurry, thumb=thumb, thumb_aspect=th.shape[1] / th.shape[0])
        # Lượt 1 ở 800px. Chưa chắc thì dò lại ở ảnh nhỏ hơn: khi chụp sát một chi tiết, chi tiết đó trong
        # ảnh chụp to gấp nhiều lần so với trong ảnh gốc; thu nhỏ ảnh chụp giúp hai bên gần cỡ nhau hơn.
        for size in QUERY_SIZES:
            g = gray if size == LONG_SIDE else _shrink(gray_full, size)
            status, ranked = self._match(g)
            top = ranked[0][1][0] if ranked else 0
            if RANK[status] > RANK[res.status] or (status == res.status and top > res.inliers):
                res.status, res.inliers = status, top
                res.second = ranked[1][1][0] if len(ranked) > 1 else 0
                if status != "none":
                    pid, (_, H, rshape) = ranked[0]
                    res.painting = pid
                    res.detail = self._detail(pid, H, rshape, g.shape[:2])
            if res.status == "sure":
                break
        res.ms = round((time.perf_counter() - t0) * 1000)
        print(f"[scan] {res.status} {res.painting or '-'} inliers={res.inliers}/{res.second} "
              f"detail={res.detail or '-'} blurry={blurry} {res.ms} ms")
        return res

    def _match(self, gray):
        """So ảnh (xám, đã thu nhỏ) với mọi bản nhớ của mọi bức. Trả (trạng thái, xếp hạng theo inliers)."""
        cv2 = _cv()
        import numpy as np
        sift = cv2.SIFT_create(nfeatures=N_FEATURES)
        kp, des = sift.detectAndCompute(gray, None)
        best: dict[str, tuple[int, object, tuple]] = {}
        if des is not None and len(kp) >= 8:
            qpts = np.float32([k.pt for k in kp])
            matcher = cv2.BFMatcher(cv2.NORM_L2)
            for pid, rpts, rdes, rshape in self._refs:
                good = [m[0] for m in matcher.knnMatch(des, rdes, k=2)
                        if len(m) == 2 and m[0].distance < RATIO * m[1].distance]
                if len(good) < 8:
                    continue
                src = qpts[[m.queryIdx for m in good]]
                dst = rpts[[m.trainIdx for m in good]]
                H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
                if H is None or not _sane(H, rshape, gray.shape[:2]):
                    continue
                n = int(mask.sum())
                if n > best.get(pid, (0,))[0]:
                    best[pid] = (n, H, rshape)
        ranked = sorted(best.items(), key=lambda kv: kv[1][0], reverse=True)
        top = ranked[0][1][0] if ranked else 0
        second = ranked[1][1][0] if len(ranked) > 1 else 0
        if top >= SURE_INLIERS and top >= 2 * second:
            return "sure", ranked
        if top >= ASK_INLIERS and top >= 3 * max(second, 1):
            return "ask", ranked
        return "none", ranked

    def _detail(self, pid, H, rshape, qshape) -> str | None:
        """Ảnh chụp chỉ phủ một phần bức tranh -> tâm ảnh rơi vào chi tiết nào (Detail.crop)?"""
        cv2 = _cv()
        import numpy as np
        p = next((x for x in self._paintings if x.id == pid), None)
        if p is None or not p.details:
            return None
        qh, qw = qshape
        rh, rw = rshape
        corners = cv2.perspectiveTransform(np.float32([[[0, 0]], [[qw, 0]], [[qw, qh]], [[0, qh]]]), H)
        corners = corners.reshape(4, 2) / [rw, rh]
        clipped = np.clip(corners, 0, 1).astype(np.float32)
        cover = abs(cv2.contourArea(clipped))
        if cover >= DETAIL_MAX_COVER:
            return None
        cx, cy = cv2.perspectiveTransform(np.float32([[[qw / 2, qh / 2]]]), H).reshape(2) / [rw, rh]
        # các vùng chi tiết có thể chồng nhau (tay nằm trên váy): chọn vùng có tâm gần tâm ảnh chụp nhất
        hits = [(((d.crop[0] + d.crop[2]) / 2 - cx) ** 2 + ((d.crop[1] + d.crop[3]) / 2 - cy) ** 2, d.key)
                for d in p.details.values() if d.crop[0] <= cx <= d.crop[2] and d.crop[1] <= cy <= d.crop[3]]
        return min(hits)[1] if hits else None


def _shrink(img, long_side: int = LONG_SIDE):
    cv2 = _cv()
    s = long_side / max(img.shape[:2])
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img


def _decode(data: bytes):
    """Đọc ảnh. Ảnh điện thoại 12-48 MP rất lớn: đọc thẳng ở 1/4 hoặc 1/2 kích thước (JPEG làm được
    việc này rất nhanh), chỉ đọc đủ cỡ khi ảnh vốn đã nhỏ."""
    cv2 = _cv()
    import numpy as np
    buf = np.frombuffer(data, np.uint8)
    img = None
    for flag in (cv2.IMREAD_REDUCED_COLOR_4, cv2.IMREAD_REDUCED_COLOR_2, cv2.IMREAD_COLOR):
        try:
            img = cv2.imdecode(buf, flag)
        except cv2.error:
            img = None
        if img is not None and max(img.shape[:2]) >= LONG_SIDE:
            return img
    return img if img is not None and min(img.shape[:2]) >= 64 else None


def _sane(H, ref_shape, photo_shape) -> bool:
    """Ảnh 4 góc tranh gốc lên ảnh chụp phải là tứ giác lồi, kích thước hợp lý (chặn nhận nhầm)."""
    cv2 = _cv()
    import numpy as np
    try:
        Hi = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        return False
    h, w = ref_shape
    c = cv2.perspectiveTransform(np.float32([[[0, 0]], [[w, 0]], [[w, h]], [[0, h]]]), Hi).reshape(4, 2)
    if not np.all(np.isfinite(c)) or not cv2.isContourConvex(c.astype(np.float32)):
        return False
    area = cv2.contourArea(c.astype(np.float32))
    ph, pw = photo_shape
    return 0.02 * ph * pw <= area <= 40 * ph * pw


_shared: Recognizer | None = None


def recognizer() -> Recognizer:
    """Bộ nhận diện dùng chung cho cả máy chủ (điểm của tranh gốc chỉ tính một lần)."""
    global _shared
    if _shared is None:
        from .data import ALL_PAINTINGS
        here = os.path.dirname(os.path.abspath(__file__))
        _shared = Recognizer(ALL_PAINTINGS, os.path.join(os.path.dirname(here), "assets"), REFS_FILE)
    return _shared


REFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_refs.npz")

if __name__ == "__main__":
    # Tính sẵn điểm đặc trưng của các bức trong Kho tranh (chạy lại mỗi khi thêm/đổi ảnh tranh):
    #   python -m aura.vision
    from .data import ALL_PAINTINGS
    here = os.path.dirname(os.path.abspath(__file__))
    rec = Recognizer(ALL_PAINTINGS, os.path.join(os.path.dirname(here), "assets"))
    rec.save_file(REFS_FILE)
    print(f"Đã ghi {REFS_FILE} ({os.path.getsize(REFS_FILE) / 1024:.0f} KB) cho {len(ALL_PAINTINGS)} bức")
