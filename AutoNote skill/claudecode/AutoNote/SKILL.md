---
name: AutoNote
description: Maintain a long-lived Markdown note file by turning noisy Markdown, `.txt`, or plain text into structured, deduplicated notes. Use this whenever the user asks to organize notes, update `Technotes.md` or another Markdown note, merge new material into an existing note file, keep a knowledge note current over time, or compress and rewrite messy source text into durable notes. Trigger even when the user only says things like “整理进笔记”, “归类到 notes”, “更新 markdown 笔记”, “把 txt 记到知识库”, “把聊天记录写进同一个笔记文件”, “长期维护同一个笔记”, or wants repeated updates to the same note.
---

# AutoNote

Use this skill to maintain one long-lived Markdown note file in place. The first version is still optimized for a single file such as `Technotes.md`, not a multi-file note vault.

## Default Assumptions

- Default target file: `./Technotes.md`
- Alternate target: any user-specified path in the current path or another explicit path
- Supported inputs in this version:
  - inline Markdown
  - inline plain text
  - `.md` file content
  - `.txt` file content
- Default write behavior: update the note file directly without asking for a pre-write confirmation
- Category strategy: dynamic, but prefer reusing the file's existing taxonomy before inventing a new one

## Read These References Before Writing

- `references/managed-note-format.md`
- `references/merge-policy.md`
- `references/topic-normalization.md`

Read the full text only when you are actually going to update a note. These files define the block contract, action ladder, and conservative same-topic normalization rules.

## Core Rule

Assume the source material is noisy, redundant, weakly structured, and low-density unless the user clearly provides polished notes already. Your job is not only to file the content but to improve it before storage.

Run an editorial pass before deciding what to write:

- compress repetitive or low-value phrasing
- summarize the main point in 1 to 3 strong sentences
- extract definitions, steps, conclusions, warnings, commands, formulas, and examples
- rewrite chatty language into durable note language
- polish awkward wording for clarity
- add only small, low-risk clarifications when needed to make the note self-contained

Do not invent unsupported facts. Do not inflate simple notes into long essays.

## Managed Note Protocol

Managed blocks use lightweight markers and stay human-editable:

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
- 需要保留原函数元信息时，可考虑 `functools.wraps`。

