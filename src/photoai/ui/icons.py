"""Line icons drawn with QPainter (design §2 ui/).

Deliberately asset-free: the app is fully offline and the design system forbids
emoji-as-icons, so every glyph is a small vector path painted on demand and
cached. Colours come from :mod:`photoai.ui.theme`.
"""
from __future__ import annotations

from typing import Callable, Dict

from PySide6 import QtCore, QtGui

from . import theme

_DRAWERS: Dict[str, Callable[[QtGui.QPainter, float], None]] = {}
_CACHE: Dict[tuple, QtGui.QPixmap] = {}


def _register(name: str):
    def decorator(fn: Callable[[QtGui.QPainter, float], None]):
        _DRAWERS[name] = fn
        return fn

    return decorator


def _pt(size: float, fx: float, fy: float) -> QtCore.QPointF:
    return QtCore.QPointF(fx * size, fy * size)


def _line(p: QtGui.QPainter, size: float, x1: float, y1: float, x2: float, y2: float) -> None:
    p.drawLine(_pt(size, x1, y1), _pt(size, x2, y2))


# --- tool icons --------------------------------------------------------------
@_register("expand")
def _expand(p: QtGui.QPainter, s: float) -> None:
    c = 0.5
    for dx, dy in ((1, -1), (-1, 1), (1, 1), (-1, -1)):
        ax, ay = c + dx * 0.30, c + dy * 0.30
        p.drawLine(_pt(s, c, c), _pt(s, ax, ay))
        _line(p, s, ax, ay, ax - dx * 0.12, ay)
        _line(p, s, ax, ay, ax, ay - dy * 0.12)


@_register("sparkle")
def _sparkle(p: QtGui.QPainter, s: float) -> None:
    _line(p, s, 0.45, 0.18, 0.45, 0.62)
    _line(p, s, 0.28, 0.40, 0.62, 0.40)
    _line(p, s, 0.70, 0.55, 0.70, 0.80)
    _line(p, s, 0.575, 0.675, 0.825, 0.675)


@_register("profile")
def _profile(p: QtGui.QPainter, s: float) -> None:
    path = QtGui.QPainterPath()
    path.moveTo(_pt(s, 0.40, 0.82))
    path.lineTo(_pt(s, 0.40, 0.52))
    path.cubicTo(_pt(s, 0.40, 0.22), _pt(s, 0.72, 0.22), _pt(s, 0.72, 0.50))
    path.cubicTo(_pt(s, 0.72, 0.62), _pt(s, 0.60, 0.60), _pt(s, 0.60, 0.70))
    path.lineTo(_pt(s, 0.66, 0.82))
    p.drawPath(path)
    p.drawEllipse(_pt(s, 0.62, 0.42), s * 0.04, s * 0.04)


@_register("eye")
def _eye(p: QtGui.QPainter, s: float) -> None:
    path = QtGui.QPainterPath()
    path.moveTo(_pt(s, 0.16, 0.50))
    path.quadTo(_pt(s, 0.50, 0.20), _pt(s, 0.84, 0.50))
    path.quadTo(_pt(s, 0.50, 0.80), _pt(s, 0.16, 0.50))
    p.drawPath(path)
    p.drawEllipse(_pt(s, 0.50, 0.50), s * 0.11, s * 0.11)


@_register("tag-off")
def _tag_off(p: QtGui.QPainter, s: float) -> None:
    p.drawEllipse(_pt(s, 0.50, 0.50), s * 0.32, s * 0.32)
    _line(p, s, 0.28, 0.28, 0.72, 0.72)


@_register("users-off")
def _users_off(p: QtGui.QPainter, s: float) -> None:
    p.drawEllipse(_pt(s, 0.36, 0.36), s * 0.11, s * 0.11)
    path = QtGui.QPainterPath()
    path.moveTo(_pt(s, 0.16, 0.78))
    path.quadTo(_pt(s, 0.36, 0.54), _pt(s, 0.56, 0.78))
    p.drawPath(path)
    p.drawEllipse(_pt(s, 0.66, 0.40), s * 0.09, s * 0.09)
    _line(p, s, 0.30, 0.30, 0.82, 0.82)


@_register("history")
def _history(p: QtGui.QPainter, s: float) -> None:
    p.drawArc(QtCore.QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64), 60 * 16, 300 * 16)
    _line(p, s, 0.50, 0.32, 0.50, 0.52)
    _line(p, s, 0.50, 0.52, 0.64, 0.60)
    p.drawPolyline([_pt(s, 0.16, 0.30), _pt(s, 0.24, 0.30), _pt(s, 0.24, 0.38)])


