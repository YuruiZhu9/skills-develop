import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_managed_note.py"


def load_module():
    spec = importlib.util.spec_from_file_location("autonote_update_managed_note", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_block(
    path,
    title,
    summary,
    key_points,
    last_updated="2026-04-13 10:00",
    details=None,
    source_notes=None,
):
    lines = [
        f'<!-- AUTONOTE:BEGIN path="{path}" -->',
        f"#### {title}",
        f"_Last Updated: {last_updated}_",
        "",
        "**Summary**",
        summary,
        "",
        "##### Key Points",
    ]
    for item in key_points:
        lines.append(f"- {item}")
    if details:
        lines.extend(["", "##### Details"])
        for item in details:
            lines.append(f"- {item}")
    lines.extend(["", "##### Source Notes"])
    for item in source_notes or ["2026-04-13: test source."]:
        lines.append(f"- {item}")
    lines.append("<!-- AUTONOTE:END -->")
    return "\n".join(lines)


class UpdateManagedNoteTests(unittest.TestCase):
    maxDiff = None

    def test_exact_path_merge_updates_existing_block(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "旧摘要。",
                    ["旧要点。"],
                ),
                "",
                "## 更新记录",
                "- 2026-04-13 10:00 更新 `技术/Python/装饰器`",
                "",
            ]
        )
        operations = [
            {
                "path": "技术/Python/装饰器",
                "aliases": ["装饰器"],
                "action": "merge",
                "title": "装饰器",
                "summary": "新摘要。",
                "key_points": ["新要点。"],
                "details": ["补充说明。"],
                "source_notes": ["2026-04-13: 新来源。"],
            }
        ]

        updated = module.apply_operations(note_text, operations, "2026-04-13 15:30")

        self.assertIn("新摘要。", updated)
        self.assertNotIn("旧摘要。", updated)
        self.assertEqual(updated.count('<!-- AUTONOTE:BEGIN path="技术/Python/装饰器" -->'), 1)
        self.assertIn("_Last Updated: 2026-04-13 15:30_", updated)
        self.assertIn("- 2026-04-13 15:30 更新 `技术/Python/装饰器`", updated)

    def test_alias_match_reuses_existing_block_and_preserves_existing_path(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "已有摘要。",
                    ["已有要点。"],
                ),
                "",
                "## 更新记录",
                "",
            ]
        )
        operations = [
            {
                "path": "技术/Python/Decorator",
                "aliases": ["装饰器", "Python 装饰器", "Decorator"],
                "action": "merge",
                "title": "装饰器",
                "summary": "别名命中的更新摘要。",
                "key_points": ["别名命中的更新要点。"],
                "source_notes": ["2026-04-13: alias match."],
            }
        ]

        updated = module.apply_operations(note_text, operations, "2026-04-13 15:45")

        self.assertIn('<!-- AUTONOTE:BEGIN path="技术/Python/装饰器" -->', updated)
        self.assertEqual(updated.count("<!-- AUTONOTE:BEGIN"), 1)
        self.assertNotIn('path="技术/Python/Decorator"', updated)
        self.assertIn("别名命中的更新摘要。", updated)

    def test_no_op_keeps_text_identical(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "稳定摘要。",
                    ["稳定要点。"],
                    last_updated="2026-04-13 09:00",
                    details=["稳定细节。"],
                    source_notes=["2026-04-13: stable."],
                ),
                "",
                "## 更新记录",
                "- 2026-04-13 09:00 更新 `技术/Python/装饰器`",
                "",
            ]
        )
        operations = [
            {
                "path": "技术/Python/装饰器",
                "aliases": ["装饰器"],
                "action": "merge",
                "title": "装饰器",
                "summary": "稳定摘要。",
                "key_points": ["稳定要点。"],
                "details": ["稳定细节。"],
                "source_notes": ["2026-04-13: stable."],
            }
        ]

        updated = module.apply_operations(note_text, operations, "2026-04-13 18:00")

        self.assertEqual(updated, note_text)

    def test_new_block_is_inserted_before_update_log_with_missing_headings(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 更新记录",
                "",
            ]
        )
        operations = [
            {
                "path": "项目/AutoNote/合并策略",
                "aliases": ["合并策略", "merge policy"],
                "action": "replace",
                "title": "合并策略",
                "summary": "记录 AutoNote 的合并决策规则。",
                "key_points": ["默认偏向 merge 而不是盲目 append。"],
                "details": ["当旧块明显过时才 replace。"],
                "source_notes": ["2026-04-13: project decision."],
            }
        ]

        updated = module.apply_operations(note_text, operations, "2026-04-13 16:00")

        self.assertIn("## 项目", updated)
        self.assertIn("### AutoNote", updated)
        self.assertIn('<!-- AUTONOTE:BEGIN path="项目/AutoNote/合并策略" -->', updated)
        self.assertLess(
            updated.index('<!-- AUTONOTE:BEGIN path="项目/AutoNote/合并策略" -->'),
            updated.index("## 更新记录"),
        )
        self.assertIn("- 2026-04-13 16:00 更新 `项目/AutoNote/合并策略`", updated)

    def test_split_action_raises_instead_of_being_silently_ignored(self):
        module = load_module()
        note_text = "# Technotes\n\n## 更新记录\n"
        operations = [
            {
                "path": "技术/Python/装饰器",
                "aliases": ["装饰器"],
                "action": "split",
                "title": "装饰器",
                "summary": "should not be accepted directly",
                "key_points": [],
                "details": [],
                "source_notes": [],
            }
        ]

        with self.assertRaises(ValueError):
            module.apply_operations(note_text, operations, "2026-04-14 09:00")

    def test_merge_can_explicitly_clear_details(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "稳定摘要。",
                    ["稳定要点。"],
                    details=["应该被删除的旧细节。"],
                    source_notes=["2026-04-14: stable."],
                ),
                "",
                "## 更新记录",
                "- 2026-04-14 09:00 更新 `技术/Python/装饰器`",
                "",
            ]
        )
        operations = [
            {
                "path": "技术/Python/装饰器",
                "aliases": ["装饰器"],
                "action": "merge",
                "title": "装饰器",
                "summary": "稳定摘要。",
                "key_points": ["稳定要点。"],
                "clear_details": True,
                "source_notes": ["2026-04-14: rewritten."],
            }
        ]

        updated = module.apply_operations(note_text, operations, "2026-04-14 10:00")

        self.assertNotIn("应该被删除的旧细节。", updated)
        self.assertNotIn("##### Details", updated)

    def test_invalid_action_is_rejected(self):
        module = load_module()
        note_text = "# Technotes\n\n## 更新记录\n"
        operations = [
            {
                "path": "技术/Python/装饰器",
                "action": "merge_everything",
                "title": "装饰器",
                "summary": "bad action",
                "key_points": [],
                "details": [],
                "source_notes": [],
            }
        ]

        with self.assertRaises(ValueError):
            module.apply_operations(note_text, operations, "2026-04-14 09:30")

    def test_merge_with_empty_list_without_clear_flag_is_rejected(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "旧摘要。",
                    ["旧要点。"],
                    details=["旧细节。"],
                    source_notes=["2026-04-14: old."],
                ),
                "",
                "## 更新记录",
                "- 2026-04-14 09:00 更新 `技术/Python/装饰器`",
                "",
            ]
        )
        operations = [
            {
                "path": "技术/Python/装饰器",
                "action": "merge",
                "title": "装饰器",
                "summary": "只改摘要，不应通过空列表表达保留旧值。",
                "key_points": [],
            }
        ]

        with self.assertRaises(ValueError):
            module.apply_operations(note_text, operations, "2026-04-14 09:45")

    def test_append_extends_existing_lists_and_keeps_summary(self):
        module = load_module()
        note_text = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "旧摘要。",
                    ["旧要点。", "重复要点。"],
                    details=["旧细节。"],
                    source_notes=["2026-04-14: old."],
                ),
                "",
                "## 更新记录",
                "- 2026-04-14 09:00 更新 `技术/Python/装饰器`",
                "",
            ]
        )
        operations = [
            {
                "path": "技术/Python/装饰器",
                "aliases": ["装饰器"],
                "action": "append",
                "title": "装饰器",
                "summary": "这个 summary 不应覆盖旧值。",
                "key_points": ["重复要点。", "新增要点。"],
                "details": ["旧细节。", "新增细节。"],
                "source_notes": ["2026-04-14: old.", "2026-04-14: appended."],
            }
        ]

        updated = module.apply_operations(note_text, operations, "2026-04-14 10:30")

        self.assertIn("旧摘要。", updated)
        self.assertNotIn("这个 summary 不应覆盖旧值。", updated)
        self.assertIn("- 旧要点。", updated)
        self.assertIn("- 重复要点。", updated)
        self.assertIn("- 新增要点。", updated)
        self.assertEqual(updated.count("- 重复要点。"), 1)
        self.assertIn("- 旧细节。", updated)
        self.assertIn("- 新增细节。", updated)
        self.assertIn("- 2026-04-14: appended.", updated)

    def test_apply_payload_creates_backup_for_existing_changed_file(self):
        module = load_module()
        original = "\n".join(
            [
                "# Technotes",
                "",
                "## 技术",
                "### Python",
                sample_block(
                    "技术/Python/装饰器",
                    "装饰器",
                    "旧摘要。",
                    ["旧要点。"],
                ),
                "",
                "## 更新记录",
                "- 2026-04-14 09:00 更新 `技术/Python/装饰器`",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "Technotes.md"
            target.write_text(original, encoding="utf-8")
            payload = {
                "target_file": str(target),
                "operations": [
                    {
                        "path": "技术/Python/装饰器",
                        "aliases": ["装饰器"],
                        "action": "merge",
                        "title": "装饰器",
                        "summary": "新摘要。",
                        "key_points": ["新要点。"],
                        "source_notes": ["2026-04-14: new."],
                    }
                ],
            }

            result = module.apply_payload(payload, "2026-04-14 11:00")

            backup_path = Path(result["backup_file"])
            self.assertTrue(backup_path.exists())
            self.assertEqual(backup_path.read_text(encoding="utf-8"), original)
            self.assertIn("新摘要。", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
