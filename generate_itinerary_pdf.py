from __future__ import annotations

from typing import List, Sequence

PAGE_WIDTH = 595.28  # A4 portrait in points
PAGE_HEIGHT = 841.89
MARGIN_X = 40
MARGIN_Y = 40


def encode_text(text: str) -> str:
    hex_text = text.encode("utf-16-be").hex()
    return f"<{hex_text}>"


class ContentBuilder:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def extend(self, command: str) -> None:
        self.commands.append(command)

    def set_fill_color(self, r: float, g: float, b: float) -> None:
        self.extend(f"{r:.4f} {g:.4f} {b:.4f} rg")

    def set_stroke_color(self, r: float, g: float, b: float) -> None:
        self.extend(f"{r:.4f} {g:.4f} {b:.4f} RG")

    def draw_rect(self, x: float, y: float, w: float, h: float, fill: bool = False) -> None:
        self.extend(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re")
        self.extend("f" if fill else "S")

    def draw_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.extend(f"{x1:.2f} {y1:.2f} m")
        self.extend(f"{x2:.2f} {y2:.2f} l S")

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        size: float,
        color: tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        self.set_fill_color(*color)
        encoded = encode_text(text)
        self.extend("BT")
        self.extend(f"/F1 {size:.2f} Tf")
        self.extend(f"1 0 0 1 {x:.2f} {y:.2f} Tm")
        self.extend(f"{encoded} Tj")
        self.extend("ET")

    def draw_multiline_text(
        self,
        x: float,
        y: float,
        text_lines: Sequence[str],
        size: float,
        leading: float,
        color: tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        for idx, line in enumerate(text_lines):
            self.draw_text(x, y - idx * leading, line, size, color=color)

    def draw_wrapped_paragraph(
        self,
        x: float,
        y: float,
        text: str,
        size: float,
        leading: float,
        max_width: float,
        color: tuple[float, float, float] = (0, 0, 0),
    ) -> float:
        line_chars = max(int(max_width / (size * 0.9)), 1)
        lines = wrap_text(text, line_chars)
        self.draw_multiline_text(x, y, lines, size, leading, color=color)
        return y - (len(lines) - 1) * leading

    def render(self) -> str:
        return "\n".join(self.commands) + "\n"


def wrap_text(text: str, max_chars: int) -> List[str]:
    words = text.split("\n")
    lines: list[str] = []
    for chunk in words:
        current = ""
        for ch in chunk:
            current += ch
            if len(current) >= max_chars:
                lines.append(current)
                current = ""
        if current or not lines:
            lines.append(current)
    return [line for line in lines if line]


def table_row_height(text_rows: Sequence[Sequence[str]], leading: float) -> list[float]:
    heights = []
    for row in text_rows:
        lines_count = max(len(cell) if cell else 1 for cell in row)
        heights.append(lines_count * leading + 10)
    return heights


def build_summary_section() -> str:
    builder = ContentBuilder()
    width = PAGE_WIDTH - 2 * MARGIN_X
    card_width = (width - 20) / 3
    card_height = 120
    colors_bg = [
        (0.847, 0.898, 0.968),
        (0.910, 0.953, 0.949),
        (0.968, 0.910, 0.937),
    ]
    titles = [
        "DAY1（静安—黄浦）",
        "DAY2（徐汇西岸）",
        "DAY3（多区Citywalk）",
    ]
    routes = [
        "上海自然博物馆 → 静安雕塑公园 → 南京西路 → 兴业太古汇 → 外滩",
        "上海西岸梦中心 → 龙美术馆 → 徐汇滨江绿地 → 油罐艺术中心",
        "武康路 → 徐家汇书院 → M50创意园 → 1933老场坊",
    ]
    tips = [
        "到达方式： 高铁坐到上海虹桥站，地铁13号线直达“自然博物馆”站",
        "",
        "",
    ]
    start_x = MARGIN_X
    y = PAGE_HEIGHT - MARGIN_Y - 80
    for idx in range(3):
        x = start_x + idx * (card_width + 10)
        builder.set_fill_color(*colors_bg[idx])
        builder.draw_rect(x, y - card_height, card_width, card_height, fill=True)
        builder.draw_multiline_text(
            x + 12,
            y - 24,
            [titles[idx]],
            14,
            18,
            color=(0.196, 0.271, 0.388),
        )
        builder.draw_wrapped_paragraph(
            x + 12,
            y - 48,
            routes[idx],
            size=11,
            leading=16,
            max_width=card_width - 24,
            color=(0.106, 0.196, 0.337),
        )
        if tips[idx]:
            builder.draw_wrapped_paragraph(
                x + 12,
                y - 74,
                tips[idx],
                size=10,
                leading=14,
                max_width=card_width - 24,
                color=(0.318, 0.404, 0.502),
            )
    return builder.render()


def draw_table(
    builder: ContentBuilder,
    origin_x: float,
    origin_y: float,
    col_widths: Sequence[float],
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    header_fill: tuple[float, float, float] = (0.945, 0.957, 0.980),
) -> float:
    leading = 14
    cell_text: list[list[list[str]]] = []
    for row_index, row in enumerate([headers] + list(rows)):
        row_cells: list[list[str]] = []
        for col_index, cell in enumerate(row):
            width = max(col_widths[col_index] - 12, 40)
            font_size = 12 if row_index == 0 else 11
            max_chars = max(int(width / (font_size * 0.9)), 1)
            row_cells.append(wrap_text(cell, max_chars=max_chars))
        cell_text.append(row_cells)
    heights = table_row_height(cell_text, leading)
    total_height = sum(heights)
    builder.set_stroke_color(0.79, 0.831, 0.902)
    builder.set_fill_color(*header_fill)
    current_y = origin_y
    table_width = sum(col_widths)
    # header background
    builder.draw_rect(origin_x, current_y - heights[0], table_width, heights[0], fill=True)
    current_y -= heights[0]
    # header text
    x = origin_x
    for idx, text_lines in enumerate(cell_text[0]):
        builder.draw_multiline_text(x + 6, origin_y - 18, text_lines, 12, 16, color=(0.18, 0.247, 0.345))
        x += col_widths[idx]
    # data rows
    for row_idx, row_lines in enumerate(cell_text[1:], start=1):
        height = heights[row_idx]
        x = origin_x
        text_y = current_y - 18
        for col_idx, text_lines in enumerate(row_lines):
            builder.draw_multiline_text(x + 6, text_y, text_lines, 11, leading, color=(0.13, 0.2, 0.31))
            x += col_widths[col_idx]
        current_y -= height

    # table grid lines
    current_y = origin_y
    builder.set_stroke_color(0.79, 0.831, 0.902)
    builder.draw_line(origin_x, origin_y, origin_x + table_width, origin_y)
    for height in heights:
        current_y -= height
        builder.draw_line(origin_x, current_y, origin_x + table_width, current_y)
    x = origin_x
    builder.draw_line(origin_x, origin_y, origin_x, origin_y - total_height)
    for width in col_widths:
        x += width
        builder.draw_line(x, origin_y, x, origin_y - total_height)
    return origin_y - total_height


def build_day_spots(builder: ContentBuilder, x: float, y: float, entries: Sequence[tuple[str, str]]) -> float:
    current_y = y
    for title, detail in entries:
        builder.draw_text(x, current_y, title, 12, color=(0.2, 0.3, 0.47))
        current_y -= 16
        current_y = builder.draw_wrapped_paragraph(
            x,
            current_y,
            detail,
            size=11,
            leading=14,
            max_width=PAGE_WIDTH - x - MARGIN_X,
            color=(0.12, 0.2, 0.32),
        )
        current_y -= 12
    return current_y


def build_page_one() -> str:
    builder = ContentBuilder()
    builder.draw_text(MARGIN_X, PAGE_HEIGHT - MARGIN_Y, "上海3天2晚旅行攻略", 24, color=(0.18, 0.25, 0.39))
    builder.draw_text(MARGIN_X, PAGE_HEIGHT - MARGIN_Y - 32, "一、行程安排总览", 18, color=(0.23, 0.3, 0.43))
    for command in build_summary_section().splitlines():
        if command:
            builder.extend(command)

    builder.draw_text(MARGIN_X, PAGE_HEIGHT - MARGIN_Y - 190, "二、详细行程（表格版）", 18, color=(0.23, 0.3, 0.43))

    y = PAGE_HEIGHT - MARGIN_Y - 220
    builder.draw_text(MARGIN_X, y, "DAY1", 14, color=(0.2, 0.3, 0.47))
    y -= 20

    rows_day1 = [
        [
            "09:00-11:30",
            "上海自然博物馆（¥30）",
            "入馆后按楼层动线参观自然史、演化主题展",
            "Tips: 提前小程序预约，馆内很大，建议租讲解器更清楚！",
        ],
        [
            "11:30-12:30",
            "静安雕塑公园（免费）",
            "自然博物馆旁边步行即达，花园漫走",
            "Tips: 就在自然博物馆旁边，逛完馆正好来散步，绿化很好！",
        ],
        [
            "12:30-14:30",
            "南京西路（免费）",
            "IFS沿线逛街+咖啡休息",
            "Tips: 逛累了找家咖啡馆休息，沿途有很多吃简餐的地方！",
        ],
        [
            "14:30-16:30",
            "兴业太古汇（免费）",
            "商场逛逛+艺术装置拍照",
            "Tips: 商场里吃的选择多，爸妈累了可以坐下来慢慢吃！",
        ],
        [
            "18:30-20:30",
            "外滩（免费）",
            "打车沿江欣赏万国建筑夜景",
            "Tips: 打车逛一圈，避免人流，车里吹空调看夜景超舒服！",
        ],
    ]

    y = draw_table(
        builder,
        MARGIN_X,
        y,
        [80, 120, 200, 140],
        ["时间", "景点", "行程要点", "TIPS"],
        rows_day1,
    )

    y -= 18
    builder.draw_text(MARGIN_X, y, "推荐路线：上海自然博物馆 → 静安雕塑公园 → 南京西路 → 兴业太古汇 → 外滩", 11, color=(0.12, 0.2, 0.32))
    y -= 16
    builder.draw_text(MARGIN_X, y, "到达信息：高铁坐到：上海虹桥站，地铁13号线直达上海自然博物馆，出站就是入口，超方便！", 11, color=(0.12, 0.2, 0.32))

    y -= 26
    builder.draw_text(MARGIN_X, y, "DAY1 打卡机位/要点", 13, color=(0.2, 0.3, 0.47))
    y -= 18

    y = build_day_spots(
        builder,
        MARGIN_X,
        y,
        [
            ("09:00-11:30 自然博物馆", "打卡点：动物世界标本、演化长廊、恐龙化石、互动体验区"),
            ("11:30-12:30 静安雕塑公园", "打卡点：大型雕塑装置、中心喷泉、绿植草坪、艺术画廊"),
            ("12:30-14:30 南京西路", "打卡点：奢侈品旗舰店、街头艺人表演、老字号商店、网红咖啡馆"),
            ("14:30-16:30 兴业太古汇", "打卡点：网红美妆店、艺术装置、空中花园、高端餐厅"),
            ("18:30-20:30 外滩", "打卡点：万国建筑群、黄浦江夜景、和平饭店外观、东方明珠合影"),
        ],
    )

    return builder.render()


def build_page_two() -> str:
    builder = ContentBuilder()

    y = PAGE_HEIGHT - MARGIN_Y
    builder.draw_text(MARGIN_X, y, "DAY2", 14, color=(0.2, 0.3, 0.47))
    y -= 20

    rows_day2 = [
        [
            "09:00-11:00",
            "上海西岸梦中心（免费）",
            "商业街区+墙面打卡点",
            "Tips: 早上去人少，拍照不用躲人头，逛完正好去吃饭！",
        ],
        [
            "11:00-12:30",
            "龙美术馆（¥50）",
            "建筑外观+当代展",
            "Tips: 提前官网预约，馆内禁止大声说话，适合安静看展！",
        ],
        [
            "12:30-14:30",
            "徐汇滨江绿地（免费）",
            "江景步道+草坪",
            "Tips: 可以租自行车逛，爸妈累了就坐草坪休息！",
        ],
        [
            "14:30-16:30",
            "油罐艺术中心（免费）",
            "油罐外观+展厅拍照",
            "Tips: 油罐拍照超出片，下午光线好，建议留足时间！",
        ],
    ]

    y = draw_table(
        builder,
        MARGIN_X,
        y,
        [80, 120, 200, 140],
        ["时间", "景点", "行程要点", "TIPS"],
        rows_day2,
    )
    y -= 18
    builder.draw_text(MARGIN_X, y, "推荐路线：上海西岸梦中心 → 龙美术馆 → 徐汇滨江绿地 → 油罐艺术中心", 11, color=(0.12, 0.2, 0.32))

    y -= 26
    builder.draw_text(MARGIN_X, y, "DAY2 打卡机位/要点", 13, color=(0.2, 0.3, 0.47))
    y -= 18

    y = build_day_spots(
        builder,
        MARGIN_X,
        y,
        [
            ("09:00-11:00 西岸梦中心", "打卡点：网红店铺、可爱装修打卡墙、文创店、露天座椅"),
            ("11:00-12:30 龙美术馆", "打卡点：建筑外观、当代艺术展、江景露台、艺术藏品"),
            ("12:30-14:30 徐汇滨江绿地", "打卡点：黄浦江江景、骑行道、草坪野餐区、滨江雕塑"),
            ("14:30-16:30 油罐艺术中心", "打卡点：巨型油罐结构、艺术展览、屋顶平台、网红咖啡"),
        ],
    )

    y -= 20
    builder.draw_text(MARGIN_X, y, "DAY3", 14, color=(0.2, 0.3, 0.47))
    y -= 20

    rows_day3 = [
        [
            "09:00-11:00",
            "武康路（免费）",
            "历史街区citywalk",
            "Tips: citywalk圣地，慢慢逛，拍照机位要耐心等！",
        ],
        [
            "11:00-12:30",
            "徐家汇书院（免费）",
            "馆内安静参观",
            "Tips: 上海最美图书馆，保持安静，不要打扰读者！",
        ],
        [
            "12:30-14:30",
            "M50创意园（免费）",
            "涂鸦墙+画廊巡游",
            "Tips: 喜欢艺术的必去，很多展览免费看！",
        ],
        [
            "14:30-16:30",
            "1933老场坊（免费）",
            "复古工业风建筑",
            "Tips: 屠宰场改造的创意园，建筑独特，光影超适合拍照！",
        ],
    ]

    y = draw_table(
        builder,
        MARGIN_X,
        y,
        [80, 120, 200, 140],
        ["时间", "景点", "行程要点", "TIPS"],
        rows_day3,
    )
    y -= 18
    builder.draw_text(MARGIN_X, y, "推荐路线：武康路 → 徐家汇书院 → M50创意园 → 1933老场坊", 11, color=(0.12, 0.2, 0.32))

    y -= 26
    builder.draw_text(MARGIN_X, y, "DAY3 打卡机位/要点", 13, color=(0.2, 0.3, 0.47))
    y -= 18

    y = build_day_spots(
        builder,
        MARGIN_X,
        y,
        [
            ("09:00-11:00 武康路", "打卡点：武康大楼、罗密欧阳台、巴金故居、网红咖啡馆"),
            ("11:00-12:30 徐家汇书院", "打卡点：光之穹顶、旋转楼梯、阅读区、建筑外观"),
            ("12:30-14:30 M50创意园", "打卡点：涂鸦墙、艺术画廊、创意店铺、莫干山路涂鸦"),
            ("14:30-16:30 1933老场坊", "打卡点：廊桥、伞形柱、旋梯、牛道"),
        ],
    )

    return builder.render()


def build_page_three() -> str:
    builder = ContentBuilder()

    y = PAGE_HEIGHT - MARGIN_Y
    builder.draw_text(MARGIN_X, y, "三、图片关键词清单（便于选图/检索）", 18, color=(0.23, 0.3, 0.43))
    y -= 28

    def keywords_block(title: str, items: Sequence[tuple[str, str]], start_y: float) -> float:
        builder.draw_text(MARGIN_X, start_y, title, 13, color=(0.2, 0.3, 0.47))
        text_width = PAGE_WIDTH - 2 * MARGIN_X - 200
        max_chars = max(int(text_width / (11 * 0.9)), 1)
        processed: list[tuple[str, list[str]]] = []
        for place, words in items:
            lines = wrap_text(words, max_chars=max_chars)
            if not lines:
                lines = [""]
            processed.append((place, lines))

        box_top = start_y - 14
        sim_y = box_top - 22
        for _, lines in processed:
            keywords_y = sim_y - 16
            last_line_y = keywords_y - (len(lines) - 1) * 14
            sim_y = last_line_y - 24
        box_bottom = sim_y + 8
        box_height = box_top - box_bottom

        builder.set_fill_color(0.973, 0.98, 0.992)
        builder.draw_rect(MARGIN_X, box_bottom, PAGE_WIDTH - 2 * MARGIN_X, box_height, fill=True)

        current_y = box_top - 22
        for place, lines in processed:
            builder.draw_text(MARGIN_X + 12, current_y, place, 12, color=(0.16, 0.25, 0.39))
            keywords_y = current_y - 16
            builder.draw_multiline_text(
                MARGIN_X + 180,
                keywords_y,
                lines,
                11,
                14,
                color=(0.12, 0.2, 0.32),
            )
            current_y = keywords_y - (len(lines) - 1) * 14 - 24
        return box_bottom - 12

    y = keywords_block(
        "DAY1",
        [
            ("上海自然博物馆", "动物标本｜演化长廊｜恐龙化石｜互动区"),
            ("上海静安雕塑公园", "雕塑｜喷泉｜草坪｜画廊"),
            ("上海南京西路", "街景｜奢侈品店｜街头艺人｜咖啡馆"),
            ("上海兴业太古汇", "艺术装置｜空中花园｜网红店｜餐厅"),
            ("上海外滩", "万国建筑｜夜景｜和平饭店｜东方明珠合影"),
        ],
        y,
    )
    y -= 12

    y = keywords_block(
        "DAY2",
        [
            ("上海西岸梦中心", "网红店｜打卡墙｜文创店｜露天座椅"),
            ("上海龙美术馆", "外观｜展览｜江景露台｜藏品"),
            ("上海徐汇滨江绿地", "江景｜骑行道｜草坪｜雕塑"),
            ("上海油罐艺术中心", "油罐｜展览｜屋顶｜咖啡"),
        ],
        y,
    )
    y -= 12

    y = keywords_block(
        "DAY3",
        [
            ("上海武康路", "武康大楼｜罗密欧阳台｜巴金故居｜咖啡馆"),
            ("上海徐家汇书院", "光之穹顶｜旋转楼梯｜阅读区｜外观"),
            ("上海M50创意园", "涂鸦墙｜画廊｜创意店｜莫干山路"),
            ("上海1933老场坊", "廊桥｜伞形柱｜旋梯｜牛道"),
        ],
        y,
    )

    y -= 20
    builder.draw_text(MARGIN_X, y, "四、美食推荐", 18, color=(0.23, 0.3, 0.43))
    y -= 28

    card_width = (PAGE_WIDTH - 2 * MARGIN_X - 20) / 2
    card_height = 180
    card_colors = [
        (0.914, 0.945, 0.992),
        (0.996, 0.945, 0.964),
    ]
    cards = [
        [
            "美食推荐 1/2",
            "店名：毛头老爹饭店",
            "位置：静安区北京西路1068号（自然博物馆旁）",
            "招牌： 黑松露红烧肉拌饭、黑洋酥走油块，软糯不甜，每道都经典！",
            "人均：人均¥80，适合家庭聚餐！",
            "图片关键词：毛头老爹饭店 黑松露红烧肉拌饭｜毛头老爹饭店 黑洋酥走油块｜毛头老爹饭店 店内环境｜毛头老爹饭店 菜品摆盘",
        ],
        [
            "美食推荐 2/2",
            "店名：BLOOMARKET",
            "位置：徐汇区西岸梦中心内（近龙腾大道）",
            "招牌： 酸甜创意菜、网红甜品，口味独特，每道都下饭！",
            "人均：人均¥70，适合年轻人和家庭！",
            "图片关键词：BLOOMARKET 创意菜｜BLOOMARKET 甜品｜BLOOMARKET 店内环境｜BLOOMARKET 菜品特写",
        ],
    ]

    for idx, card in enumerate(cards):
        x = MARGIN_X + idx * (card_width + 20)
        builder.set_fill_color(*card_colors[idx])
        builder.draw_rect(x, y - card_height, card_width, card_height, fill=True)
        text_y = y - 24
        for line in card:
            text_y = builder.draw_wrapped_paragraph(
                x + 12,
                text_y,
                line,
                size=11,
                leading=14,
                max_width=card_width - 24,
                color=(0.13, 0.2, 0.32),
            )
            text_y -= 8

    return builder.render()


def assemble_pdf(pages: Sequence[str], output_path: str) -> None:
    # Font object using standard CJK font
    font_desc_obj = (
        "<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light"
        " /Encoding /UniGB-UCS2-H /DescendantFonts [4 0 R] >>"
    )
    cid_font_obj = (
        "<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light"
        " /CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 2 >>"
        " /FontDescriptor << /Type /FontDescriptor /FontName /STSong-Light"
        " /Flags 4 /FontBBox [0 -200 1000 880] /ItalicAngle 0 /Ascent 880"
        " /Descent -120 /CapHeight 700 /StemV 80 >>"
        " /CIDToGIDMap /Identity /DW 1000 >>"
    )

    final_objects: list[str] = []
    # 1 catalog, 2 pages, 3 font type0, 4 cid font
    final_objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    final_objects.append("<< /Type /Pages /Kids [] /Count 0 >>")
    final_objects.append(font_desc_obj)
    final_objects.append(cid_font_obj)

    page_refs = []
    for page_content in pages:
        stream = page_content.encode("utf-8")
        content_obj = f"<< /Length {len(stream)} >>\nstream\n{page_content}endstream"
        final_objects.append(content_obj)
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH:.2f} {PAGE_HEIGHT:.2f}]"
            f" /Resources << /Font << /F1 3 0 R >> >> /Contents {len(final_objects)} 0 R >>"
        )
        final_objects.append(page_obj)
        page_refs.append(len(final_objects))

    pages_dict = (
        f"<< /Type /Pages /Kids [{' '.join(f'{ref} 0 R' for ref in page_refs)}] /Count {len(page_refs)} >>"
    )
    final_objects[1] = pages_dict

    # Build PDF
    offsets = []
    current_offset = len("%PDF-1.4\n")
    pdf_body = "%PDF-1.4\n"
    for obj_number, obj in enumerate(final_objects, start=1):
        entry = f"{obj_number} 0 obj\n{obj}\nendobj\n"
        offsets.append(current_offset)
        pdf_body += entry
        current_offset += len(entry)

    xref_start = current_offset
    pdf_body += "xref\n"
    pdf_body += f"0 {len(final_objects) + 1}\n"
    pdf_body += "0000000000 65535 f \n"
    for offset in offsets:
        pdf_body += f"{offset:010d} 00000 n \n"
    pdf_body += "trailer\n"
    pdf_body += f"<< /Size {len(final_objects) + 1} /Root 1 0 R >>\n"
    pdf_body += "startxref\n"
    pdf_body += f"{xref_start}\n"
    pdf_body += "%%EOF"

    with open(output_path, "wb") as f:
        f.write(pdf_body.encode("utf-8"))


def build_pdf(output_path: str) -> None:
    pages = [build_page_one(), build_page_two(), build_page_three()]
    assemble_pdf(pages, output_path)


if __name__ == "__main__":
    build_pdf("shanghai-3d2n-itinerary.pdf")
