from backend.app.services.extract import extract_action_items


def test_extract_action_items_original_patterns():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    texts = [i["text"] for i in items]
    assert "TODO: write tests" in texts
    assert "ACTION: review PR" in texts
    assert "Ship it!" in texts
    assert all("category" in i and "priority" in i for i in items)


def test_extract_new_prefixes():
    items = extract_action_items("FIXME: broken config\nNOTE: reminder\nBUG: null deref")
    categories = {i["category"] for i in items}
    assert "fixme" in categories
    assert "note" in categories
    assert "bug" in categories
    assert len(items) == 3


def test_extract_markdown_checkbox():
    items = extract_action_items("- [ ] Buy milk\n* [x] Done task\n  - [ ] Walk dog")
    assert len(items) == 3
    assert all(i["category"] == "checkbox" for i in items)
    assert items[0]["text"].strip("- ").startswith("[ ]")


def test_extract_priority():
    items = extract_action_items("TODO: normal\nURGENT: fix this!\nShip it!")
    item = next(i for i in items if "URGENT" in i["text"])
    assert item["priority"] == "high"
    ship = next(i for i in items if "Ship" in i["text"])
    assert ship["priority"] == "high"


def test_extract_empty_input():
    assert extract_action_items("") == []
    assert extract_action_items("No actionable items here.") == []


def test_extract_ignores_plain_lines():
    items = extract_action_items("Regular note\nAnother line")
    assert items == []
