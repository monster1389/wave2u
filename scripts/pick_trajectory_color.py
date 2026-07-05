"""
取色工具 v2：显示截图全貌，输出指定坐标的 HSV 值。

用法：
    1. 运行后截图保存
    2. 打开 docs/images/debug_pick_v2.png
    3. 找到轨迹线上的一点，告诉我坐标
    4. 我告诉你那个点的 HSV
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import pyautogui

from src.config import FX, FY, FW, FH

print("=" * 50)
print("取色工具 v2")
print("=" * 50)
print("\n5秒后在游戏中显示轨迹线...")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

s = pyautogui.screenshot()
frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
cv2.imwrite("docs/images/debug_pick_v2.png", frame)

# 网格内所有像素的 HSV
roi = frame[FY:FY+FH, FX:FX+FW]
hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

print(f"\n截图已保存: docs/images/debug_pick_v2.png ({frame.shape[1]}x{frame.shape[0]})")
print(f"\n请告诉我轨迹线上任意一点的坐标 (x,y)")
print(f"例如: '轨迹线在 (950, 850)'")
print(f"或者直接说轨迹线是什么颜色的\n")

# 同时输出网格内所有非方块颜色的像素
# 计算网格平均值作为背景参考
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
mean_brightness = np.mean(gray)
print(f"网格平均亮度: {mean_brightness:.0f}")

# 找出亮度明显高于平均的像素（轨迹线应该是亮色的）
bright_mask = gray > (mean_brightness + 40)
bright_coords = np.where(bright_mask)
if len(bright_coords[0]) > 0:
    bright_hsv = hsv[bright_coords]
    print(f"\n亮色像素统计 (比平均亮+40以上, {len(bright_coords[0])}个):")
    print(f"  H: {bright_hsv[:,0].min():3d}~{bright_hsv[:,0].max():3d}  均值={bright_hsv[:,0].mean():.0f}")
    print(f"  S: {bright_hsv[:,1].min():3d}~{bright_hsv[:,1].max():3d}  均值={bright_hsv[:,1].mean():.0f}")
    print(f"  V: {bright_hsv[:,2].min():3d}~{bright_hsv[:,2].max():3d}  均值={bright_hsv[:,2].mean():.0f}")
else:
    print(f"\n没有明显亮色像素")
