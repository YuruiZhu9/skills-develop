# AutoNote

长期维护单个 Markdown 笔记文件，将散乱的 Markdown、`.txt` 或纯文本自动去重、编辑压缩、归档为结构化笔记块。

## 核心功能

- **多格式输入**：支持内联 Markdown、`.md` 文件、`.txt` 文件、纯文本
- **编辑压缩**：自动去除冗余、提炼要点、重写为持久化的笔记语言
- **去重合并**：基于主题路径匹配，智能合并已有笔记而非盲目追加
- **结构化存储**：使用 `AUTONOTE:BEGIN/END` 标记管理笔记块，保持人工可编辑
- **确定性写入**：通过 `scripts/update_managed_note.py` 脚本执行原子更新，避免模型自由编辑导致格式漂移

## 文件夹结构

```
AutoNote skill/
├── README.md
├── claudecode/AutoNote/          # Claude Code 版本
│   ├── SKILL.md                  # Skill 定义文件
│   ├── references/               # 笔记格式、合并策略、主题规范化参考
│   ├── scripts/                  # 确定性更新脚本
│   ├── tests/                    # 单元测试
│   └── evals/                    # 评估用例与 fixture
└── codex/AutoNote/               # Codex 版本（结构同上）
```

## 使用方式

将对应版本的 `AutoNote/` 文件夹复制到本地 Skills 目录即可：

```bash
# Claude Code
cp -r claudecode/AutoNote/ ~/.claude/skills/AutoNote/

# Codex
cp -r codex/AutoNote/ ~/.codex/skills/AutoNote/
```

安装后，在对话中直接说"整理进笔记"、"更新 Technotes.md"等即可触发。
