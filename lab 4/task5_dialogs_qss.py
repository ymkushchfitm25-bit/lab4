"""Завдання 5. Діалогові вікна та стилізація через Qt Style Sheets.

Записник контактів:
  * стандартні діалоги: QMessageBox (підтвердження видалення), QFileDialog (експорт);
  * діалог введення: QInputDialog.getItem (зміна групи) та getText (підпис записника);
  * власний модальний ContactDialog(QDialog), що повертає дані до головного вікна.
QSS завантажується з файлу styles.qss. Пункт меню «Вигляд → Стилізація QSS»
(Ctrl+T) вмикає й вимикає стилі, щоб порівняти «до» і «після».
"""

import re
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

GROUPS = ["Родина", "Друзі", "Робота", "Навчання"]
QSS_PATH = Path(__file__).with_name("styles.qss")

# Резервний мінімальний стиль, якщо styles.qss не знайдено
FALLBACK_QSS = """
QPushButton { background: #3949ab; color: white; border-radius: 6px; padding: 6px 14px; }
QPushButton:hover { background: #5c6bc0; }
QLineEdit:focus { border: 2px solid #3949ab; }
"""

PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{8,16}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_stylesheet() -> str:
    """Читає QSS з файлу styles.qss поруч зі скриптом (або повертає резервний)."""
    try:
        return QSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_QSS


def contact_title(contact: dict) -> str:
    """Текст рядка списку для контакту."""
    star = "★ " if contact["favorite"] else ""
    return f"{star}{contact['name']}  ·  {contact['phone']}  ·  [{contact['group']}]"


