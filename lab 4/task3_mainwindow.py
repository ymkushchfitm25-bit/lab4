"""Завдання 3. Текстовий редактор на основі QMainWindow.

Стандартна схема QMainWindow: menuBar + QToolBar + centralWidget (QPlainTextEdit)
+ statusBar. Меню «Файл», «Правка», «Довідка» з QAction та гарячими клавішами,
стандартні діалоги QFileDialog і QMessageBox.
"""

import sys
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QStyle,
    QToolBar,
)

FILE_FILTER = "Текстові файли (*.txt *.md *.py);;Усі файли (*)"


class NotepadWindow(QMainWindow):
    """Простий блокнот."""

    def __init__(self) -> None:
        super().__init__()
        self.current_path: Path | None = None
        self.resize(800, 560)
        self.setMinimumSize(480, 320)

        # Центральний віджет
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Почніть вводити текст або відкрийте файл (Ctrl+O)…")
        self.setCentralWidget(self.editor)

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()

        self.editor.textChanged.connect(self.update_counters)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.editor.document().modificationChanged.connect(self.setWindowModified)
        self.editor.undoAvailable.connect(self.undo_action.setEnabled)
        self.editor.redoAvailable.connect(self.redo_action.setEnabled)

        self.update_title()
        self.update_counters()
        self.update_cursor_position()

    # ------------------------------------------------------------- побудова
    def _make_action(
        self,
        text: str,
        slot: Callable[..., object],
        shortcut: str | None = None,
        icon: QStyle.StandardPixmap | None = None,
        tip: str = "",
    ) -> QAction:
        """Створює QAction з гарячою клавішею, іконкою та підказкою для рядка стану."""
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(self.style().standardIcon(icon))
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if tip:
            action.setStatusTip(tip)  # показується в statusBar при наведенні
        action.triggered.connect(slot)
        return action

    def _create_actions(self) -> None:
        sp = QStyle.StandardPixmap
        self.new_action = self._make_action("&Новий", self.new_file, "Ctrl+N", sp.SP_FileIcon, "Створити новий документ")
        self.open_action = self._make_action("&Відкрити…", self.open_file, "Ctrl+O", sp.SP_DialogOpenButton, "Відкрити текстовий файл")
        self.save_action = self._make_action("&Зберегти", self.save_file, "Ctrl+S", sp.SP_DialogSaveButton, "Зберегти документ")
        self.save_as_action = self._make_action("Зберегти &як…", self.save_file_as, "Ctrl+Shift+S", None, "Зберегти під іншим іменем")
        self.exit_action = self._make_action("В&ихід", self.close, "Ctrl+Q", sp.SP_DialogCloseButton, "Закрити програму")

        self.undo_action = self._make_action("&Скасувати", self.editor.undo, "Ctrl+Z", sp.SP_ArrowBack, "Скасувати останню дію")
        self.redo_action = self._make_action("&Повторити", self.editor.redo, "Ctrl+Y", sp.SP_ArrowForward, "Повторити скасовану дію")
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)
        self.clear_action = self._make_action("&Очистити все", self.clear_text, None, sp.SP_TrashIcon, "Видалити весь текст")
        self.wrap_action = self._make_action("&Перенесення рядків", self.toggle_wrap, None, None, "Увімкнути/вимкнути перенесення")
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)

        self.about_action = self._make_action("&Про програму", self.show_about, "F1", sp.SP_MessageBoxInformation, "Інформація про програму")
        self.about_qt_action = self._make_action("Про &Qt", lambda: QMessageBox.aboutQt(self), None, None, "Інформація про Qt")

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&Файл")
        file_menu.addActions([self.new_action, self.open_action, self.save_action, self.save_as_action])
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = self.menuBar().addMenu("&Правка")
        edit_menu.addActions([self.undo_action, self.redo_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.clear_action, self.wrap_action])

        help_menu = self.menuBar().addMenu("&Довідка")
        help_menu.addActions([self.about_action, self.about_qt_action])

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Основна панель")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        # Ті самі QAction, що й у меню, — один обробник для обох місць
        toolbar.addActions([self.new_action, self.open_action, self.save_action])
        toolbar.addSeparator()
        toolbar.addActions([self.undo_action, self.redo_action])
        toolbar.addSeparator()
        toolbar.addAction(self.about_action)

    def _create_status_bar(self) -> None:
        self.position_label = QLabel()
        self.counter_label = QLabel()
        self.statusBar().addPermanentWidget(self.position_label)
        self.statusBar().addPermanentWidget(self.counter_label)
        self.statusBar().showMessage("Готово", 3000)

    # ------------------------------------------------------ оновлення стану
    def update_title(self) -> None:
        """Заголовок з ім'ям файлу; [*] Qt замінює на «*» при незбережених змінах."""
        name = self.current_path.name if self.current_path else "Без назви"
        self.setWindowTitle(f"{name}[*] — Блокнот")

    def update_counters(self) -> None:
        text = self.editor.toPlainText()
        self.counter_label.setText(
            f"Символів: {len(text)} | Слів: {len(text.split())} | Рядків: {self.editor.blockCount()}"
        )

    def update_cursor_position(self) -> None:
        cursor = self.editor.textCursor()
        self.position_label.setText(f"Рядок {cursor.blockNumber() + 1}, стовп. {cursor.positionInBlock() + 1}")

    def _set_document(self, text: str, path: Path | None) -> None:
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.current_path = path
        self.update_title()

    # ------------------------------------------------------------- дії меню
    def maybe_save(self) -> bool:
        """Питає про збереження незбережених змін. False — користувач скасував дію."""
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(
            self,
            "Незбережені зміни",
            "Документ змінено. Зберегти зміни?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save_file()
        return answer == QMessageBox.StandardButton.Discard

    def new_file(self) -> None:
        if self.maybe_save():
            self._set_document("", None)
            self.statusBar().showMessage("Створено новий документ", 3000)

    def open_file(self) -> None:
        if not self.maybe_save():
            return
        path_str, _ = QFileDialog.getOpenFileName(self, "Відкрити файл", "", FILE_FILTER)
        if not path_str:
            self.statusBar().showMessage("Відкриття скасовано", 3000)
            return
        path = Path(path_str)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            QMessageBox.critical(self, "Помилка", f"Не вдалося відкрити файл:\n{exc}")
            return
        self._set_document(text, path)
        self.statusBar().showMessage(f"Відкрито: {path.name} ({len(text)} символів)", 5000)

    def save_file(self) -> bool:
        if self.current_path is None:
            return self.save_file_as()
        return self._write(self.current_path)

    def save_file_as(self) -> bool:
        path_str, _ = QFileDialog.getSaveFileName(self, "Зберегти як", "документ.txt", FILE_FILTER)
        if not path_str:
            self.statusBar().showMessage("Збереження скасовано", 3000)
            return False
        return self._write(Path(path_str))

    def _write(self, path: Path) -> bool:
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти файл:\n{exc}")
            return False
        self.current_path = path
        self.editor.document().setModified(False)
        self.update_title()
        self.statusBar().showMessage(f"Збережено: {path}", 5000)
        return True

    def clear_text(self) -> None:
        # Видаляємо через курсор (а не clear()), щоб дію можна було скасувати Ctrl+Z
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.removeSelectedText()
        self.statusBar().showMessage("Текст очищено (Ctrl+Z — повернути)", 3000)

    def toggle_wrap(self, checked: bool) -> None:
        mode = QPlainTextEdit.LineWrapMode.WidgetWidth if checked else QPlainTextEdit.LineWrapMode.NoWrap
        self.editor.setLineWrapMode(mode)
        self.statusBar().showMessage(f"Перенесення рядків {'увімкнено' if checked else 'вимкнено'}", 3000)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "Про програму",
            "<h3>Блокнот</h3><p>Лабораторна робота №4, завдання 3.</p>"
            "<p>QMainWindow: меню, панель інструментів, рядок стану.</p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (ім'я з Qt)
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()


def main() -> None:
    app = QApplication(sys.argv)
    window = NotepadWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
