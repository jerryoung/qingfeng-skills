#!/usr/bin/env python3
"""Small regression test for analyze_policy_corpus.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analyze_policy_corpus import analyze_file


class AnalyzePolicyCorpusTest(unittest.TestCase):
    def test_markers_normalization_and_cross_line_keyword(self) -> None:
        content = """目录
第一篇 目录重复
正文开始
第一篇 发展基础
推进人工\n智能和ＡＩ应用，扩大消费。
附录开始
人工智能
"""
        with tempfile.TemporaryDirectory(prefix="policy-test-") as temp_dir:
            path = Path(temp_dir) / "sample.txt"
            path.write_text(content, encoding="utf-8")
            result = analyze_file(
                path,
                ["人工智能", "AI", "消费"],
                "正文开始",
                "附录开始",
            )

        self.assertEqual(result["keywords"]["人工智能"]["count"], 1)
        self.assertEqual(result["keywords"]["AI"]["count"], 1)
        self.assertEqual(result["keywords"]["消费"]["count"], 1)
        self.assertEqual(result["heading_candidates"], ["第一篇 发展基础"])
        self.assertGreater(result["hanzi_count"], 0)
        self.assertEqual(len(result["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
