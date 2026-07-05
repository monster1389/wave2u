"""检测模块单元测试

注意：这些测试需要 docs/images/nikke_screenshot.png 存在
（由 scripts/screenshot_nikke.py 生成）
"""

import sys
import os
sys.path.insert(0, "src")

import cv2
from src.detection.blocks import detect_blocks
from src.detection.launch_point import detect_launch_point


def _load_test_image():
    path = "docs/images/nikke_screenshot.png"
    if not os.path.exists(path):
        raise FileNotFoundError(f"测试截图不存在: {path}")
    return cv2.imread(path)


def test_detect_blocks_returns_list():
    img = _load_test_image()
    blocks = detect_blocks(img)
    assert isinstance(blocks, list)


def test_detect_blocks_have_required_keys():
    img = _load_test_image()
    blocks = detect_blocks(img)
    if blocks:
        for blk in blocks:
            for key in ("col", "row", "x", "y", "w", "h"):
                assert key in blk, f"missing key: {key}"


def test_detect_launch_point_returns_tuple():
    img = _load_test_image()
    pt = detect_launch_point(img)
    if pt is not None:
        x, y = pt
        assert isinstance(x, int)
        assert isinstance(y, int)
