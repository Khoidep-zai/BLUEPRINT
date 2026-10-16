"""Design tokens for the desktop UI (design §2 ui/).

Single source of truth for colours, radii and spacing used when *painting*
(icons, canvas overlay, badges). The stylesheet in ``assets/dark.qss`` mirrors
these same values — keep the two in sync when changing the palette.

Style: Dark Mode (OLED) — deep background, high contrast (>= 7:1 on body text),
visible focus, consistent corner radii, no decorative gradients or heavy shadows.
Palette derived from the `ui-ux-pro-max` design system ("Code dark + run green").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    bg: str = "#0B1120"          # window background (deepest)
    surface: str = "#0F172A"     # panels / sidebar
    elevated: str = "#1E293B"    # cards, inputs, list rows
    hover: str = "#243449"       # hover surface
    selected: str = "#1D3A2E"    # selected row (green-tinted)
    border: str = "#334155"
    border_strong: str = "#475569"

    text: str = "#F8FAFC"        # body text  (contrast ~15:1 on bg)
    text_muted: str = "#94A3B8"  # secondary (contrast ~7:1 on bg)
    text_faint: str = "#64748B"

    accent: str = "#22C55E"      # primary action / success
    accent_hover: str = "#16A34A"
    accent_press: str = "#15803D"
    accent_text: str = "#052E16"  # text on top of accent

    info: str = "#38BDF8"
    warn: str = "#FBBF24"
    danger: str = "#F87171"


PALETTE = Palette()

# Spacing scale (px). Never invent off-scale values.
SPACE_XS, SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL = 4, 8, 12, 16, 24

# Corner radii: controls are tight, cards are softer (hierarchy, not uniformity).
RADIUS_CONTROL, RADIUS_CARD, RADIUS_PILL = 6, 8, 4

FONT_UI = '"Segoe UI", "Inter", "Noto Sans", system-ui, sans-serif'
FONT_MONO = '"JetBrains Mono", "Fira Code", "Consolas", monospace'

# Canvas palette.
CANVAS_BG = "#0A0F1A"
MASK_RGBA = (248, 113, 113, 96)  # translucent red mask overlay
