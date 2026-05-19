"""Dedicated tests for pagination and sorting across all list endpoints."""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _seed_items(client, count, endpoint, template):
    """Create *count* items and return their ids."""
    ids = []
    for i in range(count):
        payload = {k: v.format(i=i) if isinstance(v, str) else v for k, v in template.items()}
        r = client.post(endpoint, json=payload)
        assert r.status_code == 201
        ids.append(r.json()["id"])
    return ids


# ── Notes pagination & sorting ───────────────────────────────────────────────


def test_notes_pagination(client):
    _seed_items(client, 5, "/notes/", {"title": "Note {i}", "content": "body {i}"})

    r = client.get("/notes/", params={"skip": 0, "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get("/notes/", params={"skip": 2, "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get("/notes/", params={"skip": 4, "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get("/notes/", params={"skip": 10, "limit": 10})
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_notes_pagination_boundaries(client):
    _seed_items(client, 3, "/notes/", {"title": "B {i}", "content": "x"})

    r = client.get("/notes/", params={"limit": 0})
    assert r.status_code == 200
    assert len(r.json()) == 0

    r = client.get("/notes/", params={"limit": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get("/notes/", params={"limit": 200})
    assert r.status_code == 200
    assert len(r.json()) >= 3

    r = client.get("/notes/", params={"limit": 201})
    assert r.status_code == 422

    r = client.get("/notes/", params={"skip": -1})
    assert r.status_code == 422


def test_notes_sort_ascending(client):
    _seed_items(client, 3, "/notes/", {"title": "Z {i}", "content": "x"})

    r = client.get("/notes/", params={"sort": "title"})
    assert r.status_code == 200
    titles = [n["title"] for n in r.json()]
    assert titles == sorted(titles)


def test_notes_sort_descending(client):
    _seed_items(client, 3, "/notes/", {"title": "Z {i}", "content": "x"})

    r = client.get("/notes/", params={"sort": "-title"})
    assert r.status_code == 200
    titles = [n["title"] for n in r.json()]
    assert titles == sorted(titles, reverse=True)


def test_notes_sort_default(client):
    _seed_items(client, 3, "/notes/", {"title": "D {i}", "content": "x"})

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    dates = [i["created_at"] for i in items]
    assert dates == sorted(dates, reverse=True)


def test_notes_sort_invalid_field(client):
    _seed_items(client, 2, "/notes/", {"title": "N {i}", "content": "x"})

    r = client.get("/notes/", params={"sort": "nonexistent"})
    assert r.status_code == 200
    items = r.json()
    dates = [i["created_at"] for i in items]
    assert dates == sorted(dates, reverse=True)


# ── Action Items pagination & sorting ────────────────────────────────────────


def test_action_items_pagination(client):
    _seed_items(client, 5, "/action-items/", {"description": "Item {i}"})

    r = client.get("/action-items/", params={"skip": 0, "limit": 2})
    assert len(r.json()) == 2

    r = client.get("/action-items/", params={"skip": 3, "limit": 2})
    assert len(r.json()) == 2

    r = client.get("/action-items/", params={"skip": 10, "limit": 5})
    assert len(r.json()) == 0


def test_action_items_sort_on_boolean_field(client):
    _seed_items(client, 3, "/action-items/", {"description": "Sort me {i}"})

    r = client.get("/action-items/", params={"sort": "completed"})
    assert r.status_code == 200
    assert len(r.json()) >= 3


def test_action_items_limit_validation(client):
    r = client.get("/action-items/", params={"limit": 201})
    assert r.status_code == 422

    r = client.get("/action-items/", params={"limit": -1})
    assert r.status_code == 422


# ── Projects pagination & sorting ────────────────────────────────────────────


def test_projects_pagination(client):
    for i in range(5):
        client.post("/projects/", json={"name": f"P{i}"})

    r = client.get("/projects/", params={"skip": 2, "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get("/projects/", params={"skip": 10, "limit": 5})
    assert r.json() == []


def test_projects_sort_by_name(client):
    client.post("/projects/", json={"name": "Zebra"})
    client.post("/projects/", json={"name": "Alpha"})
    client.post("/projects/", json={"name": "Mango"})

    r = client.get("/projects/", params={"sort": "name"})
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert names == sorted(names)


def test_projects_limit_validation(client):
    r = client.get("/projects/", params={"limit": 201})
    assert r.status_code == 422


# ── Nested routes ────────────────────────────────────────────────────────────


def test_nested_project_notes_pagination(client):
    r = client.post("/projects/", json={"name": "P"})
    pid = r.json()["id"]
    _seed_items(client, 5, "/notes/", {"title": "N {i}", "content": "c", "project_id": pid})

    r = client.get(f"/projects/{pid}/notes", params={"skip": 2, "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get(f"/projects/{pid}/notes", params={"skip": 0, "limit": 200})
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_nested_project_action_items_pagination(client):
    r = client.post("/projects/", json={"name": "P"})
    pid = r.json()["id"]
    _seed_items(client, 4, "/action-items/", {"description": "A {i}", "project_id": pid})

    r = client.get(f"/projects/{pid}/action-items", params={"skip": 1, "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get(f"/projects/{pid}/action-items", params={"completed": False})
    assert r.status_code == 200
    assert len(r.json()) == 4
