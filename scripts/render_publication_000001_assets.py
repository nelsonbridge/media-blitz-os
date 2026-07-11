#!/usr/bin/env python3
"""Render deterministic Publication #1 visual assets and a checksum manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

WIDTHS = {
    "NKS-DGM-000001-signature-diagram.png": (1600, 900),
    "NKS-HRO-000001-hero.png": (1600, 900),
    "NKS-QTC-000001-quote-card.png": (1200, 1200),
    "NKS-PIN-000001-pinterest.png": (1000, 1500),
    **{
        f"NKS-CAR-000001-panel-{index:02d}.png": (1080, 1350)
        for index in range(1, 8)
    },
}

REQUESTS = {
    "NKS-DGM-000001-signature-diagram.png": "NKS-VRQ-000001",
    "NKS-HRO-000001-hero.png": "NKS-VRQ-000002",
    **{
        f"NKS-CAR-000001-panel-{index:02d}.png": "NKS-VRQ-000003"
        for index in range(1, 8)
    },
    "NKS-QTC-000001-quote-card.png": "NKS-VRQ-000004",
    "NKS-PIN-000001-pinterest.png": "NKS-VRQ-000005",
}

BG = "#F3F0E8"
INK = "#15222C"
MUTED = "#5D6970"
NAVY = "#1D3445"
TEAL = "#2F6F70"
TEAL_LIGHT = "#B8D5D1"
GOLD = "#B88A3B"
RED = "#8E4C45"
WHITE = "#FFFDF8"
LINE = "#AEB7B7"

FONT_REGULAR_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
)
FONT_BOLD_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
)
FONT_MONO_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
)


def _font_path(candidates: Iterable[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("no supported system font found")


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        FONT_MONO_CANDIDATES
        if mono
        else FONT_BOLD_CANDIDATES
        if bold
        else FONT_REGULAR_CANDIDATES
    )
    return ImageFont.truetype(str(_font_path(candidates)), size)


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    *,
    radius: int = 18,
    fill: str = WHITE,
    outline: str | None = None,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_px(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), trial, font=text_font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
    *,
    fill: str = INK,
    spacing: int = 8,
) -> int:
    x, y = xy
    for line in wrap_px(draw, text, text_font, max_width):
        draw.text((x, y), line, font=text_font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=text_font)
        y += bbox[3] - bbox[1] + spacing
    return y


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    fill: str = TEAL,
    width: int = 5,
    head: int = 14,
) -> None:
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    point_1 = (
        x2 - head * math.cos(angle - math.pi / 6),
        y2 - head * math.sin(angle - math.pi / 6),
    )
    point_2 = (
        x2 - head * math.cos(angle + math.pi / 6),
        y2 - head * math.sin(angle + math.pi / 6),
    )
    draw.polygon([(x2, y2), point_1, point_2], fill=fill)


def save(image: Image.Image, output: Path, filename: str) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    path = output / filename
    image.save(path, optimize=True)
    return path


def render_signature_diagram(output: Path) -> Path:
    image = Image.new("RGB", (1600, 900), BG)
    draw = ImageDraw.Draw(image)
    draw.text(
        (80, 55),
        "THE CORPUS IS MANUFACTURED, NOT FOUND",
        font=font(42, bold=True),
        fill=INK,
    )
    draw.text(
        (82, 112),
        "A governed knowledge manufacturing pipeline",
        font=font(23),
        fill=MUTED,
    )
    stages = [
        ("FRAGMENTED\nSOURCES", "conversations\nnotes\nfiles"),
        ("EVIDENCE\n+ PROOF", "claims\nlimits\ncitations"),
        ("CANONICAL\nARTIFACT", "stable ID\nlineage\nstate"),
        ("NARRATIVE\nARC", "recognition\nreframe\napplication"),
        ("VISUAL\nPACKAGE", "diagram\nhero\nsocial assets"),
        ("PUBLICATION\nPACKAGE", "approved body\nassets\nreceipt"),
        ("DISTRIBUTION", "platform\nadapters\nmanual fallback"),
        ("FEEDBACK", "real signals\nclassified\nbounded"),
        ("CORPUS\nENRICHMENT", "reviewed input\nnew lineage\ncompounding\nreuse"),
    ]
    margin, y, height, gap = 40, 255, 270, 12
    box_width = (1600 - 2 * margin - gap * (len(stages) - 1)) / len(stages)
    for index, (title, subtitle) in enumerate(stages):
        x = margin + index * (box_width + gap)
        box_fill = "#E7F0ED" if index in (1, 8) else WHITE
        rounded(
            draw,
            (x, y, x + box_width, y + height),
            radius=16,
            fill=box_fill,
            outline=NAVY,
        )
        draw.rectangle(
            (x, y, x + box_width, y + 9),
            fill=GOLD if index in (1, 8) else TEAL,
        )
        title_lines = title.splitlines()
        title_start = y + 42 if len(title_lines) == 2 else y + 64
        for line_index, line in enumerate(title_lines):
            draw.text(
                (x + box_width / 2, title_start + line_index * 36),
                line,
                font=font(18, bold=True),
                fill=INK,
                anchor="ma",
            )
        subtitle_lines = subtitle.splitlines()
        subtitle_start = y + 148 if len(subtitle_lines) <= 3 else y + 135
        for line_index, line in enumerate(subtitle_lines):
            draw.text(
                (x + box_width / 2, subtitle_start + line_index * 27),
                line,
                font=font(15),
                fill=MUTED,
                anchor="ma",
            )
        if index < len(stages) - 1:
            arrow(
                draw,
                (x + box_width + 2, y + height / 2),
                (x + box_width + gap - 2, y + height / 2),
                width=3,
                head=9,
            )
    draw.text(
        (80, 620),
        "Publishing is one downstream output—not the system itself.",
        font=font(29, bold=True),
        fill=NAVY,
    )
    draw.text(
        (80, 675),
        "Every stage preserves proof boundaries, lineage, and explicit human gates.",
        font=font(23),
        fill=MUTED,
    )
    rounded(draw, (80, 750, 1520, 825), radius=14, fill="#E6E1D6")
    draw.text((110, 774), "CONTROL PRINCIPLE", font=font(18, bold=True), fill=GOLD)
    draw.text(
        (330, 774),
        "External systems are adapters. Canonical identifiers and domain policy remain portable.",
        font=font(20),
        fill=INK,
    )
    return save(image, output, "NKS-DGM-000001-signature-diagram.png")


def render_hero(output: Path) -> Path:
    image = Image.new("RGB", (1600, 900), BG)
    draw = ImageDraw.Draw(image)
    fragments = [
        (90, 130, 340, 265),
        (160, 330, 420, 485),
        (65, 570, 300, 730),
        (390, 165, 570, 300),
        (420, 520, 650, 700),
    ]
    for index, box in enumerate(fragments):
        x1, y1, x2, y2 = box
        rounded(draw, box, radius=22, fill=WHITE, outline=LINE)
        draw.rectangle(
            (x1 + 22, y1 + 25, x2 - 22, y1 + 35),
            fill=TEAL if index % 2 == 0 else GOLD,
        )
        for line_index in range(4):
            line_y = y1 + 65 + line_index * 28
            draw.line(
                (x1 + 25, line_y, x2 - 30 - (line_index % 2) * 35, line_y),
                fill="#C6CECC",
                width=5,
            )
    hub = (820, 450)
    for box in fragments:
        draw.line(
            (box[2] + 10, (box[1] + box[3]) / 2, hub[0] - 85, hub[1]),
            fill=TEAL_LIGHT,
            width=4,
        )
    for radius, stroke, color in ((95, 8, GOLD), (70, 5, TEAL), (40, 3, NAVY)):
        draw.ellipse(
            (
                hub[0] - radius,
                hub[1] - radius,
                hub[0] + radius,
                hub[1] + radius,
            ),
            outline=color,
            width=stroke,
        )
    grid_x, grid_y = 980, 145
    cell_width, cell_height = 150, 125
    for row in range(4):
        for column in range(3):
            x1 = grid_x + column * (cell_width + 30)
            y1 = grid_y + row * (cell_height + 28)
            cell_fill = "#E8EFEC" if (row + column) % 3 == 0 else WHITE
            rounded(
                draw,
                (x1, y1, x1 + cell_width, y1 + cell_height),
                radius=18,
                fill=cell_fill,
                outline=NAVY,
            )
            draw.rectangle(
                (x1 + 18, y1 + 20, x1 + cell_width - 18, y1 + 28),
                fill=TEAL if column < 2 else GOLD,
            )
            draw.line(
                (x1 + 20, y1 + 58, x1 + cell_width - 24, y1 + 58),
                fill="#C4CCCA",
                width=5,
            )
            draw.line(
                (x1 + 20, y1 + 83, x1 + cell_width - 44, y1 + 83),
                fill="#C4CCCA",
                width=5,
            )
    for row in range(4):
        arrow(
            draw,
            (hub[0] + 100, hub[1]),
            (grid_x - 25, grid_y + row * (cell_height + 28) + cell_height / 2),
            width=3,
            head=9,
        )
    draw.rounded_rectangle((1010, 60, 1510, 112), radius=12, outline="#DDD7CB", width=2)
    draw.line((1035, 86, 1440, 86), fill="#E2DDD2", width=3)
    return save(image, output, "NKS-HRO-000001-hero.png")


CAROUSEL = [
    (
        "01",
        "FRAGMENTED KNOWLEDGE\nIS NOT YET A CORPUS",
        "Conversations, notes, files, and frameworks can contain value without forming a governed system.",
        "Fragments",
    ),
    (
        "02",
        "SOURCES REQUIRE\nPROOF BOUNDARIES",
        "Claims need support, limitations, and an explicit record of what the evidence does not establish.",
        "Proof",
    ),
    (
        "03",
        "CANONICAL ARTIFACTS\nCREATE REUSABLE STRUCTURE",
        "Stable identifiers, lineage, and governed state make knowledge durable and composable.",
        "Structure",
    ),
    (
        "04",
        "NARRATIVE ARCS TURN\nSTRUCTURE INTO UNDERSTANDING",
        "Recognition, reframe, framework, proof, application, and consequence create a coherent path.",
        "Meaning",
    ),
    (
        "05",
        "VISUAL PACKAGES MAKE\nSYSTEMS LEGIBLE",
        "Diagrams and editorial assets expose relationships that prose alone can leave hidden.",
        "Legibility",
    ),
    (
        "06",
        "PUBLICATION IS ONE\nDOWNSTREAM OUTPUT",
        "Articles and social derivatives consume governed knowledge; they do not define the system.",
        "Distribution",
    ),
    (
        "07",
        "FEEDBACK CAN ENRICH\nTHE CORPUS",
        "Observed signals remain bounded candidates until classification, proof review, and authorization.",
        "Enrichment",
    ),
]


def _carousel_motif(draw: ImageDraw.ImageDraw, index: int) -> None:
    if index == 1:
        boxes = [
            (100, 265, 350, 410),
            (470, 220, 690, 355),
            (185, 505, 420, 650),
            (590, 475, 875, 640),
        ]
        for box_index, box in enumerate(boxes):
            rounded(draw, box, fill=WHITE, outline=LINE)
            draw.line(
                (box[0] + 25, box[1] + 45, box[2] - 25, box[1] + 45),
                fill=TEAL if box_index % 2 == 0 else GOLD,
                width=6,
            )
    elif index == 2:
        rounded(draw, (170, 250, 910, 625), radius=25, fill=WHITE, outline=NAVY, width=3)
        draw.text((230, 300), "SUPPORTED", font=font(25, bold=True), fill=TEAL)
        draw.text((670, 300), "LIMITED", font=font(25, bold=True), fill=RED)
        draw.line((540, 285, 540, 590), fill=LINE, width=3)
        for row in range(4):
            y = 372 + row * 52
            draw.ellipse((235, y - 7, 250, y + 8), fill=TEAL)
            draw.line((275, y, 485, y), fill="#BEC7C5", width=6)
            draw.ellipse((675, y - 7, 690, y + 8), fill=RED)
            draw.line((715, y, 855, y), fill="#BEC7C5", width=6)
    elif index == 3:
        labels = ("SRC", "ART", "PRF", "NAR", "VIS", "PUB")
        for row in range(2):
            for column in range(3):
                x = 150 + column * 270
                y = 240 + row * 190
                rounded(draw, (x, y, x + 210, y + 140), fill=WHITE, outline=NAVY)
                draw.text(
                    (x + 25, y + 25),
                    f"NKS-{labels[row * 3 + column]}",
                    font=font(20, bold=True, mono=True),
                    fill=GOLD,
                )
                draw.line((x + 25, y + 75, x + 175, y + 75), fill=TEAL, width=7)
    elif index == 4:
        steps = ("RECOGNITION", "REFRAME", "FRAMEWORK", "PROOF", "APPLICATION", "CONSEQUENCE")
        for step_index, step in enumerate(steps):
            x = 125 + (step_index % 2) * 455
            y = 220 + (step_index // 2) * 155
            rounded(draw, (x, y, x + 380, y + 105), fill=WHITE, outline=NAVY)
            draw.text(
                (x + 25, y + 34),
                step,
                font=font(24, bold=True),
                fill=TEAL if step_index % 2 == 0 else GOLD,
            )
    elif index == 5:
        rounded(draw, (100, 250, 430, 620), radius=22, fill=WHITE, outline=LINE)
        for row in range(10):
            draw.line(
                (135, 290 + row * 29, 390 - (row % 3) * 35, 290 + row * 29),
                fill="#C5CECC",
                width=5,
            )
        arrow(draw, (470, 435), (600, 435), fill=GOLD, width=7, head=18)
        for cell in range(4):
            x = 650 + (cell % 2) * 165
            y = 295 + (cell // 2) * 170
            rounded(draw, (x, y, x + 130, y + 115), radius=16, fill="#E5EFEC", outline=NAVY)
    elif index == 6:
        rounded(draw, (360, 240, 720, 480), radius=25, fill="#E5EFEC", outline=NAVY, width=3)
        draw.multiline_text(
            (540, 330),
            "GOVERNED\nCORPUS",
            font=font(33, bold=True),
            fill=INK,
            anchor="mm",
            align="center",
        )
        outputs = (("ARTICLE", 120, 590), ("THREAD", 355, 650), ("DIAGRAM", 590, 650), ("POST", 825, 590))
        for label, x, y in outputs:
            arrow(draw, (540, 500), (x + 55, y - 15), width=4, head=12)
            rounded(draw, (x, y, x + 130, y + 90), radius=15, fill=WHITE, outline=NAVY)
            draw.text((x + 65, y + 45), label, font=font(17, bold=True), fill=GOLD, anchor="mm")
    else:
        rounded(draw, (155, 245, 430, 420), fill=WHITE, outline=NAVY)
        draw.multiline_text(
            (292, 332),
            "OBSERVED\nSIGNAL",
            font=font(27, bold=True),
            fill=INK,
            anchor="mm",
            align="center",
        )
        arrow(draw, (450, 332), (610, 332), fill=GOLD, width=6, head=16)
        rounded(draw, (635, 245, 925, 420), fill="#E5EFEC", outline=NAVY)
        draw.multiline_text(
            (780, 332),
            "CLASSIFY\n+ REVIEW",
            font=font(27, bold=True),
            fill=INK,
            anchor="mm",
            align="center",
        )
        arrow(draw, (780, 445), (540, 590), width=6, head=16)
        rounded(draw, (350, 610, 730, 790), radius=22, fill=WHITE, outline=NAVY, width=3)
        draw.multiline_text(
            (540, 700),
            "AUTHORIZED\nENRICHMENT",
            font=font(29, bold=True),
            fill=TEAL,
            anchor="mm",
            align="center",
        )


def render_carousel(output: Path) -> list[Path]:
    paths: list[Path] = []
    for index, (number, title, body, label) in enumerate(CAROUSEL, 1):
        image = Image.new("RGB", (1080, 1350), BG)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1080, 18), fill=TEAL if index < 7 else GOLD)
        draw.text((75, 70), number, font=font(34, bold=True, mono=True), fill=GOLD)
        draw.text(
            (1005, 80),
            "NELSON KNOWLEDGE SYSTEM",
            font=font(17, bold=True),
            fill=MUTED,
            anchor="ra",
        )
        _carousel_motif(draw, index)
        title_y = 810 if index != 7 else 845
        for line_index, line in enumerate(title.splitlines()):
            draw.text(
                (75, title_y + line_index * 60),
                line,
                font=font(44, bold=True),
                fill=INK,
            )
        draw_wrapped(draw, (75, title_y + 145), body, font(27), 900, fill=MUTED, spacing=12)
        draw.line((75, 1220, 1005, 1220), fill=LINE, width=2)
        draw.text((75, 1250), label.upper(), font=font(20, bold=True, mono=True), fill=GOLD)
        draw.text(
            (1005, 1250),
            "THE CORPUS IS MANUFACTURED, NOT FOUND",
            font=font(16, bold=True),
            fill=MUTED,
            anchor="ra",
        )
        paths.append(save(image, output, f"NKS-CAR-000001-panel-{index:02d}.png"))
    return paths


def render_quote_card(output: Path) -> Path:
    image = Image.new("RGB", (1200, 1200), NAVY)
    draw = ImageDraw.Draw(image)
    for index in range(7):
        x = 75 + index * 70
        y = 85 + index * 35
        draw.rectangle((x, y, x + 260, y + 150), outline="#355164", width=3)
    draw.rectangle((0, 0, 18, 1200), fill=GOLD)
    draw.text((100, 120), "“", font=font(150, bold=True), fill=GOLD)
    draw.multiline_text(
        (110, 330),
        "A corpus is\nmanufactured,\nnot found.",
        font=font(68, bold=True),
        fill=WHITE,
        spacing=22,
    )
    draw.line((110, 830, 670, 830), fill=TEAL_LIGHT, width=5)
    draw.text((110, 875), "S. MICHAEL NELSON", font=font(28, bold=True), fill=TEAL_LIGHT)
    draw.text((110, 1015), "NELSON KNOWLEDGE SYSTEM", font=font(18, bold=True, mono=True), fill="#8FA7B3")
    return save(image, output, "NKS-QTC-000001-quote-card.png")


def render_pinterest(output: Path) -> Path:
    image = Image.new("RGB", (1000, 1500), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1000, 18), fill=GOLD)
    draw.text((70, 75), "THE KNOWLEDGE", font=font(42, bold=True), fill=INK)
    draw.text((70, 130), "MANUFACTURING PIPELINE", font=font(42, bold=True), fill=INK)
    draw.text((72, 198), "A governed path from source material to learning", font=font(21), fill=MUTED)
    steps = ("SOURCES", "PROOF", "CANONICAL ARTIFACT", "NARRATIVE ARC", "VISUAL PACKAGE", "PUBLICATION", "FEEDBACK")
    y = 300
    for index, step in enumerate(steps):
        rounded(
            draw,
            (130, y, 870, y + 115),
            radius=24,
            fill="#E5EFEC" if index in (1, 6) else WHITE,
            outline=NAVY,
            width=3,
        )
        draw.ellipse((165, y + 34, 215, y + 84), fill=GOLD if index in (1, 6) else TEAL)
        draw.text((190, y + 59), str(index + 1), font=font(22, bold=True, mono=True), fill=WHITE, anchor="mm")
        draw.text((250, y + 56), step, font=font(28, bold=True), fill=INK, anchor="lm")
        if index < len(steps) - 1:
            arrow(draw, (500, y + 120), (500, y + 158), width=5, head=13)
        y += 160
    rounded(draw, (70, 1370, 930, 1440), radius=16, fill=NAVY)
    draw.text(
        (500, 1405),
        "THE CORPUS IS MANUFACTURED, NOT FOUND.",
        font=font(22, bold=True),
        fill=WHITE,
        anchor="mm",
    )
    return save(image, output, "NKS-PIN-000001-pinterest.png")


def render_review_sheet(output: Path, asset_paths: list[Path]) -> Path:
    thumbnails: list[tuple[str, Image.Image]] = []
    for path in sorted(asset_paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((380, 280))
        thumbnails.append((path.name, image.copy()))
    rows = math.ceil(len(thumbnails) / 3)
    sheet = Image.new("RGB", (1200, rows * 360), WHITE)
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbnails):
        column = index % 3
        row = index // 3
        x = 20 + column * 395
        y = 20 + row * 360
        sheet.paste(image, (x, y))
        draw.text((x, y + 290), name, font=font(14), fill=INK)
    return save(sheet, output, "NKS-VIS-000001-review-sheet.png")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_requests(repository_root: Path) -> None:
    expected = {
        "NKS-VRQ-000001": "NKS-DGM-000001",
        "NKS-VRQ-000002": "NKS-HRO-000001",
        "NKS-VRQ-000003": "NKS-CAR-000001",
        "NKS-VRQ-000004": "NKS-QTC-000001",
        "NKS-VRQ-000005": "NKS-PIN-000001",
    }
    for request_id, visual_id in expected.items():
        path = repository_root / "records" / "visual-requests" / f"{request_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["request_id"] != request_id or payload["visual_id"] != visual_id:
            raise ValueError(f"visual request identity mismatch: {path}")
        if payload.get("metadata", {}).get("review_required") is not True:
            raise ValueError(f"visual request must require review: {path}")


def build_manifest(output: Path, asset_paths: list[Path], review_sheet: Path) -> Path:
    assets = []
    for path in sorted(asset_paths):
        with Image.open(path) as image:
            dimensions = list(image.size)
        if tuple(dimensions) != WIDTHS[path.name]:
            raise ValueError(f"unexpected dimensions for {path.name}: {dimensions}")
        assets.append(
            {
                "filename": path.name,
                "request_id": REQUESTS[path.name],
                "dimensions": dimensions,
                "sha256": sha256(path),
                "review_status": "needed",
            }
        )
    with Image.open(review_sheet) as image:
        review_dimensions = list(image.size)
    payload = {
        "manifest_id": "NKS-VIS-MANIFEST-000001",
        "publication_id": "NKS-PUB-000001",
        "visual_package_id": "NKS-VIS-000001",
        "renderer": "scripts/render_publication_000001_assets.py",
        "renderer_version": 1,
        "review_required": True,
        "approval_status": "needed",
        "assets": assets,
        "review_sheet": {
            "filename": review_sheet.name,
            "dimensions": review_dimensions,
            "sha256": sha256(review_sheet),
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def render_all(repository_root: Path, output: Path) -> list[Path]:
    validate_requests(repository_root)
    asset_paths = [
        render_signature_diagram(output),
        render_hero(output),
        *render_carousel(output),
        render_quote_card(output),
        render_pinterest(output),
    ]
    review_sheet = render_review_sheet(output, asset_paths)
    manifest = build_manifest(output, asset_paths, review_sheet)
    return [*asset_paths, review_sheet, manifest]


def verify(output: Path) -> None:
    manifest_path = output / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload["approval_status"] != "needed" or payload["review_required"] is not True:
        raise ValueError("rendered assets must remain pending review and approval")
    for asset in payload["assets"]:
        path = output / asset["filename"]
        if not path.exists():
            raise FileNotFoundError(path)
        if sha256(path) != asset["sha256"]:
            raise ValueError(f"checksum mismatch: {path}")
        with Image.open(path) as image:
            if list(image.size) != asset["dimensions"]:
                raise ValueError(f"dimension mismatch: {path}")
        if asset["review_status"] != "needed":
            raise ValueError(f"asset review status is not pending: {path}")
    review = payload["review_sheet"]
    review_path = output / review["filename"]
    if sha256(review_path) != review["sha256"]:
        raise ValueError(f"review sheet checksum mismatch: {review_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/publication-000001"),
    )
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    repository_root = args.repository_root.resolve()
    output = args.output
    if not output.is_absolute():
        output = repository_root / output
    if args.verify:
        verify(output)
        print(f"verified: {output}")
        return 0
    paths = render_all(repository_root, output)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
