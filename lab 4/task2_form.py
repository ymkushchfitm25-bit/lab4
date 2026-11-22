"""Завдання 2. Інтерактивна форма: сигнали, слоти, валідація та скидання.

Форма запису на курс. Дії користувача одразу змінюють інші віджети,
а валідація винесена в окрему функцію validate_form().
"""

import sys
from functools import partial

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PLACEHOLDER_COURSE = "— оберіть курс —"
COURSES: dict[str, str] = {
    "Python Basic": "8 тижнів, основи мови. Підходить для початківців.",
    "Python Advanced": "10 тижнів: ООП, генератори, асинхронність.",
    "Django": "12 тижнів, веб-розробка. Потрібен рівень Python від 3.",
    "Data Science": "14 тижнів: pandas, NumPy, візуалізація даних.",
}
LEVELS: dict[int, str] = {1: "новачок", 2: "початковий", 3: "середній", 4: "впевнений", 5: "експерт"}
NAME_MAX_LEN = 40
AGE_MIN, AGE_MAX = 16, 60

# Початковий стан форми — використовується при створенні та скиданні
INITIAL_STATE = {"name": "", "age": 18, "course_index": 0, "level": 3, "agreed": False}


def validate_form(name: str, age: int, course: str, agreed: bool) -> list[str]:
    """Перевіряє дані форми. Єдине місце, де описані правила валідації.

    Args:
        name: Введене ім'я.
        age: Вік.
        course: Назва обраного курсу.
        agreed: Чи погодився користувач з умовами.

    Returns:
        Список повідомлень про помилки (порожній, якщо дані коректні).
    """
    errors: list[str] = []
    clean_name = name.strip()
    if not clean_name:
        errors.append("Ім'я не може бути порожнім.")
    elif len(clean_name) < 2:
        errors.append("Ім'я має містити щонайменше 2 символи.")
    elif not all(ch.isalpha() or ch in " '-ʼ" for ch in clean_name):
        errors.append("Ім'я може містити лише літери, пробіл, апостроф і дефіс.")
    if not AGE_MIN <= age <= AGE_MAX:
        errors.append(f"Вік має бути від {AGE_MIN} до {AGE_MAX} років (зараз {age}).")
    if course not in COURSES:
        errors.append("Оберіть курс зі списку.")
    if not agreed:
        errors.append("Потрібно погодитися з умовами навчання.")
    return errors


def show_course_info(info_label: QLabel, course: str) -> None:
    """Звичайна функція-слот (не метод класу): показує опис курсу в мітці."""
    info_label.setText(COURSES.get(course, "Курс ще не обрано."))