# ================================================= власний модальний діалог
class ContactDialog(QDialog):
    """Модальний діалог створення контакту з валідацією полів."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новий контакт")
        self.setModal(True)
        self.setMinimumWidth(380)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ім'я та прізвище")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+380 67 123 45 67")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("name@example.com (необов'язково)")
        self.group_combo = QComboBox()
        self.group_combo.addItems(GROUPS)
        self.favorite_check = QCheckBox("Додати в обране")

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")  # окремий стиль у QSS
        self.error_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Ім'я*:", self.name_edit)
        form.addRow("Телефон*:", self.phone_edit)
        form.addRow("E-mail:", self.email_edit)
        form.addRow("Група:", self.group_combo)
        form.addRow("", self.favorite_check)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Зберегти")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def validate(self) -> list[str]:
        """Перевіряє поля діалогу; повертає список помилок."""
        errors = []
        if len(self.name_edit.text().strip()) < 2:
            errors.append("Ім'я має містити щонайменше 2 символи.")
        if not PHONE_RE.match(self.phone_edit.text().strip()):
            errors.append("Телефон має містити 9–17 цифр, напр. +380671234567.")
        email = self.email_edit.text().strip()
        if email and not EMAIL_RE.match(email):
            errors.append("Некоректний e-mail.")
        return errors

    def accept(self) -> None:
        """Закриває діалог лише якщо дані коректні."""
        errors = self.validate()
        if errors:
            self.error_label.setText("\n".join(errors))
            return
        super().accept()

    def get_data(self) -> dict:
        """Повертає введені дані (викликається після exec())."""
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "group": self.group_combo.currentText(),
            "favorite": self.favorite_check.isChecked(),
        }


# ============================================================ головне вікно
class ContactBookWindow(QMainWindow):
    """Головне вікно записника контактів."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Записник контактів — діалоги та QSS")
        self.resize(640, 480)
        self.setMinimumSize(520, 400)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.title_label = QLabel("Мої контакти")
        self.title_label.setObjectName("titleLabel")  # окремий стиль у QSS
        layout.addWidget(self.title_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Пошук за ім'ям або телефоном…")
        self.search_edit.setClearButtonEnabled(True)
        layout.addWidget(self.search_edit)

        self.contact_list = QListWidget()
        layout.addWidget(self.contact_list, 1)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Додати контакт…")
        self.add_button.setObjectName("primaryButton")
        self.group_button = QPushButton("Змінити групу…")
        self.delete_button = QPushButton("Видалити")
        self.delete_button.setObjectName("dangerButton")
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.group_button)
        buttons.addStretch()
        buttons.addWidget(self.delete_button)
        layout.addLayout(buttons)

        self._create_menu()

        self.add_button.clicked.connect(self.add_contact)
        self.group_button.clicked.connect(self.change_group)
        self.delete_button.clicked.connect(self.delete_contact)
        self.search_edit.textChanged.connect(self.apply_filter)
        self.contact_list.currentItemChanged.connect(self.update_buttons)
        self.contact_list.itemDoubleClicked.connect(self.show_contact)

        for contact in (
            {"name": "Олена Шевченко", "phone": "+380671234567", "email": "olena@example.com", "group": "Навчання", "favorite": True},
            {"name": "Іван Коваль", "phone": "+380501112233", "email": "", "group": "Друзі", "favorite": False},
        ):
            self._add_item(contact)
        self.update_buttons()
        self.statusBar().showMessage("Подвійний клік — деталі контакту; Ctrl+T — увімкнути/вимкнути стилі")

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&Файл")
        export_action = QAction("&Експорт у файл…", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_contacts)
        rename_action = QAction("&Підпис записника…", self)
        rename_action.triggered.connect(self.rename_book)
        exit_action = QAction("В&ихід", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addActions([export_action, rename_action])
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("&Вигляд")
        self.style_action = QAction("&Стилізація QSS", self)
        self.style_action.setCheckable(True)
        self.style_action.setChecked(True)
        self.style_action.setShortcut(QKeySequence("Ctrl+T"))
        self.style_action.toggled.connect(self.set_styling)
        view_menu.addAction(self.style_action)

    # ------------------------------------------------------------- допоміжне
    def _add_item(self, contact: dict) -> QListWidgetItem:
        item = QListWidgetItem(contact_title(contact))
        item.setData(Qt.ItemDataRole.UserRole, contact)
        self.contact_list.addItem(item)
        return item

    def _contacts(self) -> list[dict]:
        return [self.contact_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.contact_list.count())]

    @pyqtSlot()
    def update_buttons(self) -> None:
        """Кнопки дій активні лише коли є виділений контакт (видно стиль :disabled)."""
        has_selection = self.contact_list.currentItem() is not None
        self.delete_button.setEnabled(has_selection)
        self.group_button.setEnabled(has_selection)

    def set_styling(self, enabled: bool) -> None:
        """Застосовує або знімає глобальний stylesheet."""
        QApplication.instance().setStyleSheet(load_stylesheet() if enabled else "")
        self.statusBar().showMessage(f"QSS {'увімкнено' if enabled else 'вимкнено'}", 3000)

    # ---------------------------------------------------------------- діалоги
    def add_contact(self) -> None:
        """Власний модальний діалог -> дані повертаються в головне вікно."""
        dialog = ContactDialog(self)
        if dialog.exec():  # 1 (Accepted) — натиснуто «Зберегти» і дані валідні
            contact = dialog.get_data()
            item = self._add_item(contact)
            self.contact_list.setCurrentItem(item)
            self.statusBar().showMessage(f"Додано контакт: {contact['name']}", 4000)
        else:
            self.statusBar().showMessage("Додавання скасовано", 3000)

    def change_group(self) -> None:
        """QInputDialog.getItem — вибір групи зі списку."""
        item = self.contact_list.currentItem()
        if item is None:
            return
        contact = dict(item.data(Qt.ItemDataRole.UserRole))
        group, ok = QInputDialog.getItem(
            self, "Змінити групу", f"Група для «{contact['name']}»:", GROUPS, GROUPS.index(contact["group"]), False
        )
        if ok and group != contact["group"]:
            contact["group"] = group
            item.setData(Qt.ItemDataRole.UserRole, contact)
            item.setText(contact_title(contact))
            self.statusBar().showMessage(f"{contact['name']} → група «{group}»", 4000)

    def rename_book(self) -> None:
        """QInputDialog.getText — введення тексту."""
        text, ok = QInputDialog.getText(self, "Підпис записника", "Новий заголовок:", text=self.title_label.text())
        if ok and text.strip():
            self.title_label.setText(text.strip())

    def delete_contact(self) -> None:
        """QMessageBox.question — підтвердження небезпечної дії."""
        item = self.contact_list.currentItem()
        if item is None:
            return
        name = item.data(Qt.ItemDataRole.UserRole)["name"]
        answer = QMessageBox.question(
            self,
            "Підтвердження",
            f"Видалити контакт «{name}»?\nЦю дію не можна скасувати.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.contact_list.takeItem(self.contact_list.row(item))
            self.statusBar().showMessage(f"Видалено: {name}", 4000)
        self.update_buttons()

    def export_contacts(self) -> None:
        """QFileDialog.getSaveFileName — експорт у текстовий файл."""
        path, _ = QFileDialog.getSaveFileName(self, "Експорт контактів", "contacts.txt", "Текстові файли (*.txt)")
        if not path:
            return
        lines = [f"{c['name']};{c['phone']};{c['email']};{c['group']}" for c in self._contacts()]
        try:
            Path(path).write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти файл:\n{exc}")
            return
        self.statusBar().showMessage(f"Експортовано {len(lines)} контакт(ів) у {path}", 5000)

    def show_contact(self, item: QListWidgetItem) -> None:
        c = item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(
            self, c["name"], f"Телефон: {c['phone']}\nE-mail: {c['email'] or '—'}\nГрупа: {c['group']}"
        )

    def apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            c = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(bool(needle) and needle not in c["name"].lower() and needle not in c["phone"])


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())
    window = ContactBookWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
