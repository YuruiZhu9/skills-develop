# AutoNote Managed Note Format

This file defines the stable single-file block contract used by `AutoNote`.

## Purpose

The target note must stay easy for a human to read and edit, while still giving `AutoNote` a precise way to find and update old content. The block markers are the only machine-facing structure in this version.

## One Managed Block Per Leaf Topic

Use one managed block for one leaf topic path, for example:

- `技术/Python/装饰器`
- `工作/周报/2026-04-13`
- `项目/AutoNote/合并策略`

Do not combine unrelated leaf topics into one managed block just because they came from the same raw source.

## Block Shape

```md
<!-- AUTONOTE:BEGIN path="技术/Python/装饰器" -->
#### 装饰器
_Last Updated: 2026-04-13 14:30_

**Summary**
装饰器用于扩展函数行为而不直接修改函数主体。

##### Key Points
- 使用 `@decorator` 语法。
- 常见用途包括日志、计时、缓存。

##### Details
- 可用闭包包装原函数。
- 需要保留原函数元信息时，可考虑 `functools.wraps`。

##### Source Notes
- 2026-04-13: 来自学习记录整理。
<!-- AUTONOTE:END -->
```

## Required Elements

Every managed block should include:

- `AUTONOTE:BEGIN` with a stable `path="..."`
- a leaf-title heading
- `_Last Updated: YYYY-MM-DD HH:MM_`
- `**Summary**`
- `##### Key Points`
- `##### Source Notes`
- `AUTONOTE:END`

`##### Details` is recommended but optional when the content is very small.

## Path Rules

- Use slash-separated paths.
- Reuse existing taxonomy whenever possible.
- Keep the last path segment aligned with the block title unless an older path is being preserved for stability.
- Prefer path stability over cosmetic renaming.

If the updater matched an existing block by alias, it should usually preserve the old path rather than churn the file structure.

## Summary Rules

- Keep `Summary` to 1 to 3 sentences.
- Prefer compact, information-dense phrasing.
- State the main concept or outcome first.

## Key Points Rules

- Use flat bullets.
- Prefer 3 to 7 bullets.
- Keep each bullet self-contained and non-redundant.
- Place important warnings near the top when relevant.

## Details Rules

Use `Details` for:

- secondary explanation
- examples worth keeping
- non-trivial nuance
- implementation notes

Do not dump every raw sentence into `Details`. This section should still be edited and compressed.

## Source Notes Rules

Use `Source Notes` for brief provenance or uncertainty handling, for example:

- where the information came from
- whether it was merged from chat notes or a text file
- a short note about ambiguous or conflicting material

Keep this section short.

## Update Log Section

At the file level, maintain a plain Markdown section:

```md
## 更新记录
- 2026-04-13 14:30 更新 `技术/Python/装饰器`
```

Rules:

- append one concise line per meaningful update
- do not turn the update log into a full changelog
- if the file has no `## 更新记录`, create it near the end
- if the normalized block content did not actually change, do not append a log entry

## Meaningful Change Rules

`_Last Updated_` and `## 更新记录` should move together.

Only refresh them when:

- a new block is created
- a block's normalized content materially changes

Do not refresh them for:

- whitespace-only edits
- equivalent formatting-only edits
- alias matches that produce no content change
- `no_op`

## Safe Write Behavior

The updater now uses a safer write path:

- acquire a sidecar lock file before changing the target
- create a backup file when an existing note is materially changed
- write to a temporary file and replace the target atomically

This does not turn the note into a full versioned database. It is only a safety layer against partial writes and accidental overwrite during normal single-user use.

## Skeleton For A New File

If the target file does not exist, create:

```md
# Technotes

## 更新记录
```

Then add category headings and managed blocks above `## 更新记录`.

## Editing Existing Human Content

- Respect useful manual edits outside managed blocks.
- Do not reformat unrelated sections.
- Inside a managed block, preserve good manual content unless the new material clearly supersedes it.
- Prefer local edits over whole-file rewrites.
