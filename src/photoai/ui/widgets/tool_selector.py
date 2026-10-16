"""Sidebar: the ten functions as selectable cards with rich metadata (design §2 ui/widgets)."""
from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from photoai.ui import icons, theme

# (recipe_id, Vietnamese title, Vietnamese subtitle, English label)
RECIPE_ITEMS: list[tuple[str, str, str, str]] = [
    ("upscale_4k", "Nâng cấp 4K", "Siêu phân giải & sắc nét", "4K Upscale"),
    ("skin_retouch", "Retouch da", "Làm mịn & bảo tồn vân da", "Skin Retouch"),
    ("chin_fix", "Sửa nọng cằm", "Liquify TPS định hình cằm", "Chin Fix"),
    ("open_eyes", "Cứu ảnh nhắm mắt", "Ghép mắt mở tự nhiên", "Open Eyes"),
    ("remove_watermark", "Xóa watermark", "Xóa logo & chữ bản quyền", "Remove Watermark"),
    ("remove_bystanders", "Xóa người hậu cảnh", "Inpainting xóa vật thể thừa", "Remove Bystanders"),
    ("restore_old_photo", "Phục chế ảnh cũ", "Khử nhiễu & phục hồi chi tiết", "Restore Old Photo"),
    ("golden_hour", "Chân dung giờ vàng", "Tông ấm hoàng hôn nghệ thuật", "Golden Hour"),
    ("low_light_fix", "Sửa ảnh thiếu sáng", "Cân bằng sáng & tương phản", "Low Light Fix"),
    ("product_studio", "Điện thoại → Studio", "Chiếu sáng thương mại cao cấp", "Phone → Studio"),
]

# Keep RECIPE_LABELS for backwards compatibility if referenced
RECIPE_LABELS: list[tuple[str, str, str]] = [
    (item[0], item[1], item[3]) for item in RECIPE_ITEMS
]


class ToolCardDelegate(QtWidgets.QStyledItemDelegate):
    """Custom card delegate rendering rich title, subtitle, icon, and index badge."""

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
        return QtCore.QSize(option.rect.width(), 54)

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        rect = option.rect.adjusted(2, 2, -2, -2)
        is_selected = bool(option.state & QtWidgets.QStyle.StateFlag.State_Selected)
        is_hover = bool(option.state & QtWidgets.QStyle.StateFlag.State_MouseOver)

        # Card surface and border
        if is_selected:
            bg_color = QtGui.QColor("#1D3A2E")
            border_color = QtGui.QColor("#22C55E")
            sub_color = QtGui.QColor("#34D399")
        elif is_hover:
            bg_color = QtGui.QColor("#243449")
            border_color = QtGui.QColor("#475569")
            sub_color = QtGui.QColor(theme.PALETTE.text_muted)
        else:
            bg_color = QtGui.QColor("#1E293B")
            border_color = QtGui.QColor("#334155")
            sub_color = QtGui.QColor(theme.PALETTE.text_faint)

        painter.setBrush(bg_color)
        painter.setPen(QtGui.QPen(border_color, 1))
        painter.drawRoundedRect(rect, 6, 6)

        # Left accent line indicator when selected
        if is_selected:
            accent_bar = QtCore.QRectF(rect.left(), rect.top() + 8, 3.5, rect.height() - 16)
            painter.fillRect(accent_bar, QtGui.QColor("#22C55E"))

        # Icon
        recipe_id = str(index.data(QtCore.Qt.ItemDataRole.UserRole) or "")
        icon_name = icons.TOOL_ICONS.get(recipe_id, "sparkle")
        icon_color = "#22C55E" if is_selected else theme.PALETTE.text_muted
        icon_pm = icons.pixmap(icon_name, icon_color, 20)
        icon_x = rect.left() + 12
        icon_y = rect.top() + (rect.height() - 20) // 2
        painter.drawPixmap(icon_x, icon_y, icon_pm)

        # Text labels
        title = str(index.data(QtCore.Qt.ItemDataRole.DisplayRole) or "")
        subtitle = str(index.data(QtCore.Qt.ItemDataRole.UserRole + 1) or "")
        badge_num = str(index.data(QtCore.Qt.ItemDataRole.UserRole + 2) or "")

        # Title
        font_title = painter.font()
        font_title.setPointSizeF(9.5)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(QtGui.QColor("#F8FAFC" if is_selected else "#E2E8F0"))
        title_rect = QtCore.QRectF(rect.left() + 40, rect.top() + 8, rect.width() - 76, 18)
        painter.drawText(title_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, title)

        # Subtitle
        font_sub = painter.font()
        font_sub.setPointSizeF(8.2)
        font_sub.setBold(False)
        painter.setFont(font_sub)
        painter.setPen(sub_color)
        sub_rect = QtCore.QRectF(rect.left() + 40, rect.top() + 27, rect.width() - 76, 16)
        painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, subtitle)

        # Badge index number (e.g. 01, 02)
        font_badge = QtGui.QFont("JetBrains Mono")
        font_badge.setPointSizeF(8.0)
        font_badge.setBold(True)
        painter.setFont(font_badge)
        painter.setPen(QtGui.QColor("#22C55E" if is_selected else "#64748B"))
        badge_rect = QtCore.QRectF(rect.right() - 32, rect.top() + 8, 24, 16)
        painter.drawText(badge_rect, QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter, badge_num)

        painter.restore()


class ToolSelector(QtWidgets.QListWidget):
    """Single-select list of the ten functions with modern card presentation."""

    recipe_selected = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ToolSelector")
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setItemDelegate(ToolCardDelegate(self))

        for index, (recipe_id, label_vi, subtitle_vi, label_en) in enumerate(RECIPE_ITEMS, start=1):
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.ItemDataRole.DisplayRole, label_vi)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, recipe_id)
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, subtitle_vi)
            item.setData(QtCore.Qt.ItemDataRole.UserRole + 2, f"{index:02d}")
            item.setToolTip(f"{label_vi} ({label_en})\n{subtitle_vi}")
            self.addItem(item)

        self.setCurrentRow(0)
        self.currentItemChanged.connect(self._on_change)

    def current_recipe_id(self) -> str:
        item = self.currentItem()
        if item is None:
            return ""
        return str(item.data(QtCore.Qt.ItemDataRole.UserRole))

    def _on_change(self, current: QtWidgets.QListWidgetItem | None, _previous) -> None:
        if current is not None:
            self.recipe_selected.emit(str(current.data(QtCore.Qt.ItemDataRole.UserRole)))
