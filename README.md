# Skills Develop

个人编写的 Claude Code / Codex 开源 Skills 合集。

本仓库长期维护，持续收录自研的实用技能（Skills），每个 Skill 独立存放在自己的文件夹中，方便安装、组合和扩展。

---

## 导航

- [Skill 索引](#skill-索引)
- [Showcase](#showcase)
- [仓库结构](#仓库结构)
- [如何使用](#如何使用)
- [如何贡献新 Skill](#如何贡献新-skill)

---

## Skill 索引

| Skill | 简介 | 路径 |
|-------|------|------|
| skill-router | 显式技能路由器，帮助模型在多个可用 Skill 之间做选择、比较和组合 | [`skill-router/README.md`](./skill-router/README.md) |

> 持续更新中，新 Skill 会追加到本表。

---

## Showcase

以下网页作品均通过组合多个 Skill（`frontend-design`、`algorithmic-art`、`shader-dev`、`canvas-design`）生成，展示了 Skill 组合的实际效果。

### Ephemeral Resonance — 瞬态共鸣

![Ephemeral Resonance](./网页生成.png)

- **文件**：[`ephemeral-resonance.html`](./ephemeral-resonance.html)

### Dreamlike Flow Page

- **文件**：[`dreamlike-flow-page.html`](./dreamlike-flow-page.html)

---

## 仓库结构

```
skills-develop/
├── README.md                      # 项目介绍与 Skill 索引
├── ephemeral-resonance.html       # Showcase 网页
├── dreamlike-flow-page.html       # Showcase 网页
├── 网页生成.png                    # Showcase 截图
├── skill-router/                  # Skill: 显式技能路由器
│   ├── README.md
│   ├── SKILL_codex.md
│   └── SKILL_claudecode.md
└── ...                            # 后续新增 Skill 按文件夹存放
```

---

## 如何使用

### 安装某个 Skill

将对应的 Skill 文件夹复制或软链接到本地 Skills 目录：

```bash
# Claude Code
cp -r skill-router/ ~/.claude/skills/

# Codex
cp -r skill-router/ ~/.codex/skills/
```

### 在对话中使用

以 `skill-router` 为例，在对话中直接说：

```
该用哪个 skill？
帮我组合多个 skills 来做一个产品官网。
列出我本地的 skills。
```

---

## 如何贡献新 Skill

1. 在仓库根目录新建文件夹，命名即 Skill 名称
2. 文件夹内必须包含 `README.md`（Skill 说明）和至少一个 `SKILL*.md`（Skill 定义文件）
3. 在根目录 `README.md` 的 [Skill 索引](#skill-索引) 表中添加一行
4. 提交 PR 即可
