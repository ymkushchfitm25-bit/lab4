"""Завдання 4. Кастомні сигнали та взаємодія компонентів.

Менеджер задач з трьох незалежних компонентів (підкласів QWidget):

    TaskInputPanel --taskSubmitted(str, int)--> TaskListPanel
    TaskListPanel  --tasksChanged(list)-------> StatsPanel
    TaskListPanel  --taskSelected(str)--------> StatsPanel

Компоненти не знають один про одного. Усі з'єднання створює головне вікно
TaskManagerWindow, тому будь-який компонент можна замінити іншим з тими самими
сигналами та слотами.
"""

import sys
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

DEMO_TASKS: list[tuple[str, int]] = [
    ("Підготувати звіт з лаби 4", 5),
    ("Прочитати розділ про сигнали", 3),
    ("Зробити скріншоти", 4),
    ("Купити каву", 1),
    ("Повторити QSS", 2),
]


# =========================================================== компонент 1
class TaskInputPanel(QWidget):
    """Компонент введення: збирає назву та пріоритет нової задачі."""

    #: Користувач підтвердив нову задачу: (назва, пріоритет 1..5).
    taskSubmitted = pyqtSignal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Нова задача…")
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(3)
        self.priority_spin.setPrefix("P")
        self.priority_spin.setToolTip("Пріоритет: 1 — низький, 5 — найвищий")
        self.add_button = QPushButton("Додати")
        layout.addWidget(self.title_edit, 1)
        layout.addWidget(self.priority_spin)
        layout.addWidget(self.add_button)

        # Внутрішні з'єднання — лише з ВЛАСНИМИ дочірніми віджетами
        self.add_button.clicked.connect(self._submit)
        self.title_edit.returnPressed.connect(self._submit)

    @pyqtSlot()
    def _submit(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            self.title_edit.setPlaceholderText("Назва не може бути порожньою!")
            return
        self.taskSubmitted.emit(title, self.priority_spin.value())
        self.title_edit.clear()
        self.title_edit.setPlaceholderText("Нова задача…")
        self.title_edit.setFocus()


# =========================================================== компонент 2
class TaskListPanel(QWidget):
    """Компонент списку: зберігає задачі й повідомляє про зміни."""

    #: Змінився склад або стан задач: список словників {"title", "priority", "done"}.
    tasksChanged = pyqtSignal(list)
    #: Користувач виділив задачу: її назва.
    taskSelected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.list_widget = QListWidget()
        self.remove_button = QPushButton("Видалити виділену")
        self.clear_button = QPushButton("Очистити все")
        buttons = QHBoxLayout()
        buttons.addWidget(self.remove_button)
        buttons.addWidget(self.clear_button)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(buttons)

        self.list_widget.itemChanged.connect(self.notify_changed)  # зміна прапорця «виконано»
        self.list_widget.currentItemChanged.connect(self._on_current_changed)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear_tasks)

    @pyqtSlot(str, int)
    def add_task(self, title: str, priority: int) -> None:
        """Слот: додає задачу та випромінює tasksChanged."""
        item = QListWidgetItem(f"[P{priority}] {title}")
        item.setData(Qt.ItemDataRole.UserRole, {"title": title, "priority": priority})
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)  # до addItem — щоб не було itemChanged
        self.list_widget.addItem(item)
        self.notify_changed()

    @pyqtSlot()
    def remove_selected(self) -> None:
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)
            self.notify_changed()

    @pyqtSlot()
    def clear_tasks(self) -> None:
        self.list_widget.clear()
        self.notify_changed()
        self.taskSelected.emit("")

    def tasks(self) -> list[dict]:
        """Повертає поточні задачі як список словників."""
        result = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            data = dict(item.data(Qt.ItemDataRole.UserRole))
            data["done"] = item.checkState() == Qt.CheckState.Checked
            result.append(data)
        return result

    @pyqtSlot()
    def notify_changed(self) -> None:
        """Випромінює tasksChanged з актуальним списком задач."""
        self.tasksChanged.emit(self.tasks())

    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        title = current.data(Qt.ItemDataRole.UserRole)["title"] if current else ""
        self.taskSelected.emit(title)


