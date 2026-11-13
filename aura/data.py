"""Nội dung tĩnh của AURA: tranh, mốc thời gian, khái niệm, quiz.

Có thể thay bằng dữ liệu từ API/CSDL sau này. Giữ nguyên cấu trúc dataclass
để các màn hình không phải sửa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LOUVRE = "Bảo tàng Louvre, Paris"


@dataclass
class Detail:
    key: str
    kicker: str
    title: str
    crop: tuple[float, float, float, float]   # vùng ảnh ở mức phóng 2×
    location: str                             # mô tả vị trí trong tranh
    note: str                                 # gợi ý quan sát
    chat_crop: tuple[float, float, float, float] | None = None   # khung ngang khi đính kèm trong chat


@dataclass
class Hotspot:
    n: int
    x: float          # tâm điểm, tỉ lệ 0..1 theo ảnh
    y: float
    detail: str       # key của Detail khi chạm vào


@dataclass
class LookPoint:
    title: str
    text: str


@dataclass
class QuizQuestion:
    text: str
    options: list[str]
    correct: int
    why: list[str]
    why_crop: tuple[float, float, float, float] | None = None
    source: str = ""


@dataclass
class Painting:
    id: str
    title: str
    artist: str
    year: str
    image: str
    aspect: float                      # rộng / cao của ảnh
    tag: str                           # nhãn trên thẻ
    filters: tuple[str, ...]           # thuộc nhóm lọc nào
    read_time: str
    seeing: str
    look_points: list[LookPoint]
    story: str
    word: tuple[str, str]
    footnote: tuple[str, str]          # (trích dẫn, đường dẫn)
    url: str
    teaser: str
    hotspots: list[Hotspot] = field(default_factory=list)
    details: dict[str, Detail] = field(default_factory=dict)
    quiz: list[QuizQuestion] = field(default_factory=list)
    museum: str = ""
    # Nhánh trong kịch bản chatbot (Chatbot/scripts/*.json) -> key của Detail để đính kèm ảnh
    chat_branches: dict[str, str] = field(default_factory=dict)
    # Câu hỏi nhanh dưới ô chat (giọng người xem hỏi AURA), giúp người mới có chỗ bắt đầu.
    # Nên chọn câu mà kho tư liệu của tranh trả lời được.
    quick_prompts: list[str] = field(default_factory=list)


# Hội thoại của tranh này do kịch bản Chatbot/scripts/Mona_Lisa.json điều khiển.
MONA_LISA = Painting(
    id="mona-lisa",
    title="Mona Lisa",
    artist="Leonardo da Vinci", year="khoảng 1503–1519",
    image="images/mona_lisa.jpg", aspect=800 / 1192,
    tag="Nổi tiếng", filters=("Nổi tiếng",), read_time="3 phút",
    seeing=("Một người phụ nữ ngồi xoay người nhẹ về phía người xem, hai tay đặt chồng lên nhau. "
            "Khóe miệng cô hơi nhếch lên như đang mỉm cười. Phía sau là một phong cảnh có núi, "
            "sông và con đường uốn lượn, càng xa càng mờ dần."),
    look_points=[
        LookPoint("Nhìn vào gương mặt", "Đôi mắt và khóe miệng gợi cho bạn cảm giác gì? Cảm giác "
                  "đó có thay đổi khi bạn nhìn lâu hơn không?"),
        LookPoint("Quan sát đôi tay", "Hai bàn tay đang đặt thế nào? Tư thế ấy cho thấy sự thoải "
                  "mái hay trang trọng?"),
        LookPoint("Phong cảnh phía sau", "Hai bên phong cảnh có ở cùng một độ cao không? Hãy tách "
                  "điều bạn thấy và điều bạn đoán."),
    ],
    story=("Leonardo da Vinci bắt đầu vẽ bức tranh khoảng năm 1503 và tiếp tục hoàn thiện trong "
           "nhiều năm. Người phụ nữ thường được xác định là Lisa Gherardini, vợ của thương nhân "
           "Francesco del Giocondo ở Florence. Tranh hiện được lưu giữ tại Bảo tàng Louvre; vụ "
           "đánh cắp năm 1911 càng khiến tác phẩm được chú ý rộng rãi."),
    word=("Một từ mới: sfumato", "Là kỹ thuật tạo chuyển tiếp mềm giữa các vùng sáng, tối và "
          "đường nét, tránh ranh giới quá sắc nét — như ở khóe miệng và đôi mắt. [1]"),
    footnote=("[1] Musée du Louvre, “Portrait de Lisa Gherardini, dit La Joconde ou Monna Lisa”.",
              "collections.louvre.fr ↗"),
    url="https://collections.louvre.fr/en/ark:/53355/cl010062370",
    teaser="Một nụ cười khó nắm bắt: bạn sẽ nhìn thấy điều gì?",
    hotspots=[Hotspot(1, 0.47, 0.26, "face"), Hotspot(2, 0.45, 0.81, "hands"),
              Hotspot(3, 0.13, 0.30, "landscape")],
    details={
        "face": Detail("face", "Nhìn kỹ một chút", "Gương mặt và nụ cười", (0.28, 0.14, 0.66, 0.40),
                       "Gương mặt ở phần trên bức tranh, hơi xoay về phía người xem.",
                       "Hãy nhìn khóe miệng và đuôi mắt: ranh giới sáng tối mềm đến mức nào?",
                       chat_crop=(0.24, 0.20, 0.70, 0.36)),
        "hands": Detail("hands", "Nhìn kỹ một chút", "Đôi bàn tay", (0.22, 0.70, 0.62, 0.97),
                        "Hai bàn tay đặt chồng lên nhau trên tay ghế, ở phần dưới bức tranh.",
                        "Bàn tay nào đặt trên? Các ngón tay đang thả lỏng hay giữ chặt?",
                        chat_crop=(0.18, 0.73, 0.66, 0.89)),
        "dress": Detail("dress", "Nhìn kỹ một chút", "Trang phục", (0.30, 0.48, 0.66, 0.72),
                        "Phần cổ áo và lớp vải trên vai, ngay dưới gương mặt.",
                        "Hãy để ý đường thêu ở cổ áo và lớp voan mỏng phủ trên tóc.",
                        chat_crop=(0.26, 0.48, 0.70, 0.63)),
        "landscape": Detail("landscape", "Nhìn kỹ một chút", "Phong cảnh phía sau",
                            (0.0, 0.17, 0.36, 0.42),
                            "Phong cảnh bên trái gương mặt: núi, nước và con đường uốn lượn.",
                            "Vật ở xa trông mờ và xanh hơn: điều đó tạo cảm giác sâu ra sao?",
                            chat_crop=(0.0, 0.20, 0.42, 0.33)),
    },
    museum=LOUVRE,
    chat_branches={"BRANCH_2A": "face", "BRANCH_2B": "hands", "BRANCH_2C": "dress",
                   "BRANCH_2D": "landscape", "BRANCH_3C": "landscape"},
    # mỗi câu khớp một thẻ trong kho tư liệu của kịch bản (C1, C2, C8, C4, C5, C9, C7)
    quick_prompts=["Người phụ nữ trong tranh là ai?",
                   "Bức tranh được vẽ khi nào?",
                   "Vì sao bức tranh này nổi tiếng?",
                   "Sfumato là kỹ thuật gì?",
                   "Màu sắc trong tranh có ý nghĩa gì?",
                   "Phong cảnh phía sau có gì đặc biệt?",
                   "Leonardo da Vinci là người thế nào?",
                   "Trang phục nói gì về địa vị của bà?"],
)

# Thêm tranh: khai báo một Painting như MONA_LISA rồi đưa vào các danh sách dưới đây.
PAINTINGS: dict[str, Painting] = {p.id: p for p in (MONA_LISA,)}
DEFAULT_ID = MONA_LISA.id               # tranh mặc định khi đường dẫn không hợp lệ
FEATURED = [MONA_LISA]
GRID = [MONA_LISA]
FILTERS = ["Tất cả", "Nổi tiếng"]
NEXT_STORY: dict[str, str] = {}         # id tranh -> id tranh gợi ý tiếp theo (màn Kết quả)

# Nội dung trang Khám phá (thời Phục Hưng) nằm trong aura/topics.py

FEELINGS = [("😶", "Chưa kết nối"), ("🙂", "Ít kết nối"), ("😊", "Có chút kết nối"),
            ("🥰", "Thấy đồng cảm"), ("😍", "Rất đồng cảm")]
