"""Ownership confirmation dialog (design §2 ui/widgets).

The confirm button stays disabled until the user actively ticks the declaration,
and the dialog explains *why* consent is required instead of just demanding it.
"""
from __future__ import annotations

from PySide6 import QtWidgets

from photoai.ui import theme


class WatermarkDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Xác nhận quyền sở hữu")
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(theme.SPACE_XL, theme.SPACE_XL, theme.SPACE_XL, theme.SPACE_XL)
        layout.setSpacing(theme.SPACE_MD)

        heading = QtWidgets.QLabel("Trước khi xóa watermark")
        heading.setProperty("role", "h2")
        layout.addWidget(heading)

        body = QtWidgets.QLabel(
            "Chỉ xóa watermark/logo trên ảnh mà bạn sở hữu hoặc có quyền chỉnh sửa. "
            "Hành động này được ghi vào nhật ký (audit log) của ứng dụng."
        )
        body.setWordWrap(True)
        body.setProperty("role", "caption")
        layout.addWidget(body)

        self._check = QtWidgets.QCheckBox("Tôi xác nhận có quyền hợp pháp với ảnh này")
        layout.addWidget(self._check)

        hint = QtWidgets.QLabel("Không thể tiếp tục nếu chưa xác nhận.")
        hint.setProperty("role", "faint")
        layout.addWidget(hint)

        layout.addSpacing(theme.SPACE_SM)

        buttons = QtWidgets.QDialogButtonBox()
        self._confirm = buttons.addButton("Xác nhận và tiếp tục", QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self._confirm.setObjectName("PrimaryButton")
        cancel = buttons.addButton("Hủy", QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        cancel.setObjectName("GhostButton")
        layout.addWidget(buttons)

        self._confirm.setEnabled(False)
        self._check.toggled.connect(self._confirm.setEnabled)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._check.setFocus()

    def confirmed(self) -> bool:
        return self._check.isChecked()
