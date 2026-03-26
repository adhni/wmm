from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


CARD_WIDTH = 1080
CARD_HEIGHT = 1350

BG_TOP = "#1f1d36"
BG_BOTTOM = "#c84c2f"
PANEL = "#f6efe6"
TEXT_DARK = "#171c24"
TEXT_LIGHT = "#f7f0e6"
MUTED = "#6f5a64"
ACCENT = "#c84c2f"
ACCENT_DEEP = "#221f3b"
ACCENT_GOLD = "#efb366"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


TITLE_FONT = _load_font(74, bold=True)
SUBTITLE_FONT = _load_font(28, bold=False)
SECTION_FONT = _load_font(22, bold=True)
BODY_FONT = _load_font(30, bold=False)
BODY_BOLD = _load_font(32, bold=True)
SMALL_FONT = _load_font(24, bold=False)
SMALL_BOLD = _load_font(24, bold=True)


def _make_background() -> Image.Image:
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BG_TOP)
    draw = ImageDraw.Draw(image)
    for y in range(CARD_HEIGHT):
        ratio = y / CARD_HEIGHT
        top = int(int(BG_TOP[1:3], 16) * (1 - ratio) + int(BG_BOTTOM[1:3], 16) * ratio)
        mid = int(int(BG_TOP[3:5], 16) * (1 - ratio) + int(BG_BOTTOM[3:5], 16) * ratio)
        bot = int(int(BG_TOP[5:7], 16) * (1 - ratio) + int(BG_BOTTOM[5:7], 16) * ratio)
        draw.line((0, y, CARD_WIDTH, y), fill=(top, mid, bot))

    draw.rounded_rectangle((52, 56, CARD_WIDTH - 52, CARD_HEIGHT - 56), radius=36, fill=PANEL)
    draw.rounded_rectangle((84, 86, CARD_WIDTH - 84, 380), radius=28, fill=ACCENT_DEEP)
    return image


def _wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [text]


def _draw_lines(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: list[str],
    font: ImageFont.ImageFont,
    fill: str,
    spacing: int,
) -> int:
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, current_y), line, font=font)
        current_y += (bbox[3] - bbox[1]) + spacing
    return current_y


def _pill(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, value: str) -> None:
    draw.rounded_rectangle(box, radius=22, fill="#ffffff", outline="#eadcc7", width=2)
    x0, y0, _, _ = box
    draw.text((x0 + 22, y0 + 18), label.upper(), font=SECTION_FONT, fill=MUTED)
    draw.text((x0 + 22, y0 + 56), value, font=BODY_BOLD, fill=TEXT_DARK)


def _to_png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def runner_passport_card(
    runner_name: str,
    summary: dict[str, str | int],
    road_row: pd.Series,
    story: str,
) -> bytes:
    image = _make_background()
    draw = ImageDraw.Draw(image)

    draw.text((118, 116), "WMM RUNNER PASSPORT", font=SECTION_FONT, fill=ACCENT_GOLD)
    draw.text((118, 158), runner_name, font=TITLE_FONT, fill=TEXT_LIGHT)
    draw.text((118, 262), f"{summary['stars']} stars • {summary['entries']} finishes • {summary['years_active']} active years", font=BODY_FONT, fill=TEXT_LIGHT)
    _draw_lines(draw, 118, 316, _wrap(story, 50), SMALL_FONT, "#f1e4d8", 8)

    _pill(draw, (118, 430, 470, 560), "Best Time", str(summary["best_time"]))
    _pill(draw, (500, 430, 962, 560), "Best Indo Rank", f"#{summary['best_indo_place']}")
    _pill(draw, (118, 584, 540, 714), "Favorite Course", str(summary["favorite_marathon"]))
    _pill(draw, (570, 584, 962, 714), "Latest Result", str(summary["latest_result"]))

    draw.text((118, 782), "COMPLETED MAJORS", font=SECTION_FONT, fill=ACCENT)
    completed_lines = _wrap(str(road_row["Completed_Majors"]), 40)
    _draw_lines(draw, 118, 820, completed_lines, BODY_BOLD, TEXT_DARK, 10)

    draw.text((118, 930), "MISSING MAJORS", font=SECTION_FONT, fill=ACCENT)
    missing_text = str(road_row["Missing_Majors"])
    _draw_lines(draw, 118, 968, _wrap(missing_text, 40), BODY_BOLD, TEXT_DARK, 10)

    draw.rounded_rectangle((118, 1080, 962, 1228), radius=24, fill="#ffffff", outline="#eadcc7", width=2)
    draw.text((148, 1114), "Peak result", font=SECTION_FONT, fill=MUTED)
    _draw_lines(draw, 148, 1152, _wrap(str(summary["best_result"]), 44), BODY_BOLD, TEXT_DARK, 8)

    draw.text((118, 1262), "Generated from the Indonesian WMM dashboard", font=SMALL_FONT, fill=MUTED)
    return _to_png_bytes(image)


