# AutoNote Topic Normalization

Use this reference when deciding whether new material belongs to an existing path or should create a new one.

## Goal

Keep topic paths stable over time without forcing unrelated topics into the same bucket.

## Preferred Matching Order

1. exact path reuse
2. existing block title match
3. alias match supplied by the model
4. conservative normalized-string match

Do not jump straight from “related” to “same”.

## Good Same-Topic Cases

- `Python 装饰器` / `装饰器` / `Decorator`
- `周报` / `weekly report`
- `merge policy` / `合并策略`

## Bad Same-Topic Cases

- `装饰器` and `闭包`
- `异步编程` and `协程`
- `工作/周报` and `项目/周报模板`

Related topics are not automatically the same topic.

## Conservative Rules

- prefer stability over novelty
- prefer reusing a known path when confidence is high
- prefer creating a new path over over-merging when confidence is low
- preserve an old path if alias matching finds the existing block cleanly

## Alias Guidance

The model should supply a short alias list only for high-confidence same-topic variants.

Good alias list:

```json
["装饰器", "Python 装饰器", "Decorator"]
```

Bad alias list:

```json
["装饰器", "闭包", "高阶函数", "元编程"]
```

The second list mixes related concepts and would encourage accidental over-merging.
