"""QA panel: overall verdict + per-metric rows (design §2 ui/widgets).

State is shown with an icon **and** a text label, never colour alone. Numbers use
the monospace token (design system: "Dashboard Data") so values align and are
easy to scan.
"""
from __future__ import annotations

from typing import Any, Dict

from PySide6 import QtCore, QtGui, QtWidgets

from photoai.ui import icons, theme

_COLUMNS = ["Chỉ số", "Giá trị", "Ngưỡng", "Kết quả"]


class QaPanel(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("QaPanel")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD)
        layout.setSpacing(theme.SPACE_SM)

        self._verdict = QtWidgets.QLabel("Chưa có kết quả")
        self._verdict.setObjectName("QaVerdict")
        self._verdict.setWordWrap(True)
        layout.addWidget(self._verdict)

        self._summary = QtWidgets.QLabel("Chạy một chức năng để xem chỉ số chất lượng.")
        self._summary.setProperty("role", "caption")
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)

        self._table = QtWidgets.QTreeWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHeaderLabels(_COLUMNS)
        self._table.setRootIsDecorated(False)
        self._table.setAlternatingRowColors(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        header = self._table.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for column in range(1, len(_COLUMNS)):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table, stretch=1)

        self._mono = QtGui.QFont()
        self._mono.setFamilies(["JetBrains Mono", "Fira Code", "Consolas", "monospace"])

    # --- public API -------------------------------------------------------
    def clear_report(self) -> None:
        self._table.clear()
        self._verdict.setText("Chưa có kết quả")
        self._paint_verdict(None)
        self._summary.setText("Chạy một chức năng để xem chỉ số chất lượng.")

    def show_report(self, metrics: Dict[str, Any], thresholds: Dict[str, Any], passed: bool) -> None:
        self._table.clear()

        checks: list[tuple[str, Any, Any, bool]] = []
        for key, threshold in thresholds.items():
            if threshold is None:
                continue
            name, value, ok = self._evaluate(key, threshold, metrics)
            checks.append((name, value, threshold, ok))

        self._paint_verdict(passed)
        n_pass = sum(1 for *_, ok in checks if ok)
        if passed:
            self._summary.setText(f"Đạt toàn bộ {len(checks)} chỉ số bắt buộc.")
        else:
            failed = [name for name, *_ , ok in checks if not ok]
            self._summary.setText(
                f"Đạt {n_pass}/{len(checks)} chỉ số · chưa đạt: {', '.join(failed) or '—'}"
            )

        for name, value, threshold, ok in checks:
            item = QtWidgets.QTreeWidgetItem(
                [
                    name,
                    "—" if value is None else self._format(value),
                    self._format(threshold),
                    "Đạt" if ok else "Chưa đạt",
                ]
            )
            item.setIcon(3, icons.icon("check" if ok else "cross", theme.PALETTE.accent if ok else theme.PALETTE.danger, 16))
            item.setFont(1, self._mono)
            item.setFont(2, self._mono)
            item.setForeground(3, QtGui.QColor(theme.PALETTE.accent if ok else theme.PALETTE.danger))
            item.setToolTip(0, self._explain(name))
            self._table.addTopLevelItem(item)

    # --- helpers ----------------------------------------------------------
    def _paint_verdict(self, passed: bool | None) -> None:
        if passed is None:
            self._verdict.setText("Chưa có kết quả")
            self._verdict.setStyleSheet(
                f"color:{theme.PALETTE.text_muted};background:{theme.PALETTE.elevated};"
                f"border:1px solid {theme.PALETTE.border};border-radius:{theme.RADIUS_CARD}px;"
                f"padding:10px 12px;font-weight:600;"
            )
            return
        tone = theme.PALETTE.accent if passed else theme.PALETTE.warn
        text = "Đạt yêu cầu chất lượng" if passed else "Chưa đạt — đã trả về bản an toàn"
        self._verdict.setText(text)
        self._verdict.setStyleSheet(
            f"color:{tone};background:{theme.PALETTE.elevated};"
            f"border:1px solid {theme.PALETTE.border};border-left:3px solid {tone};"
            f"border-radius:{theme.RADIUS_CARD}px;padding:10px 12px;font-weight:600;"
        )

    @staticmethod
    def _evaluate(key: str, threshold: Any, metrics: Dict[str, Any]) -> tuple[str, Any, bool]:
        if key.endswith("_min"):
            name = key[: -len("_min")]
            value = metrics.get(name)
            return name, value, value is not None and value >= threshold
        if key.endswith("_max"):
            name = key[: -len("_max")]
            value = metrics.get(name)
            return name, value, value is not None and value <= threshold
        value = metrics.get(key)
        return key, value, bool(value)

    @staticmethod
    def _format(value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        if isinstance(value, bool):
            return "có" if value else "không"
        return str(value)

    @staticmethod
    def _explain(name: str) -> str:
        return {
            "identity_cosine": "Độ tương đồng nhận dạng khuôn mặt so với ảnh gốc (1.0 = giữ nguyên).",
            "outside_mask_ssim": "Vùng ngoài mask phải gần như không đổi (bảo vệ pixel gốc).",
            "structure_similarity": "Tương đồng cấu trúc/khuôn hình (chống méo bố cục).",
            "clip_ratio": "Tỉ lệ pixel bị cháy sáng/đen — càng thấp càng tốt.",
            "delta_e_skin": "Chênh lệch màu da (CIE76 ΔE) so với ảnh gốc.",
            "texture_variance": "Phương sai kết cấu da (chống hiệu ứng 'da nhựa').",
            "ear": "Độ mở mắt (Eye Aspect Ratio) sau khi xử lý.",
            "ocr_recheck": "Kiểm tra lại còn chữ/watermark trong ảnh hay không.",
            "person_recheck": "Kiểm tra lại còn người hậu cảnh hay không.",
            "product_pixel_diff": "Tỉ lệ pixel sản phẩm bị thay đổi (phải bằng 0).",
        }.get(name, name)
