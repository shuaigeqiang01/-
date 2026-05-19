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


