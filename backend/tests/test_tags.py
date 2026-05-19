def test_create_list_and_patch_tag(client):
    r = client.post("/tags/", json={"name": "bug"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["name"] == "bug"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/tags/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/tags/", params={"limit": 10, "sort": "-name"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    tag_id = data["id"]
    r = client.patch(f"/tags/{tag_id}", json={"name": "feature"})
    assert r.status_code == 200
    assert r.json()["name"] == "feature"


def test_delete_tag(client):
    r = client.post("/tags/", json={"name": "temp"})
    assert r.status_code == 201
    tag_id = r.json()["id"]

    r = client.delete(f"/tags/{tag_id}")
    assert r.status_code == 204

    r = client.get(f"/tags/{tag_id}")
    assert r.status_code == 404


def test_tag_validation(client):
    r = client.post("/tags/", json={"name": ""})
    assert r.status_code == 422

    r = client.post("/tags/", json={"name": "a" * 51})
    assert r.status_code == 422

    r = client.patch("/tags/999", json={"name": ""})
    assert r.status_code == 422


def test_tag_unique_name(client):
    r = client.post("/tags/", json={"name": "unique"})
    assert r.status_code == 201

    r = client.post("/tags/", json={"name": "unique"})
    assert r.status_code == 409

    r = client.get("/tags/9999")
    assert r.status_code == 404


def test_tags_pagination(client):
    for i in range(5):
        client.post("/tags/", json={"name": f"tag-{i}"})

    r = client.get("/tags/", params={"skip": 0, "limit": 2, "sort": "name"})
    assert r.status_code == 200
    page1 = r.json()
    assert len(page1) == 2

    r = client.get("/tags/", params={"skip": 2, "limit": 2, "sort": "name"})
    page2 = r.json()
    assert len(page2) == 2
    ids_page1 = {item["id"] for item in page1}
    ids_page2 = {item["id"] for item in page2}
    assert ids_page1.isdisjoint(ids_page2)

    r = client.get("/tags/", params={"skip": 4, "limit": 2, "sort": "name"})
    assert len(r.json()) == 1

    r = client.get("/tags/", params={"skip": 10, "limit": 2})
    assert r.json() == []


def test_tags_sorting(client):
    client.post("/tags/", json={"name": "b-tag"})
    client.post("/tags/", json={"name": "a-tag"})
    client.post("/tags/", json={"name": "c-tag"})

    r = client.get("/tags/", params={"sort": "name"})
    names = [item["name"] for item in r.json()]
    assert names == ["a-tag", "b-tag", "c-tag"]

    r = client.get("/tags/", params={"sort": "-name"})
    names = [item["name"] for item in r.json()]
    assert names == ["c-tag", "b-tag", "a-tag"]


def test_tags_sort_invalid_field(client):
    client.post("/tags/", json={"name": "test"})
    r = client.get("/tags/", params={"sort": "nope"})
    assert r.status_code == 200
    assert len(r.json()) >= 1
