# AutoNote Merge Policy

Use this reference when deciding whether a cleaned topic should be `no_op`, `append`, `merge`, `replace`, or `split`.

## Decision Order

Always evaluate in this order:

1. `no_op`
2. `append`
3. `merge`
4. `replace`
5. `split`

`split` is logically earlier when the source clearly contains multiple topics, but once a topic operation exists, the action ladder above applies per operation.

## `no_op`

Choose `no_op` when the cleaned content adds no meaningful information.

Typical signs:

- it only rephrases existing meaning
- it repeats known points with lower information density
- it is mostly weak planning chatter such as “先这样”, “以后再看”, “回头补充”
- it does not justify refreshing `_Last Updated_`

Effects:

- do not change the block body
- do not change `_Last Updated_`
- do not add an update-log entry

## `append`

Choose `append` when the topic is clearly the same and the new content is only additive support material.

Good examples:

- a new example
- an extra caveat
- a supporting implementation detail

Do not use `append` as the default update action. It is for small additive updates, not for lazy accumulation.

## `merge`

Choose `merge` when the topic is the same and the old and new material should be consolidated into a cleaner long-term block.

Typical signs:

- heavy overlap between old and new material
- old block is useful but structurally messy
- new material is more complete or better expressed
- a compact rewrite would improve the note

`merge` is the preferred positive default for same-topic updates.

Payload contract for `merge`:

- the payload should carry the final merged content to store
- the updater does not automatically union old and new bullet lists semantically
- if a field is omitted, the updater falls back to the existing field value
- if a field must be removed, pass an explicit clear flag such as `clear_details: true`
- for list fields, an empty list is not treated as “preserve existing”
- omit the list field to preserve old content, or use the matching clear flag to remove it

## `replace`

Choose `replace` only when the old block is clearly no longer the right source of truth.

Typical signs:

- the old block is materially outdated
- the old block structure is poor enough that local edits are not worth it
- the new content confidently supersedes the old core claims

Do not use `replace` simply because the new phrasing sounds nicer.

## `split`

Choose `split` when one raw source clearly contains more than one leaf topic.

When splitting:

- create multiple operations
- assign each operation its own `path`
- then run the action ladder independently on each operation
- do not send a raw `action: "split"` operation to the updater script; expand it first

## Interaction With The Editorial Pass

Never choose the action based on the raw source text. Always:

1. normalize the source
2. run the editorial pass
3. infer topic paths
4. choose the action

This prevents verbose or repetitive raw input from being mistaken for meaningful new content.
