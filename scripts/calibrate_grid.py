"""
Grid calibration tool.
Click top-left corner of the grid, then bottom-right corner.
Saves coordinates to grid_config.json.
"""

import sys
import json
import os

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "grid_config.json")


class Calibrator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Calibration")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        self.setGeometry(0, 0, 2240, 1400)

        self.top_left = None
        self.bottom_right = None
        self.mouse_pos = None
        self.step = 1  # 1=click TL, 2=click BR

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(33)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            if self.step == 1:
                self.top_left = (x, y)
                self.step = 2
                self.update()
            elif self.step == 2:
                self.bottom_right = (x, y)
                self._save_and_exit()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_pos = (event.x(), event.y())

    def _save_and_exit(self):
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        if x2 <= x1 or y2 <= y1:
            print(f"Error: bottom-right must be below and right of top-left")
            print(f"  TL=({x1},{y1}) BR=({x2},{y2})")
            QApplication.quit()
            return

        fw, fh = x2 - x1, y2 - y1
        config = {"fx": x1, "fy": y1, "fw": fw, "fh": fh}

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)

        print(f"Grid config saved to {CONFIG_PATH}")
        print(f"  Top-left:  ({x1}, {y1})")
        print(f"  Bottom-right: ({x2}, {y2})")
        print(f"  Size: {fw}x{fh}")
        QApplication.quit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # dim background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))

        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)

        if self.step == 1:
            painter.drawText(100, 100, "Step 1: Click the TOP-LEFT corner of the grid")
            if self.mouse_pos:
                mx, my = self.mouse_pos
                painter.setPen(QColor(255, 255, 0))
                painter.drawLine(mx - 20, my, mx + 20, my)
                painter.drawLine(mx, my - 20, mx, my + 20)
        elif self.step == 2:
            painter.drawText(100, 100, "Step 2: Click the BOTTOM-RIGHT corner of the grid")
            x1, y1 = self.top_left
            painter.setPen(QColor(0, 255, 0))
            painter.drawRect(x1 - 3, y1 - 3, 6, 6)
            if self.mouse_pos:
                mx, my = self.mouse_pos
                painter.setPen(QColor(0, 255, 0, 120))
                painter.drawRect(x1, y1, mx - x1, my - y1)

        painter.end()


def main():
    app = QApplication(sys.argv)
    w = Calibrator()
    w.show()
    print("Grid Calibration Tool")
    print("=====================")
    print("Step 1: Click the TOP-LEFT corner of the 6x8 grid")
    print("Step 2: Click the BOTTOM-RIGHT corner of the 6x8 grid")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
