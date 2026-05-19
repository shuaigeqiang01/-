import re

CATEGORY_PREFIXES = {
    "todo": re.compile(r"^TODO[:]", re.IGNORECASE),
    "action": re.compile(r"^ACTION[:]", re.IGNORECASE),
    "fixme": re.compile(r"^FIXME[:]", re.IGNORECASE),
    "hack": re.compile(r"^HACK[:]", re.IGNORECASE),
    "bug": re.compile(r"^BUG[:]", re.IGNORECASE),
    "note": re.compile(r"^NOTE[:]", re.IGNORECASE),
    "important": re.compile(r"^IMPORTANT[:]", re.IGNORECASE),
}

HIGH_PRIORITY_MARKERS = ["URGENT", "CRITICAL", "!!", "P0"]

CHECKBOX_PATTERN = re.compile(r"^\s*[-*+]\s*\[\s*[ xX]?\s*\]")


def extract_action_items(text: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        entry = _classify_line(line)
        if entry:
            results.append(entry)
            continue

        stripped = re.sub(r"^[-*+]\s+", "", line)
        if stripped != line:
            entry = _classify_line(stripped)
            if entry:
                results.append(entry)

    return results


def _classify_line(line: str) -> dict[str, str] | None:
    category = None

    for cat, regex in CATEGORY_PREFIXES.items():
        if regex.match(line):
            category = cat
            break

    if category is None and CHECKBOX_PATTERN.match(line):
        category = "checkbox"

    if category is None and line.endswith("!"):
        category = "action"

    if category is None:
        return None

    display_text = line
    if category != "checkbox":
        display_text = re.sub(r"^[-*+]\s+", "", line)

    priority = "normal"
    if line.endswith("!") or any(marker in line.upper() for marker in HIGH_PRIORITY_MARKERS):
        priority = "high"

    return {"text": display_text, "category": category, "priority": priority}
