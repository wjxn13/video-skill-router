#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""段级路由回归测试

每个用例：任务描述 -> 期望命中的规则 id（含依赖顺序）。

验证目标：路由规则被改坏时，这里能抓到。这是 reverse-skill 那套
「可测试路由矩阵」在视频领域的落点——区别是：这里测的是「段级路由」，
不是逆向那种「任务级分类」。

运行：
    python tests/test_routing.py
"""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "dsh-plugin" / "skills" / "video-skill-router" / "scripts" / "master-route.py"

spec = importlib.util.spec_from_file_location("master_route", SCRIPT)
master_route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(master_route)

RULES = master_route.load_rules()


def route_ids(text):
    return master_route.route(text, RULES)["matched_rule_ids"]


class TestSegmentRouting(unittest.TestCase):
    """内容型规则：单一片段 -> 单引擎"""

    def test_math_routes_to_manim(self):
        self.assertIn("R01", route_ids("做一个最短路径的科普动画，讲公式推导"))

    def test_quote_routes_to_hyperframes(self):
        self.assertIn("R02", route_ids("给这段金句做排版动画"))

    def test_interaction_routes_to_remotion(self):
        self.assertIn("R03", route_ids("做一个带点击分支的交互演示"))

    def test_chart_routes_to_remotion(self):
        self.assertIn("R04", route_ids("把这份数据做成柱状图"))

    def test_code_routes_to_hyperframes(self):
        self.assertIn("R05", route_ids("展示这段代码的运行演示"))


class TestVoiceRouting(unittest.TestCase):
    """旁白与音色：依赖顺序是硬规则"""

    def test_voiceover_routes_to_edge_tts_and_runs_first(self):
        ids = route_ids("做一个科普动画，女声解说")
        self.assertIn("R10", ids)
        # R10 必须排最前（run-before-others：先 TTS 定段长）
        self.assertEqual(ids[0], "R10")

    def test_custom_voice_routes_to_ddsp_after_tts(self):
        ids = route_ids("旁白用我自定义的音色，克隆我的声音")
        self.assertIn("R11", ids)
        self.assertIn("R10", ids)
        # R11 依赖 after-tts：必须排在 R10 之后
        self.assertLess(ids.index("R10"), ids.index("R11"))


class TestAssemblyRouting(unittest.TestCase):
    """字幕与多段总装"""

    def test_subtitle_routes_to_ffmpeg(self):
        self.assertIn("R20", route_ids("加中文字幕，软字幕和硬字幕都要"))

    def test_multi_segment_triggers_xfade_assembly(self):
        ids = route_ids("做一个科普视频，先公式推导，再金句排版，配女声解说")
        self.assertIn("R01", ids)
        self.assertIn("R02", ids)
        self.assertIn("R30", ids)  # 多段 -> ffmpeg xfade 总装

    def test_single_segment_does_not_trigger_assembly(self):
        ids = route_ids("画一个函数曲线")
        self.assertIn("R01", ids)
        self.assertNotIn("R30", ids)  # 只有一段，不需要总装


class TestContractIntegrity(unittest.TestCase):
    """契约完整性：关键契约必须存在且被正确挂载"""

    def test_ddsp_contract_exists(self):
        result = master_route.route("用我的声音配音", RULES)
        self.assertIn("R11", result["matched_rule_ids"])
        self.assertIn("custom-voice-content-preserved", result["contracts"])

    def test_narration_contract_mounted_on_voiceover(self):
        result = master_route.route("做个视频，女声解说", RULES)
        self.assertIn("segment-length-equals-measured-narration", result["contracts"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
