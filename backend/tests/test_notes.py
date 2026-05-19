def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"


def test_delete_note(client):
    r = client.post("/notes/", json={"title": "Del", "content": "me"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204

    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 404


def test_note_validation(client):
    r = client.post("/notes/", json={"title": "", "content": ""})
    assert r.status_code == 422

    r = client.post("/notes/", json={"title": "OK", "content": ""})
    assert r.status_code == 422

    r = client.patch("/notes/999", json={"title": ""})
    assert r.status_code == 422


def test_get_nonexistent_note(client):
    r = client.get("/notes/9999")
    assert r.status_code == 404


def test_note_title_max_length(client):
    r = client.post("/notes/", json={"title": "x" * 201, "content": "ok"})
    assert r.status_code == 422


def test_extract_endpoint(client):
    r = client.post("/notes/extract", json={"text": "TODO: fix bug\nNothing here\nShip it!"})
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) == 2
    categories = {i["category"] for i in items}
    assert categories == {"todo", "urgent"}

    r = client.post("/notes/extract", json={"text": ""})
    assert r.status_code == 422


def test_create_note_with_tags(client):
    r = client.post("/tags/", json={"name": "urgent"})
    assert r.status_code == 201
    tag_id = r.json()["id"]

    r = client.post("/notes/", json={"title": "Tagged", "content": "note", "tag_ids": [tag_id]})
    assert r.status_code == 201, r.text
    data = r.json()
    assert len(data["tags"]) == 1
    assert data["tags"][0]["id"] == tag_id
    assert data["tags"][0]["name"] == "urgent"


def test_patch_note_tags(client):
    r = client.post("/tags/", json={"name": "v1"})
    assert r.status_code == 201
    tag1 = r.json()["id"]

    r = client.post("/tags/", json={"name": "v2"})
    assert r.status_code == 201
    tag2 = r.json()["id"]

    r = client.post("/notes/", json={"title": "T", "content": "c", "tag_ids": [tag1]})
    assert r.status_code == 201
    note_id = r.json()["id"]
    assert len(r.json()["tags"]) == 1

    r = client.patch(f"/notes/{note_id}", json={"tag_ids": [tag1, tag2]})
    assert r.status_code == 200
    assert len(r.json()["tags"]) == 2

    r = client.patch(f"/notes/{note_id}", json={"tag_ids": []})
    assert r.status_code == 200
    assert len(r.json()["tags"]) == 0


def test_create_note_with_invalid_tag(client):
    r = client.post("/notes/", json={"title": "T", "content": "c", "tag_ids": [9999]})
    assert r.status_code == 404




