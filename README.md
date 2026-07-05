# wave2u — NIKKE 实时预判线工具

在 NIKKE 小游戏窗口上叠加透明覆盖层，显示小球包含边界反射的完整反弹轨迹，辅助瞄准。

## 功能

- 帧差法实时检测游戏轨迹线
- 物理模拟含墙壁反射和方块反弹的完整弹道路径
- 透明覆盖层悬浮在游戏窗口上方
- 点击穿透，不影响游戏操作
- 实时方块检测

## 环境要求

- Windows 10/11
- Python 3.10+
- NIKKE 游戏以**窗口化或无边框窗口**模式运行（非全屏独占）

## 安装

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

## 启动

```bash
.venv\Scripts\python -m src.main
```

**注意：建议以管理员身份运行**（部分 Windows 配置下普通权限无法点击穿透）

## 使用方式

1. 启动工具，覆盖层会自动显示在屏幕上
2. 在游戏中按住拖拽瞄准 → 游戏画出淡青色轨迹线
3. 工具自动检测轨迹线，并延伸出含反射的完整路径
4. 松开鼠标 → 预判线消失

## 目录结构

```
src/
  main.py              入口
  config.py            配置（网格坐标、小球半径等）
  game_window.py       窗口定位
  detection/
    blocks.py          方块检测
    launch_point.py    轨迹线检测（帧差法）
  physics/
    trajectory.py      物理模拟（墙面反射 + 方块反弹）
  overlay/
    window.py          PyQt5 透明覆盖层
    renderer.py        QPainter 渲染
scripts/               实验和调试脚本
tests/                 单元测试
```

## 配置

编辑 `src/config.py`:

| 参数 | 默认值 | 说明 |
|------|--------|------|
| BALL_RADIUS | 25 | 小球半径（像素），影响反射偏移 |
| DETECTION_INTERVAL | 0.15 | 检测间隔（秒） |

## 技术栈

- Python 3.12
- PyQt5（覆盖层窗口）
- OpenCV（图像检测）
- numpy
- pyautogui（截图）
- pygetwindow（窗口定位）
