"""
Phase 1: 对比轨迹线偏左 vs 偏右时的检测行为
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cv2, numpy as np, pyautogui
from src.config import FX, FY, FW, FH
from src.detection.launch_point import detect_trajectory

# 取色常量（从 launch_point.py 复制）
LINE_HUE_LOWER, LINE_HUE_UPPER = 70, 130
LINE_SAT_LOWER, LINE_SAT_UPPER = 5, 180
LINE_VAL_LOWER = 100

print("=" * 60)
print("PHASE 1: 左右不对称根因调查")
print("=" * 60)

for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
s = pyautogui.screenshot()
frame = cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR)
roi = frame[FY:FY+FH, FX:FX+FW]
hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

# ── 证据 A: 左侧 vs 右侧 HSV 分布对比 ──
print("\n[证据A] 左右半场 HSV 分布对比")
mid_x = FW // 2
left_hsv = hsv[:, :mid_x, :]
right_hsv = hsv[:, mid_x:, :]

# 当前颜色范围的像素数
mask_all = cv2.inRange(hsv,
    np.array([LINE_HUE_LOWER, LINE_SAT_LOWER, LINE_VAL_LOWER]),
    np.array([LINE_HUE_UPPER, LINE_SAT_UPPER, 255]))
mask_left = mask_all[:, :mid_x]
mask_right = mask_all[:, mid_x:]

px_left = cv2.countNonZero(mask_left)
px_right = cv2.countNonZero(mask_right)
area_left = mid_x * FH
area_right = (FW - mid_x) * FH
print(f"  左侧: {px_left} 像素 ({px_left/area_left*100:.1f}%)")
print(f"  右侧: {px_right} 像素 ({px_right/area_right*100:.1f}%)")

# ── 证据 B: 不同 HoughLinesP 阈值的候选线条数 ──
print("\n[证据B] HoughLinesP 阈值 vs 候选线条数")
kernel = np.ones((3,3), np.uint8)
mask_close = cv2.morphologyEx(mask_all, cv2.MORPH_CLOSE, kernel, iterations=1)

for thresh in [50, 100, 150, 200, 250, 300]:
    lines = cv2.HoughLinesP(mask_close, rho=1, theta=np.pi/360,
                             threshold=thresh, minLineLength=100, maxLineGap=50)
    n = len(lines) if lines is not None else 0
    print(f"  threshold={thresh:3d}: {n:4d} 条线段")

# ── 证据 C: threshold=200 时的线条方向分布 ──
print("\n[证据C] threshold=200 时的线条方向分布")
lines = cv2.HoughLinesP(mask_close, rho=1, theta=np.pi/360,
                         threshold=200, minLineLength=100, maxLineGap=50)
n_left = n_right = n_vert = n_horiz = 0
if lines is not None:
    if len(lines.shape) == 3:
        lines = lines[:, 0, :]
    for l in lines:
        x1, y1, x2, y2 = l
        dx = x2 - x1; dy = y2 - y1
        length = np.sqrt(dx*dx + dy*dy)
        if length < 80: continue
        horiz = abs(dx / max(length, 1))
        if horiz < 0.08: n_vert += 1; continue
        if horiz > 0.95: n_horiz += 1; continue
        # 斜线：偏左还是偏右？
        if dx < 0: n_left += 1
        else: n_right += 1
    print(f"  斜线(偏左): {n_left}")
    print(f"  斜线(偏右): {n_right}")
    print(f"  垂直线: {n_vert}")
    print(f"  水平线: {n_horiz}")
    print(f"  总计: {n_left + n_right + n_vert + n_horiz}")
    
    # 画出来
    line_img = roi.copy()
    for l in lines:
        x1, y1, x2, y2 = l
        dx = x2-x1; dy = y2-y1
        length = np.sqrt(dx*dx + dy*dy)
        if length < 80: continue
        horiz = abs(dx / max(length, 1))
        if horiz < 0.08 or horiz > 0.95: continue
        # 斜线用青色
        cv2.line(line_img, (x1, y1), (x2, y2), (0, 255, 255), 3)
    cv2.imwrite("docs/images/rca_slanted_lines.png", line_img)
    print(f"\n  斜线可视化: docs/images/rca_slanted_lines.png")

# ── 证据 D: 当前检测结果 ──
print("\n[证据D] detect_trajectory 结果")
traj = detect_trajectory(frame)
if traj:
    lx, ly, dx, dy = traj
    print(f"  发射点=({lx},{ly}) 方向=({dx},{dy})")
    print(f"  偏{'左' if dx < 0 else '右'}")
    from src.physics.trajectory import simulate
    wp, reason, col, row = simulate(lx, ly, dx, dy, [])
    print(f"  路径: {len(wp)}点 终止={reason}")
else:
    print(f"  未检测到")

print(f"\n请查看 docs/images/rca_slanted_lines.png")
print(f"青色线条 = threshold=200 时仍然保留的斜线候选")
print(f"如果右侧有更多青色线条 = 右侧噪声多")
