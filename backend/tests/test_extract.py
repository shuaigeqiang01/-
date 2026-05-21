from backend.app.services.extract import ExtractedItem, extract_action_items


def test_extract_todo_and_action():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert len(items) == 2
    contents = [i.content for i in items]
    assert "write tests" in contents
    assert "review PR" in contents
    assert all(i.priority == 1 for i in items)


def test_extract_fixme():
    items = extract_action_items("- FIXME: memory leak in parser")
    assert len(items) == 1
    assert items[0].content == "memory leak in parser"
    assert items[0].category == "fixme"
    assert items[0].priority == 3


def test_extract_hack():
    items = extract_action_items("- HACK: workaround for IE11")
    assert len(items) == 1
    assert items[0].content == "workaround for IE11"
    assert items[0].category == "hack"
    assert items[0].priority == 2


def test_extract_bug():
    items = extract_action_items("- BUG: null pointer on empty list")
    assert len(items) == 1
    assert items[0].content == "null pointer on empty list"
    assert items[0].category == "bug"
    assert items[0].priority == 3


def test_extract_urgent_single_exclaim():
    items = extract_action_items("Ship it!")
    assert len(items) == 1
    assert items[0].content == "Ship it!"
    assert items[0].category == "urgent"
    assert items[0].priority == 1


def test_extract_urgent_double_exclaim():
    items = extract_action_items("Fix this now!!")
    assert len(items) == 1
    assert items[0].category == "urgent"
    assert items[0].priority == 2


def test_extract_urgent_triple_exclaim():
    items = extract_action_items("Server is down!!!")
    assert len(items) == 1
    assert items[0].category == "urgent"
    assert items[0].priority == 3


def test_extract_todo_with_name():
    items = extract_action_items("TODO(alice): update docs")
    assert len(items) == 1
    assert items[0].content == "update docs"
    assert items[0].category == "todo"


def test_extract_mixed():
    text = """
    - TODO: do something
    - FIXME: critical issue
    - Ship it!
    - Not this one
    - BUG: something broken!!
    """.strip()
    items = extract_action_items(text)
    assert len(items) == 4
    categories = {i.category for i in items}
    assert categories == {"todo", "fixme", "bug", "urgent"}


def test_extract_prefix_takes_priority_over_exclaim():
    items = extract_action_items("TODO: fix this!")
    assert len(items) == 1
    assert items[0].category == "todo"
    assert items[0].content == "fix this!"
    assert items[0].priority == 1
