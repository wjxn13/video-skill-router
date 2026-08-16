#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bootstrap.py — 视频工具链检测与自举

检测本机 manim / remotion / hyperframes / ffmpeg / edge-tts / ddsp 等是否可用，
输出 tool-index（JSON 或人类可读），缺失项给出安装引导。

用法：
    python bootstrap.py --json
    python bootstrap.py
"""

import argparse
import json
import shutil
import sys


def detect():
    """逐项检测工具是否可用。返回 {工具名: {available, cmd, hint}}。"""
    tools = {
        "python": {"cmd": "python", "hint": "Python 3.10+，用于 Manim 与脚本"},
        "manim": {"cmd": "manim", "hint": "pip install manim（数学动画引擎）"},
        "node": {"cmd": "node", "hint": "Node.js 22+，Remotion / HyperFrames 运行时"},
        "npx": {"cmd": "npx", "hint": "随 Node.js 自带，用于 remotion / hyperframes CLI"},
        "ffmpeg": {"cmd": "ffmpeg", "hint": "视频总装/转码/字幕烧录"},
        "ffprobe": {"cmd": "ffprobe", "hint": "随 ffmpeg 安装，用于校验"},
        "edge-tts": {"cmd": "edge-tts", "hint": "pip install edge-tts（微软免费在线 TTS）"},
    }
    result = {}
    for name, spec in tools.items():
        path = shutil.which(spec["cmd"])
        result[name] = {
            "available": path is not None,
            "cmd": spec["cmd"],
            "path": path,
            "hint": spec["hint"],
        }
    return result


def render_human(detected):
    lines = []
    for name, info in detected.items():
        mark = "OK " if info["available"] else "MISS"
        lines.append("[%s] %-10s %s" % (mark, name, info["cmd"]))
        if not info["available"]:
            lines.append("         缺少 → %s" % info["hint"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="视频工具链检测与自举")
    parser.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)

    detected = detect()
    if args.as_json:
        print(json.dumps(detected, ensure_ascii=False, indent=2))
    else:
        print(render_human(detected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