##### Source Notes
- 2026-04-13: 来自学习笔记整理。
<!-- AUTONOTE:END -->
```

Treat the managed block as the atomic update unit. Do not manually freestyle block replacement when the local updater script is available.

## Resolve Inputs

1. Resolve the target note file.
   - If the user specifies `target`, use it.
   - Otherwise default to `./Technotes.md`.
2. Resolve the source material.
   - If the user points to a `.md` or `.txt` file, read that file.
   - If the user pastes inline content, use it directly.
   - If both are present, follow the user's explicit priority if given. Otherwise use the source that is clearly framed as the input to process.
3. If the target path is ambiguous in a risky way, ask one short question. Otherwise make the reasonable default choice and continue.

## Normalize The Source

Handle the input families this way:

- Markdown:
  - preserve useful headings, lists, quotes, tables, and code fences
  - remove obvious noise such as duplicate empty headings or repeated filler lines
- `.txt` and plain text:
  - split the content into semantic chunks
  - infer paragraphs, lists, steps, definitions, warnings, and conclusions
  - convert the result into Markdown-friendly structure before storage

The point of normalization is not cosmetic cleanup. It is to create reliable semantic units for categorization and merging.

## Run The Editorial Pass

Treat this as a mandatory step, not a nice-to-have.

Prioritize:

- information density
- long-term readability
- durable wording
- clean separation between summary, key points, and supporting details

Typical editorial moves:

- delete filler, repeated examples, and weak transitions
- merge near-duplicate sentences into one precise statement
- convert vague remarks into concise notes when the meaning is clear
- move secondary context into `Details` or `Source Notes`
- keep core commands, formulas, code snippets, and warnings intact

Allowed low-risk expansion:

- brief clarifying definitions
- one-line background context
- a small caveat or common use case when it is stable and obvious

Not allowed:

- fabricated facts
- speculative timelines
- specific claims not supported by the source
- broad expansions that change the meaning of the original material

## Choose Or Reuse Topic Paths

Infer one or more target paths from the cleaned material.

Rules:

- prefer existing top-level categories already used in the note file
- keep top-level categories relatively stable and broad
- create a new category only when the existing taxonomy clearly does not fit
- split mixed-topic input into multiple managed blocks when needed
- use slash-separated paths such as `技术/Python/装饰器`
- normalize same-topic naming conservatively, not aggressively

Do not collapse merely related topics into one path. Only converge high-confidence same-topic variants.

## Decide The Action

Choose one action per operation:

- `no_op`
- `append`
- `merge`
- `replace`
- `split`

Action choice must happen after the editorial pass, not on the raw source text.

Biases:

- treat `no_op` as a real action, not a failure mode
- do not append by default
- prefer `merge` over blind accumulation
- use `replace` only when the old block is clearly outdated or structurally not worth preserving
- use `split` when one raw input actually contains multiple topics

See `references/merge-policy.md` for the exact ladder.

Important updater boundary:

- `split` is a model-side planning action
- before calling the updater, expand `split` into multiple concrete operations
- do not send a raw `action: "split"` operation to `scripts/update_managed_note.py`

## Build A Structured Update Intent

Before writing, convert the decision into a structured payload. The script is easier to trust when the model hands it a clean, explicit plan.

Use this shape:

```json
{
  "target_file": "C:/Users/yrzhu/Technotes.md",
  "operations": [
    {
      "path": "技术/Python/装饰器",
      "aliases": ["装饰器", "Python 装饰器", "Decorator"],
      "action": "merge",
      "title": "装饰器",
      "summary": "装饰器用于扩展函数行为而不直接修改函数主体。",
      "key_points": [
        "使用 @decorator 语法。",
        "多层装饰器时容易混淆定义顺序与调用表现。"
      ],
      "details": [
        "装饰器本质上通常返回新的包装函数。",
        "需要保留原函数元信息时可使用 functools.wraps。"
      ],
      "source_notes": [
        "2026-04-13: 来自学习记录整理。"
      ],
      "clear_details": false,
      "reason": "新旧内容主题一致，但新内容更完整，适合合并重写。"
    }
  ]
}
```

Keep `reason` concise. It exists to force a coherent decision, not to produce a long explanation for the user.

Merge payload semantics:

- for `merge`, the payload should contain the final merged content you want stored
- the updater does not infer a semantic union for you
- if a field is omitted, the updater falls back to the existing value
- if you need to explicitly clear a field such as `Details`, pass a clear flag like `clear_details: true`
- for list fields in `merge`, do not send an empty list to mean “leave unchanged”
- omit the field to preserve the existing list, or use the clear flag to remove it

## Use The Deterministic Updater

When the payload is ready, write it to a temporary JSON file and call:

```bash
python scripts/update_managed_note.py --payload-file <payload.json> --timestamp "YYYY-MM-DD HH:MM"
```

What the script is trusted to do:

- parse existing managed blocks
- match exact paths first
- reuse same-topic aliases conservatively
- insert new category headings when needed
- keep new blocks before `## 更新记录`
- avoid timestamp churn for no-op updates
- avoid update-log churn when the normalized content did not actually change
- reject unsupported actions or malformed payloads early
- write through a lock + atomic replace path
- create a backup file when an existing target file is materially changed

What the script does not decide for you:

- whether the material should be `merge` vs `replace`
- whether two merely related topics should be unified
- how to editorially compress and rewrite the source
- how to expand a `split` into concrete child operations

Those remain model-side judgments.

## If The Script Is Unavailable

Only fall back to manual editing if the script is genuinely unavailable. In that fallback:

- preserve the exact managed block format
- follow the same `no_op` and update-log rules
- do not reformat unrelated sections

But the normal path is to use `scripts/update_managed_note.py`.

## Output Back To The User

After writing the file, return a short summary that includes:

- the target file path
- which category paths were added
- which category paths were merged or replaced
- whether any content was skipped as duplicate or no-op

Keep this summary short. The primary deliverable is the updated note file itself.

## Guardrails

- Do not keep raw low-value chatter just because it appeared in the source.
- Do not create multiple near-duplicate paths for the same concept.
- Do not ask for confirmation before normal writes unless the path or intent is genuinely ambiguous.
- Do not silently drop valuable non-conflicting details during aggressive compression.
- Do not rewrite unrelated parts of the note file.
- Do not treat weak planning chatter as a meaningful update.
- Do not refresh `_Last Updated_` or `## 更新记录` if the normalized block content did not materially change.

## Example

**Input**

```text
今天学到了 Python 装饰器的用法，它可以用来扩展函数行为，比如日志和计时。语法是用 @ 符号。重要：装饰器执行顺序是从下往上。其实我前面还看了一些重复的例子，不过核心就这些。
```

**Expected behavior**

- route to `技术/Python/装饰器`
- compress redundant phrasing
- produce a compact summary
- highlight the execution-order warning
- choose `merge` rather than blind append
- update the file via `scripts/update_managed_note.py`
