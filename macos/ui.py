from __future__ import annotations

import subprocess
from pathlib import Path

from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
)

from hotkey import HotkeyError, parse_hotkey
from settings import AppSettings, ensure_writable_directory


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: AppSettings,
        issues: tuple[str, ...] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)

        self._hotkey_edit = QKeySequenceEdit(QKeySequence(settings.hotkey))
        self._path_edit = QLineEdit(settings.save_dir)
        self._hotkey_checkbox = QCheckBox("启用快捷键截屏")
        self._hotkey_checkbox.setChecked(settings.hotkey_enabled)
        self._hotkey_edit.setEnabled(settings.hotkey_enabled)
        self._hotkey_checkbox.toggled.connect(self._hotkey_edit.setEnabled)
        self._mouse_checkbox = QCheckBox("启用鼠标左键长按截屏")
        self._mouse_checkbox.setChecked(settings.mouse_capture_enabled)
        self._hold_seconds = QDoubleSpinBox()
        self._hold_seconds.setRange(0.1, 3600)
        self._hold_seconds.setDecimals(2)
        self._hold_seconds.setSingleStep(0.1)
        self._hold_seconds.setSuffix(" 秒")
        self._hold_seconds.setValue(settings.mouse_hold_seconds)
        self._hold_seconds.setEnabled(settings.mouse_capture_enabled)
        self._mouse_checkbox.toggled.connect(self._hold_seconds.setEnabled)
        # macOS 26 + Qt 6.11 下 QLabel 开启 wordWrap 后在固定宽度对话框中
        # 中文会以错误字形渲染（已实测复现，显式指定字体也无法绕开），
        # 因此保持单行、由对话框自适应宽度。
        self._hint = QLabel("在输入框中直接按下想要的组合键即可。")
        self._hint.setStyleSheet("color: #666;")
        self._status_label = QLabel("；".join(issues) if issues else "运行正常")
        self._result: AppSettings | None = None

        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._choose_directory)

        path_row = QHBoxLayout()
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse_button)

        form = QFormLayout()
        form.addRow("运行状态", self._status_label)
        form.addRow("快捷键截屏", self._hotkey_checkbox)
        form.addRow("快捷键", self._hotkey_edit)
        form.addRow("鼠标截屏", self._mouse_checkbox)
        form.addRow("长按时长", self._hold_seconds)
        form.addRow("", QLabel("达到时长自动截屏，每次按住只截一次；长按也会影响当前应用。"))
        form.addRow("保存路径", path_row)
        form.addRow("", self._hint)

        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(actions)

    @property
    def result_settings(self) -> AppSettings | None:
        return self._result

    def _choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            self._path_edit.text() or str(Path.home()),
        )
        if directory:
            self._path_edit.setText(directory)

    def _save(self) -> None:
        hotkey = self._hotkey_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        if self._hotkey_checkbox.isChecked() and not hotkey:
            self._show_error("请先设置截图快捷键。")
            return

        try:
            if self._hotkey_checkbox.isChecked():
                parse_hotkey(hotkey)
            save_dir = ensure_writable_directory(self._path_edit.text().strip())
        except (HotkeyError, ValueError) as exc:
            self._show_error(str(exc))
            return

        self._result = AppSettings(
            hotkey=hotkey,
            save_dir=str(save_dir),
            hotkey_enabled=self._hotkey_checkbox.isChecked(),
            mouse_capture_enabled=self._mouse_checkbox.isChecked(),
            mouse_hold_seconds=self._hold_seconds.value(),
        )
        self.accept()

    def _show_error(self, message: str) -> None:
        self._status_label.setText(f"设置无效：{message}")


class TrayController:
    def __init__(self, icon: QIcon | None = None, parent=None) -> None:
        self.tray = QSystemTrayIcon(parent)
        self.tray.setIcon(icon or QIcon())
        self.tray.setToolTip("Silent Screen")
        self.menu = QMenu()

        self.settings_action = QAction("设置")
        self.open_folder_action = QAction("打开截图目录")
        self.open_log_action = QAction("打开日志")
        self.quit_action = QAction("退出")

        self.menu.addAction(self.settings_action)
        self.menu.addSeparator()
        self.menu.addAction(self.open_folder_action)
        self.menu.addAction(self.open_log_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)

    def show(self) -> None:
        self.tray.show()

    @staticmethod
    def open_path(path: str) -> None:
        subprocess.Popen(["open", str(path)])
