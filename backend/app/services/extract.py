import re
from dataclasses import dataclass

_PREFIX_PATTERN = re.compile(
    r"^(todo|action|fixme|hack|bug)(\(.*?\))?:\s*", re.IGNORECASE
)

_CATEGORY_PRIORITY = {
    "fixme": 3,
    "bug": 3,
    "hack": 2,
    "urgent": 1,
    "todo": 1,
    "action": 1,
}


@dataclass
class ExtractedItem:
    content: str
    category: str
    priority: int


def extract_action_items(text: str) -> list[ExtractedItem]:
    lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
    results: list[ExtractedItem] = []

    for line in lines:
        m = _PREFIX_PATTERN.match(line)
        if m:
            category = m.group(1).lower()
            content = line[m.end() :].strip()
            priority = _CATEGORY_PRIORITY.get(category, 1)
            results.append(
                ExtractedItem(content=content, category=category, priority=priority)
            )
        elif line.endswith("!"):
            excl_count = len(line) - len(line.rstrip("!"))
            priority = 3 if excl_count >= 3 else 2 if excl_count >= 2 else 1
            results.append(
                ExtractedItem(content=line, category="urgent", priority=priority)
            )

    return results
