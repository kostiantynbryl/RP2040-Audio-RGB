from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

STYLE = """
QWidget{background:#090b10;color:#e8edf7;font-family:'Segoe UI';font-size:10pt}
QMainWindow{background:#07090d}
QTabWidget::pane{border:1px solid #1c2430;border-radius:12px;background:#0c1017}
QTabBar::tab{padding:10px 16px;background:#0b0f15;border-radius:8px;margin:2px}
QTabBar::tab:selected{background:#182334}
QGroupBox{border:1px solid #1b2634;border-radius:12px;margin-top:10px;padding:12px;font-weight:600}
QPushButton{background:#172235;border:1px solid #263a55;border-radius:9px;padding:8px 12px}
QPushButton:hover{background:#21324d}
QLineEdit,QComboBox,QSpinBox,QTextEdit,QTableWidget{background:#0f1620;border:1px solid #263548;border-radius:8px;padding:6px}
QSlider::groove:horizontal{height:5px;background:#1f2b3a;border-radius:2px}
QSlider::handle:horizontal{width:16px;margin:-6px 0;background:#e8edf7;border-radius:8px}
QProgressBar{border:1px solid #263548;border-radius:7px;background:#0f1620;text-align:center}
QProgressBar::chunk{background:#477fff;border-radius:6px}
"""


class Spectrum(QWidget):
    def __init__(self):
        super().__init__()
        self.values = [0.0] * 32
        self.setMinimumHeight(170)

    def set_values(self, values):
        self.values = list(values)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width() / max(1, len(self.values))
        height = self.height()
        for index, value in enumerate(self.values):
            value = max(0.0, min(1.0, value))
            y = height * (1.0 - value)
            painter.fillRect(int(index * width + 2), int(y), max(1, int(width - 4)), int(height - y), QColor(72, 127, 255))


def status_card(title, value):
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    label = QLabel(value)
    label.setStyleSheet("font-size:17pt;font-weight:700")
    layout.addWidget(label)
    return box, label
