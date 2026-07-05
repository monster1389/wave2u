"""
取色工具：在截图上点击轨迹线，查看 HSV 值。
用于校准轨迹线颜色范围。

用法：
    1. 运行后 5 秒内让游戏显示轨迹线
    2. 截图会保存为 docs/images/debug_pick_color.png
    3. 查看图片，在轨迹线上找几个点的坐标
    4. 脚本会输出这些坐标的 HSV 值
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
print("轨迹线颜色取色工具")
print("=" * 50)
print("\n请在 5 秒内让游戏显示轨迹线...")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print("截图！")

s = pyautogui.screenshot()
frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
cv2.imwrite("docs/images/debug_pick_color.png", frame)
print(f"\n截图已保存: docs/images/debug_pick_color.png")
print(f"分辨率: {frame.shape[1]}x{frame.shape[0]}")
print(f"网格区域: ({FX},{FY})-({FX+FW},{FY+FH})")

# 分析网格区域内所有像素的 HSV 分布
roi = frame[FY:FY+FH, FX:FX+FW]
hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

# 在几个网格区域采样
print("\n在网格区域采样 HSV（从底部到顶部共 5 行）:")
for row_pct in [0.9, 0.7, 0.5, 0.3, 0.1]:
    y = int(FY + FH * row_pct)
    for col_pct in [0.3, 0.5, 0.7]:
        x = int(FX + FW * col_pct)
        b, g, r = frame[y, x].tolist()
        h, s, v = hsv[y - FY, x - FX].tolist()
        print(f"  位置 ({x:4d},{y:4d})  BGR=({b:3d},{g:3d},{r:3d})  HSV=({h:3d},{s:3d},{v:3d})")

# 找到网格区域中饱和度适中、亮度高的蓝色调像素（可能是轨迹线）
print("\n分析网格内可能的轨迹线颜色（蓝色调、高亮度）:")
mask_cyan = cv2.inRange(hsv, np.array([70, 10, 100]), np.array([130, 200, 255]))
cyan_pixels = np.where(mask_cyan > 0)
if len(cyan_pixels[0]) > 0:
    # 取这些像素的 HSV 统计
    h_vals = hsv[cyan_pixels][:, 0]
    s_vals = hsv[cyan_pixels][:, 1]
    v_vals = hsv[cyan_pixels][:, 2]
    print(f"  H: min={h_vals.min()} max={h_vals.max()} mean={h_vals.mean():.0f}")
    print(f"  S: min={s_vals.min()} max={s_vals.max()} mean={s_vals.mean():.0f}")
    print(f"  V: min={v_vals.min()} max={v_vals.max()} mean={v_vals.mean():.0f}")

    # 尝试画一下所有匹配的像素
    debug = frame.copy()
    debug_roi = debug[FY:FY+FH, FX:FX+FW]
    debug_roi[mask_cyan > 0] = (0, 255, 255)  # 画成黄色
    cv2.imwrite("docs/images/debug_cyan_mask.png", debug)
    print(f"\n青色掩码覆盖图: docs/images/debug_cyan_mask.png")
    print("（黄色高亮部分=匹配 HSV [70,10,100]-[130,200,255] 的像素）")
else:
    print("  网格内没有找到蓝色调像素！")

print("\n请打开 docs/images/debug_pick_color.png")
print("在轨迹线上找几个点，告诉我它们的坐标，我来算 HSV")