class RegistrationForm(QWidget):
    """Форма запису на курс."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Запис на курс — сигнали та слоти")
        self.setMinimumSize(520, 420)
        self._build_ui()
        self._connect_signals()
        self.reset_form()

    # ------------------------------------------------------------ інтерфейс
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        form = QFormLayout()

        # Текст
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ваше ім'я")
        self.name_edit.setMaxLength(NAME_MAX_LEN)
        self.name_counter = QLabel()
        self.name_counter.setMinimumWidth(50)
        name_row.addWidget(self.name_edit, 1)
        name_row.addWidget(self.name_counter)
        form.addRow("Ім'я:", name_row)

        # Число (діапазон спіна ширший за допустимий — щоб валідація мала сенс)
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setSuffix(" р.")
        form.addRow("Вік:", self.age_spin)

        # Вибір зі списку
        self.course_combo = QComboBox()
        self.course_combo.addItem(PLACEHOLDER_COURSE)
        self.course_combo.addItems(list(COURSES))
        form.addRow("Курс:", self.course_combo)
        self.course_info = QLabel()
        self.course_info.setWordWrap(True)
        form.addRow("", self.course_info)

        # Повзунок + мітка, яку він змінює
        level_row = QHBoxLayout()
        self.level_slider = QSlider(Qt.Orientation.Horizontal)
        self.level_slider.setRange(1, 5)
        self.level_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.level_label = QLabel()
        self.level_label.setMinimumWidth(130)
        level_row.addWidget(self.level_slider, 1)
        level_row.addWidget(self.level_label)
        form.addRow("Рівень Python:", level_row)

        # Прапорець
        self.agree_check = QCheckBox("Погоджуюсь з умовами навчання")
        form.addRow("", self.agree_check)
        root.addLayout(form)

        # Кнопки
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.reset_button = QPushButton("Скинути")
        self.submit_button = QPushButton("Записатися")
        self.submit_button.setDefault(True)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.submit_button)
        root.addLayout(buttons)

        # Результат валідації
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        root.addWidget(self.result_label)
        root.addStretch()

    def _connect_signals(self) -> None:
        # З'єднання 1: вбудований сигнал textChanged -> ЛЯМБДА (лічильник символів)
        self.name_edit.textChanged.connect(
            lambda text: self.name_counter.setText(f"{len(text)}/{NAME_MAX_LEN}")
        )
        # З'єднання 2: currentTextChanged -> ЗВИЧАЙНА ФУНКЦІЯ show_course_info
        # (partial «прив'язує» мітку, у яку треба писати)
        self.course_combo.currentTextChanged.connect(partial(show_course_info, self.course_info))
        # З'єднання 3: valueChanged повзунка -> метод, що змінює текст ІНШОГО віджета (мітки)
        self.level_slider.valueChanged.connect(self.update_level_label)
        # З'єднання 4: toggled прапорця -> setEnabled кнопки (властивість іншого віджета)
        self.agree_check.toggled.connect(self.submit_button.setEnabled)
        # З'єднання 5–6: clicked кнопок -> методи-слоти
        self.submit_button.clicked.connect(self.submit)
        self.reset_button.clicked.connect(self.reset_form)
        # З'єднання 7: будь-яка зміна імені прибирає старе повідомлення
        self.name_edit.textEdited.connect(self.clear_result)

    # ---------------------------------------------------------------- слоти
    @pyqtSlot(int)
    def update_level_label(self, value: int) -> None:
        """Оновлює мітку рівня при переміщенні повзунка."""
        self.level_label.setText(f"{value} — {LEVELS.get(value, '?')}")

    @pyqtSlot()
    def clear_result(self) -> None:
        """Прибирає повідомлення та підсвітку помилки."""
        self.result_label.clear()
        self.name_edit.setStyleSheet("")

    @pyqtSlot()
    def submit(self) -> None:
        """Перевіряє форму через validate_form() і показує результат."""
        errors = validate_form(
            self.name_edit.text(),
            self.age_spin.value(),
            self.course_combo.currentText(),
            self.agree_check.isChecked(),
        )
        if errors:
            self.result_label.setStyleSheet("color: #b00020;")
            self.result_label.setText("Помилки:\n• " + "\n• ".join(errors))
            if any("Ім'я" in e for e in errors):
                self.name_edit.setStyleSheet("border: 1px solid #b00020;")
            return
        self.clear_result()
        self.result_label.setStyleSheet("color: #1b5e20;")
        self.result_label.setText("Дані коректні, заявку прийнято.")
        QMessageBox.information(
            self,
            "Заявку прийнято",
            f"{self.name_edit.text().strip()}, вас записано на курс "
            f"«{self.course_combo.currentText()}».\n"
            f"Вік: {self.age_spin.value()}, рівень: {self.level_label.text()}.",
        )

    @pyqtSlot()
    def reset_form(self) -> None:
        """Повертає всі поля до початкового стану INITIAL_STATE."""
        self.name_edit.setText(INITIAL_STATE["name"])
        self.age_spin.setValue(INITIAL_STATE["age"])
        self.course_combo.setCurrentIndex(INITIAL_STATE["course_index"])
        self.level_slider.setValue(INITIAL_STATE["level"])
        self.agree_check.setChecked(INITIAL_STATE["agreed"])
        # Сигнали спрацьовують лише при ЗМІНІ значення, тож залежні віджети
        # оновлюємо явно, щоб стан був правильним і при першому запуску.
        self.update_level_label(self.level_slider.value())
        show_course_info(self.course_info, self.course_combo.currentText())
        self.name_counter.setText(f"0/{NAME_MAX_LEN}")
        self.submit_button.setEnabled(self.agree_check.isChecked())
        self.clear_result()
        self.name_edit.setFocus()


def main() -> None:
    app = QApplication(sys.argv)
    window = RegistrationForm()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
