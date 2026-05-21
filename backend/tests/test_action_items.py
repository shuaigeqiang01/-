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


def test_action_items_pagination(client):
    for i in range(5):
        client.post("/action-items/", json={"description": f"Item {i}"})

    r = client.get("/action-items/", params={"skip": 0, "limit": 2, "sort": "description"})
    assert r.status_code == 200
    page1 = r.json()
    assert len(page1) == 2

    r = client.get("/action-items/", params={"skip": 2, "limit": 2, "sort": "description"})
    page2 = r.json()
    assert len(page2) == 2
    ids_page1 = {item["id"] for item in page1}
    ids_page2 = {item["id"] for item in page2}
    assert ids_page1.isdisjoint(ids_page2)

    r = client.get("/action-items/", params={"skip": 4, "limit": 2, "sort": "description"})
    assert len(r.json()) == 1

    r = client.get("/action-items/", params={"skip": 10, "limit": 2})
    assert r.json() == []


def test_action_items_sorting(client):
    client.post("/action-items/", json={"description": "B item"})
    client.post("/action-items/", json={"description": "A item"})
    client.post("/action-items/", json={"description": "C item"})

    r = client.get("/action-items/", params={"sort": "description"})
    descs = [item["description"] for item in r.json()]
    assert descs == ["A item", "B item", "C item"]

    r = client.get("/action-items/", params={"sort": "-description"})
    descs = [item["description"] for item in r.json()]
    assert descs == ["C item", "B item", "A item"]

    # Sort by completed
    r = client.get("/action-items/", params={"sort": "completed"})
    assert r.status_code == 200


def test_action_items_sort_invalid_field(client):
    client.post("/action-items/", json={"description": "Test"})
    r = client.get("/action-items/", params={"sort": "bad_field"})
    assert r.status_code == 200
    assert len(r.json()) >= 1