def runner_milestones_card(
    runner_name: str,
    milestones: pd.DataFrame,
    badges: list[dict[str, str]],
) -> bytes:
    image = _make_background()
    draw = ImageDraw.Draw(image)

    draw.text((118, 116), "RUNNER JOURNEY", font=SECTION_FONT, fill=ACCENT_GOLD)
    draw.text((118, 158), runner_name, font=TITLE_FONT, fill=TEXT_LIGHT)
    draw.text((118, 262), "Milestones and unlocked achievements", font=BODY_FONT, fill=TEXT_LIGHT)

    draw.text((118, 424), "MILESTONES", font=SECTION_FONT, fill=ACCENT)
    y = 470
    for idx, row in milestones.head(6).iterrows():
        draw.rounded_rectangle((118, y, 962, y + 98), radius=18, fill="#ffffff", outline="#eadcc7", width=2)
        draw.text((146, y + 18), str(row["Milestone"]), font=SMALL_BOLD, fill=TEXT_DARK)
        draw.text((146, y + 50), f"{row['Year']} • {row['Detail']}", font=SMALL_FONT, fill=MUTED)
        y += 112

    draw.text((118, y + 18), "BADGES", font=SECTION_FONT, fill=ACCENT)
    y += 62
    for badge in badges[:6]:
        draw.rounded_rectangle((118, y, 962, y + 76), radius=18, fill="#fff6eb", outline="#f0d6b4", width=2)
        draw.text((146, y + 16), str(badge["title"]), font=SMALL_BOLD, fill=ACCENT_DEEP)
        draw.text((430, y + 16), str(badge["detail"]), font=SMALL_FONT, fill=MUTED)
        y += 90

    draw.text((118, 1262), "Share your visible WMM journey", font=SMALL_FONT, fill=MUTED)
    return _to_png_bytes(image)


def runner_goals_card(
    runner_name: str,
    goals: pd.DataFrame,
    rarity: pd.DataFrame,
) -> bytes:
    image = _make_background()
    draw = ImageDraw.Draw(image)

    draw.text((118, 116), "WHAT'S NEXT", font=SECTION_FONT, fill=ACCENT_GOLD)
    draw.text((118, 158), runner_name, font=TITLE_FONT, fill=TEXT_LIGHT)
    draw.text((118, 262), "Targets, rarity, and the next level to chase", font=BODY_FONT, fill=TEXT_LIGHT)

    draw.text((118, 424), "NEXT GOALS", font=SECTION_FONT, fill=ACCENT)
    y = 470
    for _, row in goals.head(4).iterrows():
        draw.rounded_rectangle((118, y, 962, y + 120), radius=20, fill="#ffffff", outline="#eadcc7", width=2)
        draw.text((146, y + 18), str(row["Goal"]).upper(), font=SECTION_FONT, fill=MUTED)
        draw.text((146, y + 48), str(row["Target"]), font=BODY_BOLD, fill=TEXT_DARK)
        draw.text((560, y + 48), str(row["Gap"]), font=BODY_BOLD, fill=ACCENT)
        _draw_lines(draw, 146, y + 84, _wrap(str(row["Why"]), 52), SMALL_FONT, MUTED, 6)
        y += 142

    draw.text((118, y + 12), "RARITY", font=SECTION_FONT, fill=ACCENT)
    y += 58
    for _, row in rarity.iterrows():
        draw.rounded_rectangle((118, y, 962, y + 76), radius=18, fill="#fff6eb", outline="#f0d6b4", width=2)
        draw.text((146, y + 16), str(row["Metric"]), font=SMALL_BOLD, fill=ACCENT_DEEP)
        draw.text((360, y + 16), str(row["Standing"]), font=SMALL_BOLD, fill=ACCENT)
        draw.text((560, y + 16), str(row["Rank"]), font=SMALL_FONT, fill=MUTED)
        draw.text((820, y + 16), str(row["Value"]), font=SMALL_FONT, fill=MUTED)
        y += 90

    return _to_png_bytes(image)
