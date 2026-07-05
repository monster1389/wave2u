"""QPainter 渲染器：绘制网格、方块、预判线"""

from typing import List, Optional, Tuple
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QPointF

from src.config import FX, FY, FW, FH, GRID_COLS, GRID_ROWS


class Renderer:
    """在覆盖层上绘制所有可视元素"""

    def __init__(self):
        self.grid_rect = (FX, FY, FW, FH)
        self.blocks: List[dict] = []
        self.launch_point: Optional[Tuple[int, int]] = None
        self.trajectory: List[Tuple[int, int]] = []
        self.mouse_pos: Optional[Tuple[int, int]] = None
        self.is_dragging = False
        self.endpoint: Optional[Tuple[int, int]] = None
        self.status_text = "Ready"
        self.status_color = QColor(0, 200, 0)

    def draw(self, painter: QPainter, win_w: int, win_h: int):
        """主绘制方法"""
        painter.setRenderHint(QPainter.Antialiasing)

        # 淡色背景：让覆盖层可见
        painter.fillRect(0, 0, win_w, win_h, QColor(0, 0, 0, 25))

        self._draw_grid(painter)
        self._draw_blocks(painter)
        if self.launch_point:
            self._draw_launch_point(painter)
        if self.mouse_pos and self.is_dragging and self.launch_point:
            self._draw_direction_line(painter)
        if self.trajectory:
            self._draw_trajectory(painter)
        if self.endpoint:
            self._draw_endpoint(painter)
        self._draw_status(painter, win_w, win_h)
        if not self.trajectory and not self.is_dragging:
            self._draw_hint(painter, win_w, win_h)

    def _draw_grid(self, painter: QPainter):
        """绘制网格轮廓"""
        gx, gy, gw, gh = self.grid_rect
        pen = QPen(QColor(180, 180, 180, 120), 1)
        painter.setPen(pen)

        # 外框
        painter.drawRect(gx, gy, gw, gh)

        # 网格线
        cell_w = gw / GRID_COLS
        cell_h = gh / GRID_ROWS
        for c in range(1, GRID_COLS):
            x = int(c * cell_w) + gx
            painter.drawLine(x, gy, x, gy + gh)
        for r in range(1, GRID_ROWS):
            y = int(r * cell_h) + gy
            painter.drawLine(gx, y, gx + gw, y)

    def _draw_blocks(self, painter: QPainter):
        """绘制半透明方块覆盖层"""
        for blk in self.blocks:
            pen = QPen(QColor(0, 200, 0, 180), 2)
            brush = QBrush(QColor(0, 200, 0, 40))
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(blk["x"], blk["y"], blk["w"], blk["h"])

    def _draw_launch_point(self, painter: QPainter):
        """绘制发射点指示器"""
        x, y = self.launch_point
        pen = QPen(QColor(255, 255, 0, 200), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 0, 100)))
        painter.drawEllipse(QPointF(x, y), 6, 6)

    def _draw_direction_line(self, painter: QPainter):
        """绘制从发射点到鼠标的虚线方向指示"""
        lx, ly = self.launch_point
        mx, my = self.mouse_pos
        pen = QPen(QColor(200, 200, 200, 150), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(lx, ly, mx, my)

    def _draw_trajectory(self, painter: QPainter):
        """绘制预判线（青色，透明度逐段递减）"""
        if len(self.trajectory) < 2:
            return

        total_segments = len(self.trajectory) - 1
        for i in range(total_segments):
            x1, y1 = self.trajectory[i]
            x2, y2 = self.trajectory[i + 1]
            alpha = max(60, 255 - int(i / total_segments * 150))
            pen = QPen(QColor(0, 255, 255, alpha), 2)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)

    def _draw_endpoint(self, painter: QPainter):
        """绘制终点标记（黄色实心圆）"""
        x, y = self.endpoint
        pen = QPen(QColor(255, 255, 0, 220), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 0, 120)))
        painter.drawEllipse(QPointF(x, y), 8, 8)

    def _draw_status(self, painter: QPainter, win_w: int, win_h: int):
        """绘制状态文字（右下角）"""
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(self.status_color)
        painter.drawText(win_w - 120, win_h - 10, self.status_text)

    def _draw_hint(self, painter: QPainter, win_w: int, win_h: int):
        """绘制操作提示"""
        font = QFont("Arial", 14)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawText(win_w // 2 - 200, win_h // 2,
                         "在游戏中瞄准以查看预判轨迹")
