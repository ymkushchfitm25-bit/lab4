"""Завдання 1. Вікно додатка з базовими віджетами та вкладеними layouts.

Анкета студента: 10 типів віджетів, розміщених лише через менеджери
компонування (QVBoxLayout, QHBoxLayout, QFormLayout) без move(x, y).
"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ProfileWindow(QWidget):
    """Головне вікно з анкетою студента."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Анкета студента — базові віджети PyQt6")
        self.setMinimumSize(560, 620)
        self._build_ui()

    def _build_ui(self) -> None:
        # Кореневий layout: усе вікно — вертикальна колонка
        root = QVBoxLayout(self)
        root.setSpacing(10)

        # QLabel — заголовок
        title = QLabel("Анкета студента курсу «Python»")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        root.addWidget(title)

        # --- Група 1: особисті дані (QFormLayout, вкладений у QVBoxLayout) ---
        personal_box = QGroupBox("Особисті дані")
        form = QFormLayout(personal_box)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Прізвище та ім'я, напр. Шевченко Олена")
        self.name_edit.setMaxLength(60)
        self.name_edit.setClearButtonEnabled(True)

        self.group_combo = QComboBox()
        self.group_combo.addItems(["КІ-21", "КІ-22", "ПІ-21", "ПІ-22"])
        self.group_combo.setCurrentIndex(1)
        self.group_combo.setToolTip("Оберіть свою академічну групу")

        self.age_spin = QSpinBox()
        self.age_spin.setRange(16, 60)
        self.age_spin.setValue(19)
        self.age_spin.setSuffix(" р.")
        self.age_spin.setToolTip("Допустимий вік: від 16 до 60 років")

        form.addRow("ПІБ:", self.name_edit)
        form.addRow("Група:", self.group_combo)
        form.addRow("Вік:", self.age_spin)
        root.addWidget(personal_box)

        # --- Група 2: форма навчання (QHBoxLayout з радіокнопками) ---
        study_box = QGroupBox("Форма навчання")
        study_row = QHBoxLayout(study_box)
        self.full_time_radio = QRadioButton("Денна")
        self.full_time_radio.setChecked(True)
        self.part_time_radio = QRadioButton("Заочна")
        self.remote_radio = QRadioButton("Дистанційна")
        self.remote_radio.setEnabled(False)
        self.remote_radio.setToolTip("Набір на дистанційну форму тимчасово закрито")
        for radio in (self.full_time_radio, self.part_time_radio, self.remote_radio):
            study_row.addWidget(radio)
        study_row.addStretch()
        root.addWidget(study_box)

        # --- Група 3: рівень знань (QHBoxLayout вкладений у QVBoxLayout групи) ---
        skill_box = QGroupBox("Рівень володіння Python")
        skill_layout = QVBoxLayout(skill_box)

        slider_row = QHBoxLayout()
        self.skill_slider = QSlider(Qt.Orientation.Horizontal)
        self.skill_slider.setRange(0, 10)
        self.skill_slider.setValue(5)
        self.skill_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.skill_slider.setTickInterval(1)
        self.skill_slider.setToolTip("0 — новачок, 10 — експерт")
        slider_row.addWidget(QLabel("0"))
        slider_row.addWidget(self.skill_slider, 1)  # stretch: повзунок розтягується
        slider_row.addWidget(QLabel("10"))
        skill_layout.addLayout(slider_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(40)
        self.progress.setFormat("Анкету заповнено на %p%")
        skill_layout.addWidget(self.progress)
        root.addWidget(skill_box)

        # --- Коментар: QTextEdit забирає весь вільний простір по вертикалі ---
        root.addWidget(QLabel("Коментар:"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Чого ви очікуєте від курсу? (необов'язково)")
        self.comment_edit.setAcceptRichText(False)
        root.addWidget(self.comment_edit, 1)

        self.agree_check = QCheckBox("Погоджуюсь на обробку персональних даних")
        self.agree_check.setToolTip("Без згоди анкету не можна надіслати")
        root.addWidget(self.agree_check)

        # --- Рядок кнопок (QHBoxLayout), притиснутий праворуч ---
        buttons_row = QHBoxLayout()
        buttons_row.addStretch()
        self.clear_button = QPushButton("Очистити")
        self.clear_button.setToolTip("Очистити всі поля анкети")
        self.send_button = QPushButton("Надіслати")
        self.send_button.setEnabled(False)
        self.send_button.setToolTip("Стане активною після підтвердження згоди")
        buttons_row.addWidget(self.clear_button)
        buttons_row.addWidget(self.send_button)
        root.addLayout(buttons_row)


def main() -> None:
    app = QApplication(sys.argv)
    window = ProfileWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
