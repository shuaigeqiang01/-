def test_create_complete_list_and_patch_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "created_at" in item and "updated_at" in item

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/", params={"completed": True, "limit": 5, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.patch(f"/action-items/{item['id']}", json={"description": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["description"] == "Updated"


def test_get_single_action_item(client):
    r = client.post("/action-items/", json={"description": "Get me"})
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 200
    assert r.json()["description"] == "Get me"


def test_delete_action_item(client):
    r = client.post("/action-items/", json={"description": "Delete me"})
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.delete(f"/action-items/{item_id}")
    assert r.status_code == 204

    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 404


def test_action_item_validation(client):
    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422

    r = client.patch("/action-items/999", json={"description": ""})
    assert r.status_code == 422


def test_get_nonexistent_action_item(client):
    r = client.get("/action-items/9999")
    assert r.status_code == 404


def test_create_action_item_with_note_id(client):
    r = client.post("/notes/", json={"title": "N", "content": "c"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.post("/action-items/", json={"description": "From note", "note_id": note_id})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["note_id"] == note_id

    r = client.get("/action-items/", params={"note_id": note_id})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["note_id"] == note_id


def test_create_action_item_with_invalid_note_id(client):
    r = client.post("/action-items/", json={"description": "Bad", "note_id": 9999})
    assert r.status_code == 404


def test_patch_action_item_note_id(client):
    r = client.post("/notes/", json={"title": "N1", "content": "c"})
    assert r.status_code == 201
    note1 = r.json()["id"]

    r = client.post("/notes/", json={"title": "N2", "content": "c"})
    assert r.status_code == 201
    note2 = r.json()["id"]

    r = client.post("/action-items/", json={"description": "Movable", "note_id": note1})
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.patch(f"/action-items/{item_id}", json={"note_id": note2})
    assert r.status_code == 200
    assert r.json()["note_id"] == note2