@_register("sun")
def _sun(p: QtGui.QPainter, s: float) -> None:
    p.drawEllipse(_pt(s, 0.50, 0.50), s * 0.16, s * 0.16)
    for fx, fy in ((0.50, 0.12), (0.50, 0.88), (0.12, 0.50), (0.88, 0.50),
                   (0.24, 0.24), (0.76, 0.24), (0.24, 0.76), (0.76, 0.76)):
        dx, dy = fx - 0.50, fy - 0.50
        norm = (dx * dx + dy * dy) ** 0.5
        _line(p, s, 0.50 + dx / norm * 0.24, 0.50 + dy / norm * 0.24,
              0.50 + dx / norm * 0.34, 0.50 + dy / norm * 0.34)


@_register("moon")
def _moon(p: QtGui.QPainter, s: float) -> None:
    path = QtGui.QPainterPath()
    path.moveTo(_pt(s, 0.62, 0.16))
    path.arcTo(QtCore.QRectF(s * 0.16, s * 0.16, s * 0.68, s * 0.68), 70, 220)
    path.arcTo(QtCore.QRectF(s * 0.38, s * 0.16, s * 0.46, s * 0.68), 150, -220)
    p.drawPath(path)


@_register("box")
def _box(p: QtGui.QPainter, s: float) -> None:
    p.drawPolygon([_pt(s, 0.50, 0.16), _pt(s, 0.82, 0.33), _pt(s, 0.82, 0.67),
                   _pt(s, 0.50, 0.84), _pt(s, 0.18, 0.67), _pt(s, 0.18, 0.33)])
    _line(p, s, 0.18, 0.33, 0.50, 0.50)
    _line(p, s, 0.82, 0.33, 0.50, 0.50)
    _line(p, s, 0.50, 0.50, 0.50, 0.84)


# --- action icons ------------------------------------------------------------
@_register("folder")
def _folder(p: QtGui.QPainter, s: float) -> None:
    path = QtGui.QPainterPath()
    path.moveTo(_pt(s, 0.14, 0.74))
    path.lineTo(_pt(s, 0.14, 0.28))
    path.lineTo(_pt(s, 0.42, 0.28))
    path.lineTo(_pt(s, 0.50, 0.38))
    path.lineTo(_pt(s, 0.86, 0.38))
    path.lineTo(_pt(s, 0.86, 0.74))
    path.closeSubpath()
    p.drawPath(path)


@_register("play")
def _play(p: QtGui.QPainter, s: float) -> None:
    p.drawPolygon([_pt(s, 0.32, 0.22), _pt(s, 0.80, 0.50), _pt(s, 0.32, 0.78)])


@_register("save")
def _save(p: QtGui.QPainter, s: float) -> None:
    _line(p, s, 0.50, 0.18, 0.50, 0.60)
    p.drawPolyline([_pt(s, 0.34, 0.46), _pt(s, 0.50, 0.62), _pt(s, 0.66, 0.46)])
    _line(p, s, 0.22, 0.80, 0.78, 0.80)


@_register("fit")
def _fit(p: QtGui.QPainter, s: float) -> None:
    for ox, oy, dx, dy in ((0.18, 0.18, 1, 1), (0.82, 0.18, -1, 1),
                           (0.18, 0.82, 1, -1), (0.82, 0.82, -1, -1)):
        _line(p, s, ox, oy, ox + dx * 0.20, oy)
        _line(p, s, ox, oy, ox, oy + dy * 0.20)


@_register("zoom-in")
def _zoom_in(p: QtGui.QPainter, s: float) -> None:
    p.drawEllipse(_pt(s, 0.44, 0.44), s * 0.26, s * 0.26)
    _line(p, s, 0.64, 0.64, 0.84, 0.84)
    _line(p, s, 0.44, 0.32, 0.44, 0.56)
    _line(p, s, 0.32, 0.44, 0.56, 0.44)


@_register("zoom-out")
def _zoom_out(p: QtGui.QPainter, s: float) -> None:
    p.drawEllipse(_pt(s, 0.44, 0.44), s * 0.26, s * 0.26)
    _line(p, s, 0.64, 0.64, 0.84, 0.84)
    _line(p, s, 0.32, 0.44, 0.56, 0.44)