# =========================================================== компонент 3
class StatsPanel(QWidget):
    """Компонент відображення: статистика по задачах."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.total_label = QLabel()
        self.priority_label = QLabel()
        self.selected_label = QLabel()
        self.selected_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setFormat("Виконано %v з %m")
        for widget in (self.total_label, self.priority_label, self.progress, self.selected_label):
            layout.addWidget(widget)
        self.update_stats([])
        self.show_selected("")

    @pyqtSlot(list)
    def update_stats(self, tasks: list) -> None:
        """Слот: перераховує статистику за списком задач."""
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        urgent = sum(1 for t in tasks if t["priority"] >= 4 and not t["done"])
        avg = sum(t["priority"] for t in tasks) / total if total else 0
        self.total_label.setText(f"Усього задач: {total}")
        self.priority_label.setText(f"Термінових (P4–P5) невиконаних: {urgent} | середній пріоритет: {avg:.1f}")
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done)

    @pyqtSlot(str)
    def show_selected(self, title: str) -> None:
        """Слот: показує назву виділеної задачі."""
        self.selected_label.setText(f"Виділено: {title}" if title else "Виділено: —")


# ======================================================== головне вікно
class TaskManagerWindow(QWidget):
    """Батьківський віджет: створює компоненти та з'єднує їх сигнали."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Менеджер задач — кастомні сигнали")
        self.setMinimumSize(820, 520)
        self.emit_counter = 0
        self.tasks_changed_count = 0
        self._stats_connected = False

        self.input_panel = TaskInputPanel()
        self.list_panel = TaskListPanel()
        self.stats_panel = StatsPanel()

        self.sync_check = QCheckBox("Синхронізувати статистику (connect / disconnect)")
        self.sync_check.setChecked(True)
        self.block_check = QCheckBox("Блокувати сигнали під час пакетного завантаження (blockSignals)")
        self.block_check.setChecked(True)
        self.demo_button = QPushButton(f"Завантажити {len(DEMO_TASKS)} демо-задач")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Тут з'являтиметься кожне випромінення кастомного сигналу")

        self._build_layout()
        self._wire_components()

    def _build_layout(self) -> None:
        left = QGroupBox("Задачі")
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self.input_panel)
        left_layout.addWidget(self.list_panel, 1)

        stats_box = QGroupBox("Статистика")
        QVBoxLayout(stats_box).addWidget(self.stats_panel)

        controls = QGroupBox("Керування сигналами")
        controls_layout = QVBoxLayout(controls)
        controls_layout.addWidget(self.sync_check)
        controls_layout.addWidget(self.block_check)
        controls_layout.addWidget(self.demo_button)

        log_box = QGroupBox("Журнал сигналів")
        QVBoxLayout(log_box).addWidget(self.log)

        right = QVBoxLayout()
        right.addWidget(stats_box)
        right.addWidget(controls)
        right.addWidget(log_box, 1)

        root = QHBoxLayout(self)
        root.addWidget(left, 1)
        root.addLayout(right, 1)

    def _wire_components(self) -> None:
        """Усі міжкомпонентні з'єднання — тут, а не всередині компонентів."""
        self.input_panel.taskSubmitted.connect(self.list_panel.add_task)
        self.list_panel.taskSelected.connect(self.stats_panel.show_selected)
        self.set_stats_sync(True)

        # Журнал: показує, які сигнали і скільки разів були випромінені
        self.input_panel.taskSubmitted.connect(
            lambda title, prio: self.write_log(f"taskSubmitted('{title}', {prio})")
        )
        self.list_panel.tasksChanged.connect(self._log_tasks_changed)
        self.list_panel.taskSelected.connect(
            lambda title: self.write_log(f"taskSelected('{title}')") if title else None
        )

        self.sync_check.toggled.connect(self.set_stats_sync)
        self.demo_button.clicked.connect(self.load_demo_tasks)

    @pyqtSlot(list)
    def _log_tasks_changed(self, tasks: list) -> None:
        self.tasks_changed_count += 1
        self.write_log(f"tasksChanged(list з {len(tasks)} задач)")

    def write_log(self, text: str) -> None:
        self.emit_counter += 1
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log.appendPlainText(f"{self.emit_counter:>3}. {stamp}  {text}")

    @pyqtSlot(bool)
    def set_stats_sync(self, enabled: bool) -> None:
        """Підключає або від'єднує (disconnect) статистику від списку задач."""
        if enabled and not self._stats_connected:
            self.list_panel.tasksChanged.connect(self.stats_panel.update_stats)
            self._stats_connected = True
            self.stats_panel.update_stats(self.list_panel.tasks())  # наздогнати зміни
            self.write_log("connect: tasksChanged -> StatsPanel.update_stats")
        elif not enabled and self._stats_connected:
            self.list_panel.tasksChanged.disconnect(self.stats_panel.update_stats)
            self._stats_connected = False
            self.write_log("DISCONNECT: статистика більше не оновлюється")

    @pyqtSlot()
    def load_demo_tasks(self) -> None:
        """Пакетне додавання задач з blockSignals або без нього.

        Без блокування кожна add_task() випромінює tasksChanged, тобто буде 5
        каскадних оновлень статистики. З блокуванням сигнали під час циклу
        пригнічуються, а після нього випромінюється рівно одне tasksChanged.
        """
        block = self.block_check.isChecked()
        before = self.tasks_changed_count
        self.write_log(f"--- пакетне завантаження, blockSignals={block} ---")
        if block:
            self.list_panel.blockSignals(True)
        try:
            for title, priority in DEMO_TASKS:
                self.list_panel.add_task(title, priority)
        finally:
            if block:
                self.list_panel.blockSignals(False)
                self.list_panel.notify_changed()  # одне підсумкове оновлення
        emitted = self.tasks_changed_count - before
        self.write_log(f"--- готово: tasksChanged випромінено {emitted} раз(и) ---")


def main() -> None:
    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
