# skill-router

显式技能路由器——帮助模型在多个可用 Skill 之间做**选择、比较和组合**。

它不是通用前置拦截器，不会自动介入所有任务，仅在用户明确需要"选 Skill、比 Skill、配 Skill"时触发。

---

## 文件说明

| 文件 | 适用环境 | 说明 |
|------|---------|------|
| [`SKILL_codex.md`](./SKILL_codex.md) | Codex | 适配 Codex 环境的 Skill 定义 |
| [`SKILL_claudecode.md`](./SKILL_claudecode.md) | Claude Code | 适配 Claude Code 环境的 Skill 定义 |

---

## 一句话理解

适合 `skill-router` 的问题是 **"帮我决定该用哪些 Skills"**，而不是"帮我做事"。

---

## 什么时候会触发

- "该用哪个 skill？"
- "帮我选一个 skill"
- "列出本地 / 可用的 skills"
- "组合多个 skills"
- "多个 skill 怎么配合？"
- 任务明显跨多个 Skill，且没有单一明确赢家
- 需要比较两个 Skill 的适配性

## 什么时候不会触发

- 用户已经点名某个 Skill（如"用 frontend-design 做一个网页"）
- 某个领域 Skill 明显就是直接答案
- 只是普通的单领域任务
- 只说了"create"、"build"、"generate"，但没表达 Skill 路由需求

---

## 核心工作流

路由器会先判断当前任务属于哪一类：

| 类型 | 场景 |
|------|------|
| A. 盘点 Skills | 用户只想知道有哪些 Skills |
| B. 选择单个 Skill | 有明确任务，不知道该用哪个 |
| C. 组合多个 Skills | 一个任务确实需要多个 Skill 协作 |
| D. 比较 / 去歧义 | 同名 Skill 多版本，或两个 Skill 看起来都适用 |

### 路由优先级

1. 用户是否已经点名某个 Skill
2. 是否存在必须先触发的流程型 Skill（如 `brainstorming`）
3. 是否存在单一明确优先的领域 Skill
4. 以上都不满足时，才进入多 Skill 路由

### 组合方式

优先采用 **主 Skill + 辅助 Skill** 结构，不会平铺并列多个 Skill。

---

## 示例输出

以下网页由 `skill-router` 路由组合 `frontend-design`、`algorithmic-art`、`shader-dev`、`canvas-design` 四个 Skill 生成，展示了多 Skill 协作的实际效果。

### Ephemeral Resonance — 瞬态共鸣

![Ephemeral Resonance](./网页生成.png)

- **文件**：[`ephemeral-resonance.html`](./ephemeral-resonance.html)

### Dreamlike Flow Page

- **文件**：[`dreamlike-flow-page.html`](./dreamlike-flow-page.html)

---

## 安装

```bash
# Claude Code
cp -r skill-router/ ~/.claude/skills/

# Codex
cp -r skill-router/ ~/.codex/skills/
```

---

## 常用提问模板

```
这个任务该用哪个 skill？
帮我选一个最合适的 skill 来完成：...
帮我组合多个 skills 来完成：...
列出我本地的 skills，并按用途分类。
比较这两个 skill：... vs ...
```