@_register("hand")
def _hand(p: QtGui.QPainter, s: float) -> None:
    p.drawPolyline([
        _pt(s, 0.30, 0.76),
        _pt(s, 0.30, 0.44),
        _pt(s, 0.38, 0.44),
        _pt(s, 0.38, 0.32),
        _pt(s, 0.46, 0.32),
        _pt(s, 0.46, 0.36),
        _pt(s, 0.54, 0.36),
        _pt(s, 0.54, 0.40),
        _pt(s, 0.62, 0.40),
        _pt(s, 0.62, 0.58),
        _pt(s, 0.54, 0.76),
        _pt(s, 0.30, 0.76),
    ])


@_register("brush")
def _brush(p: QtGui.QPainter, s: float) -> None:
    _line(p, s, 0.30, 0.70, 0.66, 0.34)
    p.drawEllipse(_pt(s, 0.28, 0.72), s * 0.09, s * 0.09)
    _line(p, s, 0.62, 0.30, 0.72, 0.40)



@_register("eraser")
def _eraser(p: QtGui.QPainter, s: float) -> None:
    p.drawPolygon([_pt(s, 0.24, 0.62), _pt(s, 0.52, 0.34), _pt(s, 0.74, 0.56),
                   _pt(s, 0.46, 0.84)])
    _line(p, s, 0.36, 0.50, 0.58, 0.72)


@_register("clear")
def _clear(p: QtGui.QPainter, s: float) -> None:
    p.drawEllipse(_pt(s, 0.50, 0.50), s * 0.32, s * 0.32)
    _line(p, s, 0.38, 0.38, 0.62, 0.62)
    _line(p, s, 0.62, 0.38, 0.38, 0.62)


@_register("check")
def _check(p: QtGui.QPainter, s: float) -> None:
    p.drawPolyline([_pt(s, 0.24, 0.52), _pt(s, 0.43, 0.70), _pt(s, 0.78, 0.32)])


@_register("cross")
def _cross(p: QtGui.QPainter, s: float) -> None:
    _line(p, s, 0.30, 0.30, 0.70, 0.70)
    _line(p, s, 0.70, 0.30, 0.30, 0.70)


@_register("image")
def _image(p: QtGui.QPainter, s: float) -> None:
    p.drawRoundedRect(QtCore.QRectF(s * 0.16, s * 0.22, s * 0.68, s * 0.56), s * 0.06, s * 0.06)
    p.drawEllipse(_pt(s, 0.34, 0.38), s * 0.04, s * 0.04)
    p.drawPolyline([_pt(s, 0.22, 0.72), _pt(s, 0.42, 0.50), _pt(s, 0.58, 0.66), _pt(s, 0.70, 0.56), _pt(s, 0.80, 0.70)])


@_register("cpu")
def _cpu(p: QtGui.QPainter, s: float) -> None:
    p.drawRoundedRect(QtCore.QRectF(s * 0.28, s * 0.28, s * 0.44, s * 0.44), s * 0.06, s * 0.06)
    p.drawRoundedRect(QtCore.QRectF(s * 0.42, s * 0.42, s * 0.16, s * 0.16), s * 0.03, s * 0.03)
    for f in (0.38, 0.50, 0.62):
        _line(p, s, f, 0.20, f, 0.28)
        _line(p, s, f, 0.72, f, 0.80)
        _line(p, s, 0.20, f, 0.28, f)
        _line(p, s, 0.72, f, 0.80, f)


# --- public API --------------------------------------------------------------
def pixmap(name: str, color: str | None = None, size: int = 20) -> QtGui.QPixmap:
    """Return a cached icon pixmap for ``name`` (transparent background)."""
    color = color or theme.PALETTE.text_muted
    key = (name, color, size)
    if key in _CACHE:
        return _CACHE[key]

    dpr = 2
    pm = QtGui.QPixmap(size * dpr, size * dpr)
    pm.setDevicePixelRatio(dpr)
    pm.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pm)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
    pen = QtGui.QPen(QtGui.QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

    drawer = _DRAWERS.get(name)
    if drawer is not None:
        drawer(painter, float(size))
    painter.end()

    _CACHE[key] = pm
    return pm


def icon(name: str, color: str | None = None, size: int = 20) -> QtGui.QIcon:
    """Return a cached :class:`QIcon` for ``name``."""
    return QtGui.QIcon(pixmap(name, color, size))


TOOL_ICONS = {
    "upscale_4k": "expand",
    "skin_retouch": "sparkle",
    "chin_fix": "profile",
    "open_eyes": "eye",
    "remove_watermark": "tag-off",
    "remove_bystanders": "users-off",
    "restore_old_photo": "history",
    "golden_hour": "sun",
    "low_light_fix": "moon",
    "product_studio": "box",
}
