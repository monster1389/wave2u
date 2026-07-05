"""全局常量配置"""

# ── 网格区域（与 scripts/detect_blocks.py 一致） ──
FX = 800   # 网格左上角 x
FY = 210   # 网格左上角 y
FW = 637   # 网格宽度
FH = 845   # 网格高度
GRID_COLS = 6
GRID_ROWS = 8

# ── 轨迹模拟 ──
STEP_SIZE = 2       # 每步推进像素
MAX_STEPS = 5000    # 最大步数（防死循环）
BALL_RADIUS = 25    # 小球半径（像素），影响碰撞偏移

# ── 覆盖层 ──
OVERLAY_FPS = 30    # 覆盖层刷新率
DETECTION_INTERVAL = 0.15  # 方块检测间隔（秒），~7fps 响应游戏拖拽
WINDOW_CHECK_INTERVAL = 1.0  # 窗口位置检测间隔（秒）

# ── 颜色（BGR 格式） ──
COLOR_PREDICTION_LINE = (255, 255, 0)    # 青色
COLOR_GRID = (128, 128, 128)            # 灰色
COLOR_BLOCK = (0, 255, 0)               # 绿色
COLOR_LAUNCH_POINT = (0, 255, 255)      # 黄色
COLOR_DIRECTION = (200, 200, 200)       # 浅灰虚线
COLOR_ENDPOINT = (0, 255, 255)          # 黄色终点
