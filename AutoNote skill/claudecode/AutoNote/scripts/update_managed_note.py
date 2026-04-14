import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4


BLOCK_PATTERN = re.compile(
    r'<!-- AUTONOTE:BEGIN path="(?P<path>[^"]+)" -->\n(?P<body>.*?)\n<!-- AUTONOTE:END -->',
    re.DOTALL,
)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
LAST_UPDATED_PATTERN = re.compile(r"^_Last Updated:\s+(.+?)_$")
SUPPORTED_ACTIONS = {"append", "merge", "replace", "no_op", "split"}


@dataclass
class ManagedBlock:
    path: str
    title: str
    summary: str
    key_points: List[str]
    details: List[str]
    source_notes: List[str]
    raw_text: str
    start: int
    end: int


def normalize_topic_name(value: str) -> str:
    cleaned = re.sub(r"\s+", "", value or "")
    cleaned = cleaned.replace("（", "(").replace("）", ")")
    cleaned = cleaned.replace("“", "").replace("”", "").replace("'", "").replace('"', "")
    return cleaned.lower()


def normalize_block_text(text: str) -> str:
    normalized_lines = []
    blank_pending = False
    for raw_line in text.strip().splitlines():
        if LAST_UPDATED_PATTERN.match(raw_line.strip()):
            continue
        line = raw_line.rstrip()
        if not line.strip():
            if not blank_pending:
                normalized_lines.append("")
            blank_pending = True
            continue
        normalized_lines.append(line.strip())
        blank_pending = False
    return "\n".join(normalized_lines).strip()


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        normalized = normalize_topic_name(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(item)
    return result


def validate_operation(operation: Dict) -> None:
    path = operation.get("path")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Each AutoNote operation must include a non-empty 'path'.")

    action = operation.get("action", "merge")
    if action not in SUPPORTED_ACTIONS:
        raise ValueError(f"Unsupported AutoNote action: {action}")
    if action == "split":
        raise ValueError("AutoNote 'split' operations must be expanded into multiple concrete operations before calling the updater.")

    title = operation.get("title")
    if title is not None and not isinstance(title, str):
        raise ValueError("Operation 'title' must be a string when provided.")

    for field in ("aliases", "key_points", "details", "source_notes"):
        if field in operation and not isinstance(operation[field], list):
            raise ValueError(f"Operation '{field}' must be a list when provided.")


def validate_payload(payload: Dict) -> None:
    target_file = payload.get("target_file")
    if not isinstance(target_file, str) or not target_file.strip():
        raise ValueError("Payload must include a non-empty 'target_file'.")
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise ValueError("Payload must include an 'operations' list.")


def validate_merge_field_semantics(existing: Optional[ManagedBlock], operation: Dict) -> None:
    if not existing or operation.get("action", "merge") != "merge":
        return

    for field_name in ("key_points", "details", "source_notes"):
        clear_flag = f"clear_{field_name}"
        if field_name in operation and operation.get(field_name) == [] and not operation.get(clear_flag):
            raise ValueError(
                f"Merge operation provided an empty '{field_name}' list without '{clear_flag}: true'. "
                f"Omit the field to preserve existing content, or use the clear flag to remove it."
            )


def resolve_scalar_field(existing_value: str, operation: Dict, field_name: str) -> str:
    clear_flag = f"clear_{field_name}"
    if operation.get(clear_flag):
        return ""
    if field_name in operation:
        return operation.get(field_name, "")
    return existing_value


def resolve_list_field(existing_value: List[str], operation: Dict, field_name: str) -> List[str]:
    clear_flag = f"clear_{field_name}"
    if operation.get(clear_flag):
        return []
    if field_name in operation:
        return list(operation.get(field_name) or [])
    return list(existing_value)


def parse_block(match: re.Match) -> ManagedBlock:
    path = match.group("path")
    raw_text = match.group(0)
    body = match.group("body")
    lines = body.splitlines()

    title = path.split("/")[-1]
    if lines:
        first_line = lines[0].strip()
        heading_match = HEADING_PATTERN.match(first_line)
        if heading_match:
            title = heading_match.group(2).strip()

    summary_lines: List[str] = []
    key_points: List[str] = []
    details: List[str] = []
    source_notes: List[str] = []
    section: Optional[str] = None

    for line in lines[1:]:
        stripped = line.strip()
        if LAST_UPDATED_PATTERN.match(stripped):
            continue
        if stripped == "**Summary**":
            section = "summary"
            continue
        if stripped == "##### Key Points":
            section = "key_points"
            continue
        if stripped == "##### Details":
            section = "details"
            continue
        if stripped == "##### Source Notes":
            section = "source_notes"
            continue
        if not stripped:
            continue
        if section == "summary":
            summary_lines.append(stripped)
        elif section == "key_points" and stripped.startswith("- "):
            key_points.append(stripped[2:].strip())
        elif section == "details" and stripped.startswith("- "):
            details.append(stripped[2:].strip())
        elif section == "source_notes" and stripped.startswith("- "):
            source_notes.append(stripped[2:].strip())

    return ManagedBlock(
        path=path,
        title=title,
        summary=" ".join(summary_lines).strip(),
        key_points=key_points,
        details=details,
        source_notes=source_notes,
        raw_text=raw_text,
        start=match.start(),
        end=match.end(),
    )


def parse_managed_blocks(note_text: str) -> List[ManagedBlock]:
    return [parse_block(match) for match in BLOCK_PATTERN.finditer(note_text)]


def render_block(
    path: str,
    title: str,
    summary: str,
    key_points: List[str],
    details: List[str],
    source_notes: List[str],
    timestamp: str,
) -> str:
    lines = [
        f'<!-- AUTONOTE:BEGIN path="{path}" -->',
        f"#### {title}",
        f"_Last Updated: {timestamp}_",
        "",
        "**Summary**",
        summary.strip(),
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
    for item in source_notes or ["AutoNote update."]:
        lines.append(f"- {item}")
    lines.append("<!-- AUTONOTE:END -->")
    return "\n".join(lines)


def compose_block(existing: Optional[ManagedBlock], operation: Dict, matched_path: str, matched_title: str) -> str:
    action = operation.get("action", "merge")
    summary = operation.get("summary", "")
    key_points = list(operation.get("key_points", []))
    details = list(operation.get("details", []))
    source_notes = list(operation.get("source_notes", []))

    if existing and action == "append":
        summary = existing.summary
        key_points = unique_preserve_order(existing.key_points + key_points)
        details = unique_preserve_order(existing.details + details)
        source_notes = unique_preserve_order(existing.source_notes + source_notes)
    elif existing and action == "merge":
        summary = resolve_scalar_field(existing.summary, operation, "summary")
        key_points = resolve_list_field(existing.key_points, operation, "key_points")
        details = resolve_list_field(existing.details, operation, "details")
        source_notes = resolve_list_field(existing.source_notes, operation, "source_notes")
    elif action == "replace":
        summary = resolve_scalar_field("", operation, "summary")
        key_points = resolve_list_field([], operation, "key_points")
        details = resolve_list_field([], operation, "details")
        source_notes = resolve_list_field([], operation, "source_notes")

    return render_block(
        path=matched_path,
        title=matched_title,
        summary=summary,
        key_points=key_points,
        details=details,
        source_notes=source_notes,
        timestamp=operation["_timestamp"],
    )


def find_matching_block(operation: Dict, blocks: List[ManagedBlock]) -> Optional[ManagedBlock]:
    path = operation.get("path", "")
    for block in blocks:
        if block.path == path:
            return block

    candidates = [normalize_topic_name(alias) for alias in operation.get("aliases", [])]
    candidates.append(normalize_topic_name(path.split("/")[-1] if path else ""))
    candidates = [candidate for candidate in candidates if candidate]

    for block in blocks:
        block_values = {
            normalize_topic_name(block.title),
            normalize_topic_name(block.path.split("/")[-1]),
        }
        if any(candidate in block_values for candidate in candidates):
            return block
    return None


def ensure_base_note(note_text: str) -> str:
    stripped = note_text.strip()
    if stripped:
        return note_text
    return "# Technotes\n\n## 更新记录\n"


def find_heading_index(lines: List[str], heading: str, start: int, end: int) -> Optional[int]:
    for index in range(start, end):
        if lines[index].strip() == heading:
            return index
    return None


def find_section_end(lines: List[str], start_index: int, level: int, limit: int) -> int:
    for index in range(start_index + 1, limit):
        match = HEADING_PATTERN.match(lines[index].strip())
        if match and len(match.group(1)) <= level:
            return index
    return limit


def ensure_update_log(lines: List[str]) -> int:
    for index, line in enumerate(lines):
        if line.strip() == "## 更新记录":
            return index
    if lines and lines[-1].strip():
        lines.append("")
    lines.append("## 更新记录")
    lines.append("")
    return len(lines) - 2


def insert_block(note_text: str, path: str, block_text: str) -> str:
    lines = note_text.rstrip("\n").splitlines()
    if not lines:
        lines = ["# Technotes", "", "## 更新记录", ""]

    update_log_index = ensure_update_log(lines)
    insertion_index = update_log_index
    current_start = 0
    current_end = update_log_index
    categories = path.split("/")[:-1]

    for depth, segment in enumerate(categories):
        level = depth + 2
        heading = "{} {}".format("#" * level, segment)
        found_index = find_heading_index(lines, heading, current_start, current_end)
        if found_index is None:
            to_insert = []
            if insertion_index > 0 and lines[insertion_index - 1].strip():
                to_insert.append("")
            to_insert.append(heading)
            lines[insertion_index:insertion_index] = to_insert
            added_count = len(to_insert)
            update_log_index += added_count
            found_index = insertion_index + added_count - 1
            current_start = found_index + 1
            current_end = update_log_index
            insertion_index = update_log_index
        else:
            current_start = found_index + 1
            current_end = find_section_end(lines, found_index, level, update_log_index)
            insertion_index = current_end

    block_lines = block_text.splitlines()
    to_insert = []
    if insertion_index > 0 and lines[insertion_index - 1].strip():
        to_insert.append("")
    to_insert.extend(block_lines)
    to_insert.append("")
    lines[insertion_index:insertion_index] = to_insert
    return "\n".join(lines).rstrip() + "\n"


def append_update_log(note_text: str, changed_paths: List[str], timestamp: str) -> str:
    unique_paths = []
    for path in changed_paths:
        if path not in unique_paths:
            unique_paths.append(path)

    lines = note_text.rstrip("\n").splitlines()
    update_log_index = ensure_update_log(lines)

    insert_index = len(lines)
    for index in range(update_log_index + 1, len(lines)):
        if lines[index].startswith("## "):
            insert_index = index
            break

    entries = [f"- {timestamp} 更新 `{path}`" for path in unique_paths]
    if insert_index > update_log_index + 1 and lines[insert_index - 1].strip():
        entries.insert(0, "")
    lines[insert_index:insert_index] = entries
    return "\n".join(lines).rstrip() + "\n"


def sanitized_timestamp(timestamp: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "-", timestamp.strip())
    return cleaned.strip("-") or "autonote-backup"


class LockFile:
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.fd: Optional[int] = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"AutoNote lock already exists: {self.lock_path}") from exc
        os.write(self.fd, str(os.getpid()).encode("utf-8"))
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        if self.lock_path.exists():
            self.lock_path.unlink()


def write_text_atomically(target_file: Path, text: str) -> None:
    target_file.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_file.parent / f".{target_file.name}.{uuid4().hex}.tmp"
    temp_path.write_text(text, encoding="utf-8")
    os.replace(str(temp_path), str(target_file))


def apply_operations(note_text: str, operations: List[Dict], current_timestamp: str) -> str:
    text = ensure_base_note(note_text)
    changed_paths: List[str] = []

    for operation in operations:
        operation = dict(operation)
        validate_operation(operation)
        action = operation.get("action", "merge")
        operation["_timestamp"] = current_timestamp

        blocks = parse_managed_blocks(text)
        existing = find_matching_block(operation, blocks)

        if existing:
            matched_path = existing.path
            matched_title = existing.title
        else:
            matched_path = operation.get("path", "")
            matched_title = operation.get("title") or matched_path.split("/")[-1]

        validate_merge_field_semantics(existing, operation)

        if action == "no_op":
            continue

        rendered = compose_block(existing, operation, matched_path, matched_title)
        if existing and normalize_block_text(existing.raw_text) == normalize_block_text(rendered):
            continue

        if existing:
            text = text[: existing.start] + rendered + text[existing.end :]
        else:
            text = insert_block(text, matched_path, rendered)
        changed_paths.append(matched_path)

    if changed_paths:
        text = append_update_log(text, changed_paths, current_timestamp)
    return text


def apply_payload(payload: Dict, timestamp: str) -> Dict:
    validate_payload(payload)
    target_file = Path(payload["target_file"])
    lock_path = target_file.with_name(f"{target_file.name}.autonote.lock")
    backup_file: Optional[Path] = None

    with LockFile(lock_path):
        existing_text = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
        updated_text = apply_operations(existing_text, payload.get("operations", []), timestamp)
        updated = updated_text != existing_text

        if updated:
            if target_file.exists():
                backup_name = f"{target_file.stem}.autonote-{sanitized_timestamp(timestamp)}.bak{target_file.suffix}"
                backup_file = target_file.with_name(backup_name)
                backup_file.write_text(existing_text, encoding="utf-8")
            write_text_atomically(target_file, updated_text)

    return {
        "target_file": str(target_file),
        "updated": updated,
        "backup_file": str(backup_file) if backup_file else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Apply AutoNote managed block updates to a Markdown note.")
    parser.add_argument("--payload-file", required=True, help="Path to a JSON payload file.")
    parser.add_argument("--timestamp", required=True, help="Timestamp string for _Last Updated_ and update log.")
    args = parser.parse_args()

    payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    result = apply_payload(payload, args.timestamp)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
