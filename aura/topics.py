"""Nội dung trang Khám phá: thời Phục Hưng — các chặng, dòng thời gian, khái niệm, “Bạn có biết?”.

Mỗi mục là một `Topic`, bấm vào sẽ mở trang chi tiết (/topic/<id>) với ảnh minh hoạ,
bài viết dài hơn và một gợi ý “Nhìn kỹ” theo tinh thần của AURA.

Tham khảo: Encyclopaedia Britannica, “Renaissance” và các bài liên quan; chỉ dùng những
thông tin đã được ghi nhận rộng rãi. Ảnh minh hoạ: tranh thuộc phạm vi công cộng (public
domain / CC0) lấy từ Wikimedia Commons, đã thu nhỏ, nằm trong assets/images/home/.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .data import MONA_LISA

REFERENCE = ("Tham khảo: Encyclopaedia Britannica, “Renaissance”",
             "https://www.britannica.com/event/Renaissance")


@dataclass
class Topic:
    id: str
    kind: str                     # period | event | concept
    label: str                    # năm / thời gian / nhóm (hiện như nhãn nhỏ)
    title: str
    short: str                    # một câu tóm tắt (thẻ trên trang chủ)
    body: list[str]               # các đoạn của trang chi tiết
    look: str = ""                # gợi ý "Nhìn kỹ" (quan sát chính bức ảnh minh hoạ)
    image: str = ""               # đường dẫn trong assets, "" = không có ảnh
    aspect: float = 1.0           # rộng / cao của ảnh
    caption: str = ""             # chú thích ảnh: tác giả, tên, năm, nơi lưu giữ
    crop: tuple[float, float, float, float] = (0, 0, 1, 1)   # vùng ảnh dùng cho thẻ nhỏ
    link: tuple[str, str] | None = None                      # (chữ trên nút, route) nếu có


def _img(name: str) -> str:
    return f"images/home/{name}.jpg"


# Tỉ lệ khung ảnh (rộng/cao) sau khi thu nhỏ — xem get_images.py khi thay ảnh
ASPECT = {
    "duomo": 1.276, "trinity": 0.620, "ghent": 1.368, "cosimo": 0.742, "gutenberg": 0.717,
    "venus": 1.592, "creation": 2.203, "athens": 1.289, "sack": 1.912, "copernicus": 0.619,
    "matthew": 1.059, "vitruvian": 0.735, "keys": 1.613, "rocks": 0.631, "rolin": 0.935,
    "gozzoli": 1.287, "durer": 0.723,
}


def _pic(name: str) -> dict:
    return {"image": _img(name), "aspect": ASPECT[name]}


INTRO = (
    "Phục Hưng là gì?",
    "Phục Hưng là thời kỳ của văn minh châu Âu nối tiếp ngay sau thời Trung Cổ, kéo dài khoảng "
    "từ thế kỷ XIV đến thế kỷ XVI. Đặc trưng nổi bật của nó là sự quan tâm trở lại với tri thức "
    "và giá trị của thời cổ điển Hy Lạp – La Mã.",
    "Từ “Renaissance” trong tiếng Pháp nghĩa là “tái sinh”: người đương thời cảm thấy mình đang "
    "làm sống lại văn hoá Hy Lạp – La Mã sau nhiều thế kỷ bị lãng quên. Năm 1550, Giorgio Vasari "
    "đã dùng từ “rinascita” (sự tái sinh) khi viết về các nghệ sĩ Ý; đến năm 1860, cuốn sách của "
    "nhà sử học Jacob Burckhardt về văn hoá Phục Hưng ở Ý khiến khái niệm này trở nên phổ biến.\n\n"
    "Phong trào bắt đầu ở các thành bang miền bắc nước Ý, đặc biệt là Florence, nơi giàu lên nhờ "
    "thương mại và ngân hàng. Nền tảng tư tưởng của nó là chủ nghĩa nhân văn: đọc lại các tác giả "
    "cổ đại, đề cao năng lực và phẩm giá của con người.\n\n"
    "Phục Hưng không chỉ là nghệ thuật. Đây còn là thời của những chuyến thám hiểm tới các lục địa "
    "mới, của thuyết Copernicus thay cho mô hình Ptolemy trong thiên văn học, của sự suy yếu chế "
    "độ phong kiến và sự lớn mạnh của thương mại, cùng việc ứng dụng những phát minh như giấy, "
    "máy in, la bàn và thuốc súng.",
)

# ---------------------------------------------------------------------------- 3 chặng
PERIODS = [
    Topic(
        "p-early", "period", "Thế kỷ XV", "Phục Hưng sơ kỳ",
        "Florence tìm lại phối cảnh, hình khối và con người tự nhiên.",
        [
            "Phục Hưng sơ kỳ gắn với Florence trong những năm 1400. Thành phố giàu lên nhờ ngân hàng "
            "và buôn bán len, lụa; các phường hội và những gia tộc như Medici sẵn lòng chi tiền cho "
            "nhà thờ, tượng và tranh.",
            "Ba gương mặt thường được nhắc đến là kiến trúc sư Filippo Brunelleschi, nhà điêu khắc "
            "Donatello và họa sĩ Masaccio. Brunelleschi tìm lại phép phối cảnh tuyến tính; Donatello "
            "đưa tượng trở lại dáng người tự nhiên, có trọng lượng; Masaccio vẽ những nhân vật có "
            "khối, đứng vững trong một không gian có chiều sâu.",
            "Cùng lúc ở vùng Flanders (nay thuộc Bỉ), Jan van Eyck và các họa sĩ phương Bắc đưa sơn "
            "dầu đến độ tinh xảo chưa từng có. Hai dòng chảy ấy về sau gặp nhau và nuôi dưỡng lẫn nhau.",
        ],
        look="Ở bức Chúa Ba Ngôi của Masaccio, hãy lần theo các gờ trên trần vòm: chúng cùng hội tụ "
             "về một điểm thấp, gần ngang tầm mắt người đứng xem trong nhà thờ.",
        caption="Masaccio, Chúa Ba Ngôi, khoảng 1425–1428, nhà thờ Santa Maria Novella, Florence.",
        crop=(0.05, 0.08, 0.95, 0.55), **_pic("trinity")),
    Topic(
        "p-high", "period", "Khoảng 1490–1527", "Phục Hưng đỉnh cao",
        "Leonardo, Michelangelo, Raphael: hài hòa và chín muồi nhất.",
        [
            "Phục Hưng đỉnh cao là một quãng ngắn, chừng ba mươi năm, khi hội họa Ý đạt tới sự cân bằng "
            "giữa quan sát tự nhiên, bố cục hài hòa và lý tưởng về vẻ đẹp con người.",
            "Leonardo da Vinci đưa vào hội họa sfumato cùng những nghiên cứu về ánh sáng và giải phẫu; "
            "Michelangelo vẽ trần Nhà nguyện Sistine và tạc những pho tượng đầy sức mạnh; Raphael đem "
            "lại vẻ trong trẻo, cân đối, tiêu biểu là bức Trường học Athens.",
            "Trung tâm nghệ thuật dần chuyển từ Florence về Rome, nơi các giáo hoàng như Julius II đặt "
            "hàng những công trình lớn ở Vatican. Ở Venice, Giorgione và Titian phát triển một lối vẽ "
            "giàu màu sắc của riêng mình.",
            "Năm 1527, quân đội của Hoàng đế Charles V cướp phá Rome; nhiều nhà sử học xem đó là dấu "
            "mốc khép lại giai đoạn này.",
        ],
        look="Trong Trường học Athens, các triết gia đứng dưới những mái vòm nối tiếp nhau; hãy để ý "
             "hai nhân vật ở chính giữa, nơi mọi đường phối cảnh cùng hướng về.",
        caption="Raphael, Trường học Athens, 1509–1511, Cung điện Tông tòa, Vatican.",
        crop=(0.2, 0.2, 0.8, 0.75), **_pic("athens")),
    Topic(
        "p-late", "period", "Thế kỷ XVI", "Lan tỏa và hậu kỳ",
        "Tinh thần Phục Hưng sang phương Bắc; Mannerism ở Ý.",
        [
            "Nhờ máy in, những chuyến đi và các nhà bảo trợ, tư tưởng và phong cách Phục Hưng lan "
            "sang Pháp, Đức, vùng Flanders, Anh và xa hơn nữa trong thế kỷ XVI.",
            "Albrecht Dürer ở Nuremberg từng sang Ý, kết hợp óc quan sát tỉ mỉ của phương Bắc với lý "
            "thuyết tỉ lệ và phối cảnh của Ý. Tranh khắc gỗ, khắc đồng của ông được in ra và đi khắp "
            "châu Âu.",
            "Ở Ý sau những năm 1520, nhiều họa sĩ chủ ý kéo dài hình thể, dùng màu lạ và bố cục căng "
            "thẳng; phong cách này về sau được gọi là Mannerism. Đến cuối thế kỷ XVI, nghệ thuật dần "
            "chuyển sang Baroque.",
        ],
        look="Trong bức tự họa năm 1500, Dürer nhìn thẳng ra người xem với tư thế đối xứng hiếm thấy "
             "ở chân dung thời đó: hãy để ý từng lọn tóc và lớp lông viền áo được vẽ rất tỉ mỉ.",
        caption="Albrecht Dürer, Tự họa, 1500, Alte Pinakothek, Munich.",
        crop=(0.1, 0.05, 0.9, 0.5), **_pic("durer")),
]

# ---------------------------------------------------------------------------- dòng thời gian
TIMELINE = [
    Topic(
        "t-1341", "event", "1341", "Petrarch được trao vòng nguyệt quế ở Rome",
        "Nhà thơ được xem là người đặt nền cho chủ nghĩa nhân văn.",
        [
            "Năm 1341, nhà thơ Francesco Petrarca (Petrarch) được trao vòng nguyệt quế thi sĩ trên "
            "đồi Capitol ở Rome, một nghi lễ mô phỏng thời cổ đại.",
            "Petrarch say mê sưu tầm và đọc lại bản thảo của Cicero, Virgil cùng nhiều tác giả La Mã. "
            "Ông coi những thế kỷ trước đó là một thời “tăm tối” và mơ làm sống lại vẻ rực rỡ của văn "
            "hóa cổ điển.",
            "Vì vậy ông thường được gọi là “cha đẻ của chủ nghĩa nhân văn”, phong trào tư tưởng làm "
            "nền cho cả thời Phục Hưng.",
        ]),
    Topic(
        "t-1420", "event", "1420", "Brunelleschi khởi công mái vòm nhà thờ Florence",
        "Một khoảng trống hơn 40 mét được phủ kín mà không cần giàn đỡ khổng lồ.",
        [
            "Năm 1420, Filippo Brunelleschi bắt đầu xây mái vòm cho nhà thờ chính tòa Florence "
            "(Santa Maria del Fiore), che một khoảng trống rộng hơn 40 mét mà trước đó chưa ai biết "
            "cách phủ kín.",
            "Ông dùng hai lớp vỏ lồng vào nhau và xếp gạch theo kiểu xương cá để mái vòm tự đỡ trong "
            "lúc xây. Phần chính hoàn thành năm 1436, và đến nay đây vẫn là mái vòm gạch lớn nhất "
            "thế giới.",
            "Brunelleschi cũng được ghi nhận là người tìm lại các nguyên tắc của phối cảnh tuyến tính, "
            "thay đổi hẳn cách các họa sĩ dựng không gian trong tranh.",
        ],
        look="Trong tranh của Domenico di Michelino, mái vòm đỏ của Brunelleschi hiện lên giữa thành "
             "Florence ở bên phải, cạnh nhà thơ Dante.",
        caption="Domenico di Michelino, Dante và Thần khúc, 1465, Nhà thờ chính tòa Florence.",
        crop=(0.55, 0.3, 1.0, 0.8), **_pic("duomo")),
    Topic(
        "t-1427", "event", "Khoảng 1427", "Masaccio vẽ Chúa Ba Ngôi bằng phối cảnh",
        "Bức tường nhà thờ như được khoét mở thành một nhà nguyện.",
        [
            "Khoảng năm 1425–1428, Masaccio vẽ bức bích họa Chúa Ba Ngôi trên tường nhà thờ Santa "
            "Maria Novella ở Florence. Đây được coi là một trong những bức tranh đầu tiên dùng phối "
            "cảnh tuyến tính một cách chặt chẽ.",
            "Trần vòm được vẽ thụt sâu vào bức tường như một nhà nguyện thật; người đương thời đứng "
            "trước tranh có cảm giác bức tường bị khoét mở.",
            "Masaccio mất khi mới khoảng 26 tuổi, nhưng cách ông vẽ những nhân vật có khối, có trọng "
            "lượng đã ảnh hưởng đến nhiều thế hệ họa sĩ sau.",
        ],
        look="Hai người đặt vẽ quỳ ở hai bên, bên ngoài khung kiến trúc: họ như đứng cùng không gian "
             "với chính người xem.",
        caption="Masaccio, Chúa Ba Ngôi, khoảng 1425–1428, nhà thờ Santa Maria Novella, Florence.",
        crop=(0.05, 0.08, 0.95, 0.55), **_pic("trinity")),
    Topic(
        "t-1432", "event", "1432", "Bàn thờ Ghent được hoàn thành",
        "Đỉnh cao của sơn dầu và óc quan sát ở phương Bắc.",
        [
            "Năm 1432, Bàn thờ Ghent được hoàn thành và đặt tại nhà thờ thánh Bavo ở thành phố Ghent. "
            "Công trình được cho là do hai anh em Hubert và Jan van Eyck thực hiện.",
            "Bằng sơn dầu, Jan van Eyck vẽ được ánh lấp lánh trên đá quý, từng ngọn cỏ, từng sợi lông "
            "của con cừu ở giữa tranh. Độ chi tiết ấy khiến các họa sĩ khắp châu Âu kinh ngạc.",
            "Đây là một trong những tác phẩm quan trọng nhất của Phục Hưng phương Bắc, cho thấy tinh "
            "thần quan sát thế giới không chỉ có ở Ý.",
        ],
        look="Ở tầng dưới, những đoàn người từ bốn phía cùng tiến về chú cừu trên bàn thờ ở giữa; ở "
             "hai cánh ngoài cùng tầng trên là Adam và Eva, được vẽ gần như kích thước người thật.",
        caption="Hubert và Jan van Eyck, Bàn thờ Ghent (khi mở), hoàn thành 1432, nhà thờ thánh Bavo, Ghent.",
        crop=(0.25, 0.45, 0.75, 1.0), **_pic("ghent")),
    Topic(
        "t-1434", "event", "1434", "Cosimo de’ Medici trở về Florence",
        "Gia tộc ngân hàng bắt đầu chi phối thành phố và bảo trợ nghệ thuật.",
        [
            "Năm 1434, chủ ngân hàng Cosimo de’ Medici trở về Florence sau một năm bị lưu đày. Từ đó "
            "gia tộc Medici chi phối chính trường thành phố suốt nhiều thế hệ, dù vẫn giữ hình thức "
            "của một nước cộng hòa.",
            "Cosimo bảo trợ các nghệ sĩ như Brunelleschi và Donatello, lập thư viện và nuôi dưỡng việc "
            "nghiên cứu triết học Plato. Cháu nội ông, Lorenzo “the Magnificent”, tiếp tục truyền thống "
            "ấy.",
            "Sau khi ông mất, người Florence tôn vinh Cosimo là “Pater Patriae”, người cha của tổ quốc.",
        ],
        look="Bức chân dung này được Pontormo vẽ gần một thế kỷ sau khi Cosimo mất: hãy để ý chiếc áo "
             "choàng đỏ và cành nguyệt quế bên cạnh, những biểu tượng tôn vinh gia tộc Medici.",
        caption="Pontormo, Chân dung Cosimo de’ Medici, 1519–1520, Uffizi, Florence.",
        crop=(0.15, 0.05, 0.95, 0.55), **_pic("cosimo")),
    Topic(
        "t-1455", "event", "Khoảng 1455", "Kinh Thánh Gutenberg ra đời",
        "Máy in chữ rời giúp sách và tư tưởng lan khắp châu Âu.",
        [
            "Khoảng giữa thế kỷ XV, Johannes Gutenberg ở Mainz (Đức) phát triển máy in dùng chữ rời "
            "bằng kim loại. Bộ Kinh Thánh Gutenberg, hoàn thành khoảng năm 1455, là cuốn sách lớn đầu "
            "tiên được in theo cách này ở châu Âu.",
            "Trước đó, mỗi cuốn sách phải chép tay mất hàng tháng. Với máy in, sách trở nên nhiều và rẻ "
            "hơn; đến năm 1500 đã có xưởng in ở hàng trăm thành phố châu Âu.",
            "Nhờ vậy, văn bản cổ điển, sách của các nhà nhân văn và cả tranh in lan đi rất nhanh, giúp "
            "Phục Hưng vượt ra khỏi nước Ý.",
        ],
        look="Phần chữ được in, còn những đường hoa lá và chữ cái lớn đầu trang lại được tô vẽ bằng "
             "tay sau đó, nên mỗi bản Kinh Thánh Gutenberg có trang trí khác nhau.",
        caption="Một trang Kinh Thánh Gutenberg, khoảng 1455, Thư viện Quốc hội Hoa Kỳ.",
        crop=(0.0, 0.0, 1.0, 0.5), **_pic("gutenberg")),
    Topic(
        "t-1485", "event", "Khoảng 1485", "Botticelli vẽ Sự ra đời của thần Vệ Nữ",
        "Thần thoại cổ đại trở thành đề tài của một bức tranh lớn.",
        [
            "Khoảng năm 1485, Sandro Botticelli vẽ Sự ra đời của thần Vệ Nữ: nữ thần tình yêu La Mã "
            "cổ đại đứng trên vỏ sò, được gió thổi vào bờ.",
            "Chọn một đề tài thần thoại cho một bức tranh khổ lớn như vậy là điều hiếm thấy trước đó. "
            "Nó cho thấy giới thượng lưu Florence, gần gũi với nhà Medici, say mê văn hóa và triết học "
            "cổ đại đến mức nào.",
            "Botticelli không chạy theo giải phẫu chính xác; ông chuộng những đường nét uyển chuyển, "
            "mái tóc bay và nhịp điệu gần như trang trí.",
        ],
        look="Hãy để ý cổ và bờ vai trái của nữ thần: chúng dài và dốc hơn ngoài đời, nhưng chính sự "
             "“sai” ấy tạo nên dáng đứng mềm mại như đang lướt đi.",
        caption="Sandro Botticelli, Sự ra đời của thần Vệ Nữ, khoảng 1485, Uffizi, Florence.",
        crop=(0.3, 0.0, 0.7, 0.6), **_pic("venus")),
    Topic(
        "t-1503", "event", "1503", "Leonardo bắt đầu vẽ Mona Lisa",
        "Sfumato tạo nên gương mặt và nụ cười mềm mại, khó nắm bắt.",
        [
            "Khoảng năm 1503, ở Florence, Leonardo da Vinci bắt đầu vẽ chân dung Lisa Gherardini, vợ "
            "của thương nhân Francesco del Giocondo. Ông giữ bức tranh bên mình và tiếp tục chỉnh sửa "
            "trong nhiều năm.",
            "Bằng sfumato, những lớp màu thật mỏng chồng lên nhau, Leonardo làm đường nét gương mặt tan "
            "vào bóng tối, khiến nụ cười như thay đổi theo cách ta nhìn. Phong cảnh phía sau dùng phối "
            "cảnh khí quyển: càng xa càng mờ và ngả xanh.",
            "Bố cục bán thân xoay ba phần tư, có cả đôi tay, về sau trở thành hình mẫu cho chân dung "
            "châu Âu. Ngày nay bức tranh nằm ở Bảo tàng Louvre, Paris.",
        ],
        look="Nhìn vào đôi mắt rồi chuyển sang khóe miệng: nhiều người thấy nụ cười rõ hơn khi họ "
             "không nhìn thẳng vào nó.",
        image=MONA_LISA.image, aspect=MONA_LISA.aspect,
        caption="Leonardo da Vinci, Mona Lisa, khoảng 1503–1519, Bảo tàng Louvre, Paris.",
        crop=(0.0, 0.1, 1.0, 0.55), link=("Trò chuyện cùng AURA về bức tranh này", f"/painting/{MONA_LISA.id}")),
    Topic(
        "t-1508", "event", "1508", "Michelangelo bắt đầu vẽ trần Nhà nguyện Sistine",
        "Bốn năm, hàng trăm nhân vật, kể lại sách Sáng Thế.",
        [
            "Năm 1508, Giáo hoàng Julius II giao cho Michelangelo vẽ trần Nhà nguyện Sistine ở Vatican, "
            "dù ông vốn tự coi mình là nhà điêu khắc hơn là họa sĩ.",
            "Trong bốn năm, đến 1512, ông phủ kín trần nhà rộng khoảng 500 mét vuông bằng hàng trăm "
            "nhân vật, kể các tích trong sách Sáng Thế, từ lúc tạo dựng thế giới đến trận Đại Hồng Thủy.",
            "Những thân hình cơ bắp, đầy chuyển động của Michelangelo cho thấy hiểu biết sâu về giải "
            "phẫu người, một đặc trưng của Phục Hưng đỉnh cao.",
        ],
        look="Trong cảnh Tạo dựng Adam, ngón tay của Chúa và của Adam gần chạm mà không chạm: khoảng "
             "trống nhỏ ấy là tâm điểm của cả bức tranh.",
        caption="Michelangelo, Tạo dựng Adam (chi tiết trần Nhà nguyện Sistine), khoảng 1508–1512, Vatican.",
        crop=(0.25, 0.0, 0.75, 1.0), **_pic("creation")),
    Topic(
        "t-1509", "event", "1509", "Raphael vẽ Trường học Athens",
        "Các triết gia Hy Lạp hội tụ dưới một mái vòm lộng lẫy.",
        [
            "Năm 1509, Raphael, khi ấy khoảng 26 tuổi, bắt đầu vẽ bích họa trong những căn phòng của "
            "Giáo hoàng ở Vatican. Nổi tiếng nhất là Trường học Athens (1509–1511).",
            "Bức tranh tập hợp các nhà tư tưởng Hy Lạp cổ đại dưới một công trình kiến trúc đồ sộ. Ở "
            "chính giữa, Plato chỉ tay lên trời còn Aristotle hướng bàn tay xuống mặt đất, gợi hai cách "
            "tìm kiếm chân lý khác nhau.",
            "Người ta cho rằng Raphael đã mượn gương mặt của các nghệ sĩ cùng thời cho một số nhân vật, "
            "và tự vẽ mình đứng ở rìa phải bức tranh.",
        ],
        look="Mọi đường gạch lát nền và gờ vòm đều dẫn mắt về khoảng giữa Plato và Aristotle, một ví "
             "dụ mẫu mực của phối cảnh tuyến tính.",
        caption="Raphael, Trường học Athens, 1509–1511, Cung điện Tông tòa, Vatican.",
        crop=(0.2, 0.2, 0.8, 0.75), **_pic("athens")),
    Topic(
        "t-1527", "event", "1527", "Rome bị cướp phá",
        "Biến cố thường được xem là dấu mốc khép lại Phục Hưng đỉnh cao.",
        [
            "Tháng 5 năm 1527, binh lính của Hoàng đế Charles V, nhiều người đã lâu không được trả "
            "lương, tràn vào cướp phá Rome. Giáo hoàng Clement VII phải chạy vào lâu đài Sant’Angelo "
            "để trú ẩn.",
            "Thành phố bị tàn phá nặng nề và nhiều nghệ sĩ bỏ đi nơi khác. Biến cố này thường được xem "
            "là dấu mốc khép lại thời Phục Hưng đỉnh cao ở Rome.",
            "Sau đó, nghệ thuật Ý chuyển sang những tìm tòi mới, căng thẳng hơn, mà ngày nay gọi là "
            "Mannerism.",
        ],
        caption="Johannes Lingelbach, Cuộc cướp phá Rome năm 1527, thế kỷ XVII.",
        crop=(0.25, 0.1, 0.75, 0.9), **_pic("sack")),
    Topic(
        "t-1543", "event", "1543", "Copernicus công bố thuyết nhật tâm",
        "Trái Đất không còn là trung tâm của vũ trụ.",
        [
            "Năm 1543, Nicolaus Copernicus công bố cuốn Về chuyển động quay của các thiên cầu, đưa ra "
            "mô hình Mặt Trời ở trung tâm và Trái Đất quay quanh nó.",
            "Mô hình này thách thức quan niệm Trái Đất là trung tâm vũ trụ của Ptolemy, vốn được chấp "
            "nhận hơn một nghìn năm. Phải mất nhiều thập kỷ, cùng với Kepler và Galileo, nó mới được "
            "thừa nhận rộng rãi.",
            "Cũng năm 1543, Andreas Vesalius xuất bản bộ sách giải phẫu người nổi tiếng của mình. Tinh "
            "thần quan sát và đặt câu hỏi của Phục Hưng đã lan sang khoa học.",
        ],
        look="Trong sơ đồ của Copernicus, Mặt Trời (Sol) nằm ở tâm các vòng tròn, còn Trái Đất chỉ là "
             "một vòng trong số đó, đi cùng Mặt Trăng.",
        caption="Sơ đồ hệ nhật tâm trong sách của Copernicus, 1543.",
        crop=(0.05, 0.0, 0.95, 0.55), **_pic("copernicus")),
    Topic(
        "t-1600", "event", "1600", "Caravaggio mở đường cho Baroque",
        "Ánh sáng gắt, bóng sâu và cảm xúc dồn dập.",
        [
            "Khoảng năm 1599–1600, Caravaggio hoàn thành bức Lời gọi của thánh Matthew cho một nhà "
            "nguyện ở Rome. Một luồng sáng xiên cắt qua bóng tối, rọi lên những gương mặt rất đời thường.",
            "Lối dùng tương phản sáng tối gay gắt ấy, về sau gọi là tenebrism, cùng sự kịch tính và "
            "cảm xúc dồn dập, báo hiệu thời Baroque đang tới.",
            "Tinh thần quan sát thế giới thật mà Phục Hưng khơi dậy vẫn tiếp tục, nhưng nghệ thuật giờ "
            "muốn lay động người xem mạnh mẽ hơn.",
        ],
        look="Lần theo vệt sáng từ phía trên bên phải: nó chạy gần song song với cánh tay Chúa Kitô "
             "đang chỉ về phía Matthew.",
        caption="Caravaggio, Lời gọi của thánh Matthew, 1599–1600, nhà thờ San Luigi dei Francesi, Rome.",
        crop=(0.0, 0.2, 1.0, 0.8), **_pic("matthew")),
]
# Bốn mốc hiện trên trang chủ (trải đều 1300–1600); xem đủ ở /timeline
TIMELINE_HIGHLIGHTS = ["t-1341", "t-1455", "t-1503", "t-1600"]

# ---------------------------------------------------------------------------- khái niệm
CONCEPTS = [
    Topic(
        "c-humanism", "concept", "Tư tưởng", "Chủ nghĩa nhân văn",
        "Học lại từ người xưa, đặt con người vào trung tâm.",
        [
            "Chủ nghĩa nhân văn là phong trào tư tưởng nền tảng của Phục Hưng, hình thành ở miền bắc "
            "nước Ý trong thế kỷ XIII–XIV và có trung tâm ở Florence. Petrarch được xem là người đặt "
            "nền móng: ông đề cao việc đọc các tác giả cổ điển hơn là các nhà triết học kinh viện thời "
            "Trung Cổ.",
            "Các nhà nhân văn học ngữ pháp, tu từ, thơ ca, lịch sử và triết học đạo đức, những môn được "
            "gọi chung là studia humanitatis, với niềm tin rằng con người có thể tự hoàn thiện qua học vấn.",
            "Tinh thần đó thấm vào nghệ thuật: con người, cơ thể và thế giới tự nhiên trở thành đề tài "
            "được quan sát kỹ lưỡng và trân trọng.",
        ],
        look="Trong Trường học Athens, Raphael đặt các triết gia cổ đại giữa một tòa nhà lộng lẫy như "
             "thánh đường: tri thức của con người được tôn vinh trang trọng như điều thiêng liêng.",
        caption="Raphael, Trường học Athens, 1509–1511, Vatican.",
        crop=(0.2, 0.2, 0.8, 0.75), **_pic("athens")),
    Topic(
        "c-perspective", "concept", "Kỹ thuật", "Phối cảnh tuyến tính",
        "Tạo chiều sâu bằng các đường hội tụ về một điểm.",
        [
            "Phối cảnh tuyến tính dùng các đường thẳng hội tụ về một điểm tụ và thu nhỏ dần vật ở xa, "
            "để mặt phẳng bức tranh trông như một ô cửa nhìn vào không gian thật.",
            "Kiến trúc sư Filippo Brunelleschi được ghi nhận là người tìm lại các nguyên tắc này ở "
            "Florence đầu thế kỷ XV; sau đó Leon Battista Alberti hệ thống hóa chúng trong sách “Về "
            "hội họa” (khoảng 1435).",
            "Một ví dụ rõ ràng là bức Trao chìa khóa cho thánh Phêrô của Perugino (1481–1482) trong "
            "Nhà nguyện Sistine: quảng trường lát gạch chạy thẳng về ngôi đền ở giữa.",
        ],
        look="Lần theo các đường gạch lát trên quảng trường: chúng cùng hội tụ về cánh cửa của ngôi "
             "đền ở chính giữa bức tranh.",
        caption="Perugino, Trao chìa khóa cho thánh Phêrô, 1481–1482, Nhà nguyện Sistine, Vatican.",
        crop=(0.2, 0.0, 0.8, 0.7), **_pic("keys")),
    Topic(
        "c-chiaroscuro", "concept", "Kỹ thuật", "Sáng tối (chiaroscuro)",
        "Tương phản sáng – tối tạo khối và cảm xúc.",
        [
            "Chiaroscuro (tiếng Ý: “sáng – tối”) là cách dùng tương phản giữa vùng sáng và vùng tối để "
            "vật thể có khối, như nổi lên khỏi mặt tranh.",
            "Khi ánh sáng đến từ một hướng rõ ràng, bóng đổ giúp người xem cảm nhận hình khối và chiều "
            "sâu, còn vùng sáng nhất thường dẫn mắt tới điều quan trọng của bức tranh.",
            "Leonardo dùng nền tối của hang đá trong bức Đức Mẹ trong hang đá để các nhân vật sáng lên, "
            "có khối như tượng. Gần một thế kỷ sau, Caravaggio đẩy tương phản này đến mức gay gắt.",
        ],
        look="Ánh sáng rơi lên gương mặt và bờ vai của Đức Mẹ, thiên thần và hai em bé, trong khi hang "
             "đá phía sau chìm trong bóng tối.",
        caption="Leonardo da Vinci, Đức Mẹ trong hang đá, khoảng 1483–1486, Bảo tàng Louvre, Paris.",
        crop=(0.05, 0.3, 0.95, 0.85), **_pic("rocks")),
    Topic(
        "c-sfumato", "concept", "Kỹ thuật", "Sfumato",
        "Chuyển tiếp mềm như khói giữa sáng và tối.",
        [
            "Sfumato (tiếng Ý, nghĩa là “tan như khói”) là kỹ thuật làm các vùng sáng, tối và đường "
            "viền chuyển vào nhau thật mềm, không có ranh giới sắc nét.",
            "Họa sĩ chồng rất nhiều lớp màu mỏng, gần như trong suốt; mỗi lớp chỉ làm tối hay ấm thêm "
            "một chút, nên mắt ta không thấy nét cọ.",
            "Leonardo da Vinci là bậc thầy của kỹ thuật này. Ở Mona Lisa, khóe miệng và đuôi mắt được "
            "làm mờ nhẹ, khiến biểu cảm như thay đổi tùy cách ta nhìn: đó là một lý do nụ cười ấy khó "
            "nắm bắt đến vậy.",
        ],
        look="Hãy phóng to khóe miệng Mona Lisa: không có đường viền nào, chỉ có những lớp bóng mờ "
             "chuyển dần vào nhau.",
        image=MONA_LISA.image, aspect=MONA_LISA.aspect,
        caption="Leonardo da Vinci, Mona Lisa, khoảng 1503–1519, Bảo tàng Louvre, Paris.",
        crop=(0.2, 0.14, 0.8, 0.45), link=("Xem Mona Lisa", f"/painting/{MONA_LISA.id}")),
    Topic(
        "c-oil", "concept", "Chất liệu", "Sơn dầu",
        "Màu khô chậm, cho phép chồng nhiều lớp mỏng.",
        [
            "Bột màu trộn với dầu khô chậm, cho phép họa sĩ phủ nhiều lớp mỏng trong suốt để tạo độ "
            "sâu, độ bóng và những chi tiết rất nhỏ.",
            "Các họa sĩ vùng Flanders như Jan van Eyck đã làm chủ kỹ thuật này từ đầu thế kỷ XV. Sơn "
            "dầu dần lan sang Ý và thay thế sơn tempera (pha bột màu với lòng đỏ trứng) vốn khô nhanh "
            "và khó hòa màu hơn.",
            "Nhờ sơn dầu, họa sĩ có thể vẽ ánh sáng trên kim loại, độ trong của thủy tinh hay sự mềm "
            "mại của da người một cách thuyết phục.",
        ],
        look="Trong bức Đức Mẹ và chưởng ấn Rolin, hãy nhìn qua hàng cột ở giữa: cả một thành phố với "
             "cầu, sông và những người tí hon được vẽ trong khoảng nhỏ hơn bàn tay.",
        caption="Jan van Eyck, Đức Mẹ và chưởng ấn Rolin, khoảng 1435, Bảo tàng Louvre, Paris.",
        crop=(0.0, 0.0, 1.0, 0.6), **_pic("rolin")),
    Topic(
        "c-patronage", "concept", "Xã hội", "Bảo trợ nghệ thuật",
        "Gia tộc giàu có và Giáo hội đặt hàng tác phẩm.",
        [
            "Nghệ thuật Phục Hưng phần lớn ra đời nhờ người bảo trợ: các gia tộc giàu có, các phường "
            "hội và Giáo hội. Gia tộc ngân hàng Medici ở Florence đã đặt hàng nhiều công trình, trong "
            "đó có thiết kế của Brunelleschi cho nhà thờ San Lorenzo.",
            "Khoảng năm 1459, Benozzo Gozzoli vẽ đoàn rước Ba Vua trên tường nhà nguyện trong dinh thự "
            "Medici và đưa chân dung nhiều người trong gia tộc vào đoàn rước.",
            "Ở Rome, các giáo hoàng như Julius II mời Michelangelo và Raphael thực hiện những công trình "
            "lớn tại Vatican. Người bảo trợ thường quyết định đề tài, kích thước, thậm chí cả chất liệu.",
        ],
        look="Người bảo trợ thường hiện diện ngay trong tác phẩm họ đặt hàng: trong đoàn rước của "
             "Gozzoli, nhiều nhân vật được cho là người nhà Medici và những người thân cận.",
        caption="Benozzo Gozzoli, Đoàn rước của vị vua trẻ nhất (chi tiết), khoảng 1459, dinh thự Medici Riccardi, Florence.",
        crop=(0.0, 0.3, 1.0, 1.0), **_pic("gozzoli")),
    Topic(
        "c-proportion", "concept", "Khoa học", "Tỉ lệ và giải phẫu",
        "Cơ thể người được đo đạc và nghiên cứu như một cấu trúc hài hòa.",
        [
            "Các nghệ sĩ Phục Hưng tin rằng cơ thể con người được xây dựng theo những tỉ lệ hài hòa. "
            "Họ đọc lại kiến trúc sư La Mã Vitruvius, người cho rằng một người đứng dang tay chân có thể "
            "vừa khít trong hình tròn và hình vuông.",
            "Khoảng năm 1490, Leonardo da Vinci vẽ hình Người Vitruvius để kiểm chứng ý tưởng đó. Ông và "
            "Michelangelo còn tự tay mổ xẻ tử thi để hiểu cơ, xương và gân.",
            "Nhờ những nghiên cứu ấy, các thân hình trong tranh và tượng Phục Hưng có trọng lượng, chuyển "
            "động và sức sống chưa từng có.",
        ],
        look="Cùng một thân người vừa khớp vào hình tròn vừa khớp vào hình vuông, chỉ bằng cách thay "
             "đổi tư thế tay chân.",
        caption="Leonardo da Vinci, Người Vitruvius, khoảng 1490, Gallerie dell’Accademia, Venice.",
        crop=(0.05, 0.1, 0.95, 0.75), **_pic("vitruvian")),
    Topic(
        "c-fresco", "concept", "Chất liệu", "Bích họa (fresco)",
        "Vẽ lên vữa còn ướt để màu gắn chặt vào tường.",
        [
            "Fresco là kỹ thuật vẽ lên lớp vữa vôi còn ướt; khi vữa khô, màu gắn chặt vào tường và bền "
            "qua hàng thế kỷ.",
            "Mỗi ngày họa sĩ chỉ trát một mảng vữa vừa đủ để vẽ (người Ý gọi là giornata, “một ngày "
            "làm việc”) và phải vẽ nhanh, vì vữa khô rồi thì rất khó sửa.",
            "Nhiều kiệt tác Phục Hưng là fresco: Chúa Ba Ngôi của Masaccio, trần Nhà nguyện Sistine của "
            "Michelangelo, Trường học Athens của Raphael.",
        ],
        look="Trên trần Sistine, các nhà phục chế vẫn nhận ra ranh giới giữa những mảng vữa vẽ trong "
             "từng ngày, như những mảnh ghép của một bức tranh khổng lồ.",
        caption="Michelangelo, Tạo dựng Adam (chi tiết trần Nhà nguyện Sistine), khoảng 1508–1512, Vatican.",
        crop=(0.25, 0.0, 0.75, 1.0), **_pic("creation")),
    Topic(
        "c-north", "concept", "Không gian", "Phục Hưng phương Bắc",
        "Flanders, Đức, Hà Lan: tỉ mỉ, sơn dầu và tranh in.",
        [
            "Ở phía bắc dãy Alps, các họa sĩ vùng Flanders, Đức và Hà Lan cũng đổi mới nghệ thuật, theo "
            "một cách khác với Ý: chú trọng chi tiết, ánh sáng trên bề mặt đồ vật và đời sống thường ngày.",
            "Jan van Eyck làm chủ sơn dầu; Albrecht Dürer đưa tranh khắc gỗ, khắc đồng lên trình độ cao "
            "và đi khắp châu Âu nhờ máy in; về sau Pieter Bruegel vẽ những cảnh làng quê đông vui.",
            "Hai dòng chảy Nam và Bắc gặp nhau qua thương mại và những chuyến đi, như hai lần Dürer sang Ý.",
        ],
        look="Ở bức tự họa năm 1500, hãy tìm chữ ký lồng hai chữ AD và dòng chữ Latin ở bên phải gương "
             "mặt: Dürer ghi tên và tuổi của mình ngay trên tranh.",
        caption="Albrecht Dürer, Tự họa, 1500, Alte Pinakothek, Munich.",
        crop=(0.1, 0.05, 0.9, 0.5), **_pic("durer")),
]
CONCEPTS_ON_HOME = 4

# ---------------------------------------------------------------------------- "Bạn có biết?"
# (câu hỏi, câu trả lời ngắn trên thẻ, giải thích thêm khi bấm vào)
FACTS = [
    ("“Phục Hưng” nghĩa là gì?",
     "“Renaissance” là tiếng Pháp, nghĩa là “tái sinh”.",
     "Người đương thời cảm thấy mình đang làm sống lại văn hóa Hy Lạp – La Mã sau nhiều thế kỷ. "
     "Giorgio Vasari dùng chữ “rinascita” (sự tái sinh) năm 1550; đến thế kỷ XIX, các nhà sử học "
     "như Jules Michelet và Jacob Burckhardt biến “Renaissance” thành tên gọi cả một thời đại."),
    ("Vì sao bắt đầu ở Ý?",
     "Các thành bang như Florence giàu nhờ thương mại, ngân hàng và có nhiều di tích La Mã.",
     "Các thành bang Ý như Florence, Venice, Milan giàu lên nhờ buôn bán và ngân hàng, nên có người "
     "và tiền để bảo trợ nghệ thuật. Họ sống giữa tàn tích La Mã cổ đại, và khi các học giả từ "
     "Constantinople sang Ý, nhất là sau năm 1453, họ mang theo nhiều bản thảo Hy Lạp cổ."),
    ("Ai đặt nền cho chủ nghĩa nhân văn?",
     "Nhà thơ Petrarch, người đề cao việc đọc các tác giả cổ điển.",
     "Petrarch (1304–1374) săn tìm những bản thảo cổ bị lãng quên trong các tu viện, như thư của "
     "Cicero, và kêu gọi học lại tiếng Latin cổ điển. Ông được coi là cha đẻ của chủ nghĩa nhân văn."),
    ("Máy in đã thay đổi gì?",
     "Sách in rẻ và nhanh hơn chép tay, nên tư tưởng mới lan khắp châu Âu.",
     "Sau Kinh Thánh Gutenberg (khoảng 1455), các xưởng in mọc lên nhanh chóng. Sách cổ điển, sách "
     "khoa học và cả tranh khắc in như của Dürer đi khắp châu Âu, giúp ý tưởng lan xa nhanh hơn "
     "bao giờ hết."),
    ("Leonardo chỉ là họa sĩ?",
     "Ông còn nghiên cứu giải phẫu, cơ khí, thực vật… và để lại hàng nghìn trang sổ tay.",
     "Leonardo da Vinci ghi chép về giải phẫu, dòng chảy của nước, chuyến bay của chim, máy móc, "
     "thực vật… bằng lối viết ngược từ phải sang trái. Hàng nghìn trang sổ tay của ông còn lưu "
     "giữ đến ngày nay, nhưng số tranh ông thực sự hoàn thành lại khá ít."),
    ("Sơn dầu đến từ đâu?",
     "Họa sĩ vùng Flanders như van Eyck đã làm chủ kỹ thuật này rất sớm.",
     "Dầu đã được dùng trong hội họa từ trước, nhưng Jan van Eyck và các họa sĩ Flanders đầu thế kỷ "
     "XV đã đưa sơn dầu lên một trình độ mới. Kỹ thuật này dần lan sang Ý, nhất là Venice, và thay "
     "thế sơn tempera."),
]

ALL: dict[str, Topic] = {t.id: t for t in PERIODS + TIMELINE + CONCEPTS}
GROUPS = {"period": PERIODS, "event": TIMELINE, "concept": CONCEPTS}
KIND_NAME = {"period": "Chặng Phục Hưng", "event": "Dòng thời gian", "concept": "Khái niệm"}
