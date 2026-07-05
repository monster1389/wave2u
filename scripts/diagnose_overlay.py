"""
诊断脚本：检查覆盖层各环节是否正常。

运行方式：
    .venv/Scripts/python scripts/diagnose_overlay.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

print("=" * 50)
print("NIKKE 覆盖层诊断")
print("=" * 50)

# 1. 检查窗口检测
print("\n[1/5] 窗口检测")
try:
    import pygetwindow as gw
    windows = gw.getWindowsWithTitle("NIKKE")
    visible = [w for w in windows if w.visible]
    print(f"  找到 {len(windows)} 个 'NIKKE' 标题的窗口, {len(visible)} 个可见")
    for w in windows[:5]:
        print(f"    - '{w.title}' visible={w.visible} pos=({w.left},{w.top}) size={w.width}x{w.height}")
except Exception as e:
    print(f"  ❌ 窗口检测失败: {e}")

# 2. 检查截图
print("\n[2/5] 截图")
try:
    import pyautogui
    from PIL import Image
    s = pyautogui.screenshot()
    print(f"  ✅ 截图成功: {s.size[0]}x{s.size[1]}")
except Exception as e:
    print(f"  ❌ 截图失败: {e}")

# 3. 检查检测模块
print("\n[3/5] 检测模块")
try:
    from src.config import FX, FY, FW, FH
    from src.detection.blocks import detect_blocks
    from src.detection.launch_point import detect_launch_point
    import cv2
    import numpy as np
    s = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
    blocks = detect_blocks(frame)
    print(f"  方块检测: {len(blocks)} 个方块")
    pt = detect_launch_point(frame)
    print(f"  发射点检测: {pt}")
except Exception as e:
    print(f"  ❌ 检测失败: {e}")

# 4. 检查物理模拟
print("\n[4/5] 物理模拟")
try:
    from src.physics.trajectory import simulate
    sx, sy = FX + FW // 2, FY + 5
    waypoints, reason, col, row = simulate(sx, sy, 0, 1, [])
    print(f"  ✅ 模拟成功: {len(waypoints)} 个路径点, reason={reason}")
except Exception as e:
    print(f"  ❌ 模拟失败: {e}")

# 5. 检查覆盖层能否创建
print("\n[5/5] 覆盖层窗口（需要桌面环境，仅创建不显示）")
try:
    from PyQt5.QtWidgets import QApplication
    # Don't create QApplication here - it needs display and would block
    from src.overlay.renderer import Renderer
    r = Renderer()
    r.trajectory = [(100, 100), (200, 200)]
    print(f"  ✅ Renderer 创建成功, trajectory={len(r.trajectory)}pts")
except Exception as e:
    print(f"  ❌ 覆盖层创建失败: {e}")

print("\n" + "=" * 50)
print("诊断完成")
print("=" * 50)
