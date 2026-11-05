"""Nội dung tĩnh của AURA: tranh, mốc thời gian, khái niệm, quiz.

Có thể thay bằng dữ liệu từ API/CSDL sau này. Giữ nguyên cấu trúc dataclass
để các màn hình không phải sửa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

NG = "National Gallery, London"


@dataclass
class Detail:
    key: str
    kicker: str
    title: str
    crop: tuple[float, float, float, float]   # vùng ảnh ở mức phóng 2×
    location: str                             # mô tả vị trí trong tranh
    note: str                                 # gợi ý quan sát


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
    source: str = f"Nguồn: {NG} — nationalgallery.org.uk ↗"


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
    museum: str = NG


HANDS_CROP = (0.39, 0.30, 0.99, 0.533)      # bàn tay + váy xanh (màn chào, chat)
DETAIL_HANDS = (0.30, 0.30, 0.96, 0.80)     # màn Chi tiết tranh
MIRROR_CROP = (0.34, 0.24, 0.64, 0.36)      # gương lồi (quiz)

ARNOLFINI = Painting(
    id="arnolfini",
    title="Chân dung vợ chồng Arnolfini",
    artist="Jan van Eyck", year="1434",
    image="images/arnolfini.jpg", aspect=586 / 800,
    tag="Nổi tiếng", filters=("Nổi tiếng",), read_time="3 phút",
    seeing=("Một đôi vợ chồng giàu có đang đứng trong phòng tiếp khách. Người đàn ông và "
            "người phụ nữ đang nắm tay nhau, cả hai đều có vẻ mặt nghiêm túc. Trong phòng có "
            "giường, gương lồi và nhiều đồ trang trí."),
    look_points=[
        LookPoint("Nhìn vào đôi tay", "Hai người đang nắm tay, nhưng tay của họ ở vị trí ra sao? "
                  "Bạn có thấy sự thoải mái hay trang trọng trong tư thế đó?"),
        LookPoint("Đọc từ gương", "Gương lồi phản chiếu những gì? Bạn có thấy ai khác trong phòng "
                  "không? Gương có thể đang nói gì về bối cảnh?"),
        LookPoint("Quan sát chiếc áo xanh", "Chiếc áo xanh đang được nâng lên. Bạn có nghĩ rằng đây "
                  "là một chi tiết ngẫu nhiên hay có ý nghĩa gì? Hãy tách riêng việc bạn thấy và "
                  "việc bạn suy đoán."),
    ],
    story=("Tác phẩm được vẽ bằng sơn dầu trên gỗ vào năm 1434. Bức tranh hiện được trưng bày "
           "tại National Gallery ở London và là một trong những tác phẩm nổi tiếng nhất của "
           "thời kỳ Phục hưng phương Bắc. Những chi tiết nhỏ trong phòng cho thấy chủ nhân "
           "rất giàu có và có gu thẩm mỹ tinh tế."),
    word=("Một từ mới: sơn dầu", "Là loại sơn được làm từ bột màu trộn với dầu. Sơn dầu rất "
          "bền và cho phép họa sĩ tạo ra nhiều lớp màu sâu, mịn. Tác phẩm này được vẽ bằng sơn "
          "dầu trên gỗ. [1]"),
    footnote=("[1] National Gallery, “The Arnolfini Portrait”.",
              "nationalgallery.org.uk/paintings/jan-van-eyck-the-arnolfini-portrait ↗"),
    url="https://www.nationalgallery.org.uk/paintings/jan-van-eyck-the-arnolfini-portrait",
    teaser="Hai bàn tay nắm lấy nhau giữa căn phòng: bạn sẽ nhìn thấy điều gì?",
    hotspots=[Hotspot(1, 0.517, 0.399, "hands"), Hotspot(2, 0.496, 0.298, "mirror"),
              Hotspot(3, 0.698, 0.521, "dress")],
    details={
        "hands": Detail("hands", "Nhìn kỹ một chút", "Bàn tay và những nếp vải", DETAIL_HANDS,
                        "Từ đôi tay ở giữa tranh đến bàn tay người phụ nữ đang gom những nếp váy xanh.",
                        "Hãy quan sát cử chỉ và nếp vải trước khi tìm một lời giải thích. Chi tiết "
                        "này chưa đủ để kết luận người phụ nữ mang thai."),
        "mirror": Detail("mirror", "Nhìn kỹ một chút", "Chiếc gương lồi", (0.30, 0.20, 0.68, 0.40),
                         "Chiếc gương treo trên bức tường phía sau, ngay giữa hai nhân vật.",
                         "Gương phản chiếu cả căn phòng và hai người đứng ở phía cửa. Bạn thấy "
                         "được bao nhiêu chi tiết trước khi đọc chú thích?"),
        "dress": Detail("dress", "Nhìn kỹ một chút", "Chiếc váy xanh", (0.45, 0.42, 1.0, 0.97),
                        "Phần váy xanh của người phụ nữ, từ thắt lưng xuống sàn nhà.",
                        "Hãy để ý độ dày của lớp vải và cách nó được gom lên. Đó là điều bạn thấy, "
                        "hay điều bạn đoán?"),
    },
    quiz=[
        QuizQuestion(
            "Chi tiết nào trong bức tranh gợi giả thuyết về sự hiện diện của chính họa sĩ Jan "
            "van Eyck tại căn phòng này?",
            ["Chiếc gương lồi phản chiếu bóng dáng họa sĩ ở hậu cảnh.",
             "Chữ ký được viết cách điệu trên khung cửa sổ.",
             "Đôi giày gỗ vứt ngổn ngang dưới sàn nhà."],
            0,
            ["Gương lồi ở trung tâm bức tranh phản chiếu toàn bộ căn phòng và hai nhân vật đứng "
             "từ phía cửa vào — một trong số đó có thể là Jan van Eyck. Đây là một giả thuyết được "
             "nhiều nhà nghiên cứu đề xuất, dù chưa được xác nhận tuyệt đối."],
            why_crop=MIRROR_CROP,
        ),
        QuizQuestion(
            "Theo một cách diễn giải trước đây, việc họa sĩ tự ký tên và vẽ bóng mình làm nhân "
            "chứng trên tường từng được liên hệ với ý nghĩa gì?",
            ["Chỉ là thói quen khoe kỹ thuật vẽ tranh chân thực.",
             "Biến bức tranh thành một \"hợp đồng hôn nhân\" hoặc giấy chứng nhận hợp pháp.",
             "Xác nhận đây là một bức chân dung tự họa."],
            1,
            ["Dòng chữ \"Johannes de Eyck fuit hic\" (Jan van Eyck ở đây) và bóng dáng trong gương "
             "từng được các nhà nghiên cứu liên hệ với vai trò nhân chứng — tương tự một giấy "
             "chứng nhận pháp lý. Tuy nhiên, National Gallery London hiện không còn coi đây là "
             "cảnh lễ hôn nhân; cách diễn giải này vẫn còn là chủ đề tranh luận học thuật."],
        ),
    ],
)

RED_TURBAN = Painting(
    id="red-turban",
    title="Người đàn ông đội khăn đỏ",
    artist="Jan van Eyck", year="1433",
    image="images/red_turban.jpg", aspect=800 / 1022,
    tag="Tự họa?", filters=("Nổi tiếng",), read_time="2 phút",
    seeing=("Một người đàn ông lớn tuổi nhìn thẳng ra ngoài, đầu quấn một chiếc khăn đỏ với rất "
            "nhiều nếp gấp. Nền tối khiến khuôn mặt và chiếc khăn nổi bật. Khung tranh có những "
            "dòng chữ được vẽ như khắc vào gỗ."),
    look_points=[
        LookPoint("Nhìn vào ánh mắt", "Ông đang nhìn về đâu? Bạn có cảm giác mình đang bị quan sát "
                  "không?"),
        LookPoint("Đếm nếp khăn", "Những nếp gấp đỏ được vẽ ra sao? Ánh sáng đến từ phía nào?"),
        LookPoint("Đọc chữ trên khung", "Dòng chữ trên khung có thể cho biết điều gì về người vẽ? "
                  "Hãy tách điều bạn đọc được và điều bạn đoán."),
    ],
    story=("Tranh được vẽ bằng sơn dầu trên gỗ năm 1433. Khung tranh ghi khẩu hiệu “Als ich can” "
           "(Hết khả năng của tôi) và ngày hoàn thành. Nhiều người cho rằng đây là tự họa của "
           "Jan van Eyck, vì người mẫu nhìn thẳng như đang soi gương — nhưng điều này chưa được "
           "xác nhận."),
    word=("Một từ mới: tự họa", "Là bức chân dung họa sĩ vẽ chính mình, thường nhờ một chiếc "
          "gương. Với bức tranh này, “tự họa” vẫn là một giả thuyết. [1]"),
    footnote=("[1] National Gallery, “Portrait of a Man (Self Portrait?)”.",
              "nationalgallery.org.uk ↗"),
    url="https://www.nationalgallery.org.uk/paintings/jan-van-eyck-portrait-of-a-man-self-portrait",
    teaser="Một ánh mắt nhìn thẳng về phía bạn: ai đang quan sát ai?",
    hotspots=[Hotspot(1, 0.50, 0.50, "face"), Hotspot(2, 0.55, 0.28, "turban")],
    details={
        "face": Detail("face", "Nhìn kỹ một chút", "Ánh mắt và nếp nhăn", (0.25, 0.32, 0.80, 0.72),
                       "Khuôn mặt ở giữa tranh, ngay dưới chiếc khăn đỏ.",
                       "Hãy nhìn đôi mắt và từng nếp nhăn trước khi đoán người này là ai."),
        "turban": Detail("turban", "Nhìn kỹ một chút", "Chiếc khăn đỏ", (0.15, 0.10, 0.90, 0.48),
                         "Phần khăn quấn trên đầu người đàn ông.",
                         "Những nếp gấp được tạo bằng nhiều lớp đỏ đậm nhạt khác nhau."),
    },
)

MADONNA = Painting(
    id="madonna-pinks",
    title="Đức Mẹ hoa cẩm chướng",
    artist="Raphael", year="khoảng 1506–1507",
    image="images/madonna_pinks.jpg", aspect=643 / 800,
    tag="Viên ngọc ẩn", filters=("Viên ngọc ẩn",), read_time="2 phút",
    seeing=("Một người mẹ trẻ ngồi trong phòng, bế đứa bé trên chiếc gối trắng. Hai người cùng "
            "cầm những bông hoa cẩm chướng nhỏ. Qua ô cửa sổ phía sau là bầu trời xanh và một "
            "tòa lâu đài."),
    look_points=[
        LookPoint("Nhìn vào bàn tay", "Bàn tay của mẹ và bé đang làm gì với bông hoa?"),
        LookPoint("Theo ánh mắt", "Mẹ nhìn ai, bé nhìn ai? Ánh mắt nối hai nhân vật như thế nào?"),
        LookPoint("Ô cửa sổ", "Phong cảnh ngoài cửa sổ thêm gì cho không gian căn phòng?"),
    ],
    story=("Đây là một bức tranh rất nhỏ, Raphael vẽ khi còn trẻ, khoảng năm 1506–1507. Hoa cẩm "
           "chướng thường được liên hệ với tình yêu và hôn nhân. Bức tranh hiện thuộc bộ sưu "
           "tập của National Gallery ở London."),
    word=("Một từ mới: biểu tượng", "Là một vật hay hình ảnh được dùng để gợi đến một ý nghĩa "
          "khác. Ý nghĩa đó có thể thay đổi theo thời đại và người xem. [1]"),
    footnote=("[1] National Gallery, “The Madonna of the Pinks”.", "nationalgallery.org.uk ↗"),
    url="https://www.nationalgallery.org.uk/paintings/raphael-the-madonna-of-the-pinks-la-madonna-dei-garofani",
    teaser="Một bông hoa nhỏ giữa hai bàn tay: bạn sẽ nhìn thấy điều gì?",
    hotspots=[Hotspot(1, 0.50, 0.45, "flowers")],
    details={
        "flowers": Detail("flowers", "Nhìn kỹ một chút", "Bông hoa giữa hai bàn tay",
                          (0.30, 0.28, 0.80, 0.62), "Ở giữa tranh, nơi tay mẹ và tay bé gặp nhau.",
                          "Hãy nhìn cử chỉ trước khi tìm ý nghĩa của bông hoa."),
    },
)

LEAL = Painting(
    id="leal-souvenir",
    title="Chân dung một người đàn ông",
    artist="Jan van Eyck", year="1432",
    image="images/leal_souvenir.jpg", aspect=800 / 1438,
    tag="Viên ngọc ẩn", filters=("Viên ngọc ẩn",), read_time="2 phút",
    seeing=("Một người đàn ông đội mũ xanh, mặc áo đỏ, cầm một cuộn giấy nhỏ. Ông đứng sau một "
            "bờ tường đá có khắc chữ. Ánh mắt ông nhìn sang một bên."),
    look_points=[
        LookPoint("Đọc bờ tường", "Bờ tường đá có những dòng chữ nào? Chúng được vẽ như khắc hay "
                  "như viết?"),
        LookPoint("Nhìn bàn tay", "Ông đang cầm gì? Vật đó có thể nói gì về người này?"),
        LookPoint("Tìm vết nứt", "Bạn có thấy những vết nứt, vết mòn trên đá không?"),
    ],
    story=("Tranh vẽ năm 1432. Trên bờ tường có dòng chữ “Leal Souvenir” (Kỷ niệm trung thành) "
           "và chữ ký ghi ngày của Jan van Eyck. Danh tính người mẫu vẫn chưa được biết chắc chắn."),
    word=("Một từ mới: trompe-l'œil", "Là kỹ thuật vẽ khiến vật thể trông như thật, đánh lừa "
          "mắt người xem — như dòng chữ tưởng được khắc vào đá. [1]"),
    footnote=("[1] National Gallery, “Portrait of a Man (Léal Souvenir)”.",
              "nationalgallery.org.uk ↗"),
    url="https://www.nationalgallery.org.uk/paintings/jan-van-eyck-portrait-of-a-man-leal-souvenir",
    teaser="Một dòng chữ khắc trên đá: lời nhắn gửi cho ai?",
    hotspots=[Hotspot(1, 0.50, 0.85, "parapet")],
    details={
        "parapet": Detail("parapet", "Nhìn kỹ một chút", "Dòng chữ trên bờ tường",
                          (0.05, 0.74, 0.95, 0.98), "Bờ tường đá ở phần dưới bức tranh.",
                          "Hãy đọc chậm từng chữ trước khi tìm hiểu ý nghĩa."),
    },
)

PAINTINGS: dict[str, Painting] = {p.id: p for p in (ARNOLFINI, RED_TURBAN, MADONNA, LEAL)}
FEATURED = [ARNOLFINI, RED_TURBAN, MADONNA, LEAL]
GRID = [ARNOLFINI, RED_TURBAN, MADONNA, LEAL]
FILTERS = ["Tất cả", "Nổi tiếng", "Viên ngọc ẩn"]
NEXT_STORY = {"arnolfini": "madonna-pinks", "madonna-pinks": "leal-souvenir",
              "leal-souvenir": "red-turban", "red-turban": "arnolfini"}

TIMELINE = [
    ("1400", "Đầu thế kỷ XV: Phục Hưng nở rộ ở Ý",
     "Nghệ sĩ quay lại cổ điển, đo đạc và quan sát tự nhiên."),
    ("1434", "Jan van Eyck vẽ Chân dung vợ chồng Arnolfini",
     "Một tác phẩm tiêu biểu cho cách nhìn chi tiết và không gian sâu."),
    ("1503", "Leonardo da Vinci bắt đầu vẽ Mona Lisa",
     "Ánh sáng, bóng và nụ cười tinh tế trở thành chuẩn mực."),
    ("1600", "Baroque kế thừa tinh thần quan sát",
     "Ánh sáng mạnh, bóng sâu và cảm xúc dồn dập tiếp tục phát triển."),
]

CONCEPTS = [
    ("Phối cảnh", "Không gian sâu được tạo bằng đường tụ và tỷ lệ giảm dần.",
     "Họa sĩ Phục Hưng dùng các đường thẳng hội tụ về một điểm và thu nhỏ dần vật ở xa, để mặt "
     "phẳng của bức tranh trông như một ô cửa nhìn vào không gian thật."),
    ("Ánh sáng", "Nguồn sáng tập trung tạo bóng, khối và cảm xúc mạnh hơn.",
     "Khi ánh sáng đến từ một hướng rõ ràng, bóng đổ giúp vật thể có khối, còn vùng sáng – tối "
     "dẫn mắt người xem đến điều quan trọng."),
    ("Sơn dầu", "Vật liệu cho phép chồng lớp, độ bóng và màu sắc phong phú hơn.",
     "Bột màu trộn với dầu khô chậm, cho phép họa sĩ phủ nhiều lớp mỏng trong suốt để tạo độ "
     "sâu, độ bóng và những chi tiết rất nhỏ."),
]

FACTS = [
    ("Phục Hưng bắt đầu ở đâu?", "Ở Ý, khi nghệ sĩ quay lại cổ điển và quan sát tự nhiên."),
    ("Phối cảnh làm gì?", "Tạo không gian sâu bằng đường tụ và tỷ lệ giảm dần."),
    ("Sơn dầu đến từ đâu?", "Họa sĩ vùng Flanders như van Eyck đã làm chủ kỹ thuật này rất sớm."),
]

FEELINGS = [("😶", "Chưa kết nối"), ("🙂", "Ít kết nối"), ("😊", "Có chút kết nối"),
            ("🥰", "Thấy đồng cảm"), ("😍", "Rất đồng cảm")]
