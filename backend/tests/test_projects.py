def test_create_list_patch_and_delete_project(client):
    r = client.post("/projects/", json={"name": "My Project", "description": "desc"})
    assert r.status_code == 201
    proj = r.json()
    assert proj["name"] == "My Project"
    assert "created_at" in proj and "updated_at" in proj

    r = client.get("/projects/")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    pid = proj["id"]
    r = client.get(f"/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "My Project"

    r = client.patch(f"/projects/{pid}", json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

    r = client.delete(f"/projects/{pid}")
    assert r.status_code == 204

    r = client.get(f"/projects/{pid}")
    assert r.status_code == 404


def test_project_relationships(client):
    r = client.post("/projects/", json={"name": "P"})
    pid = r.json()["id"]

    r = client.post("/notes/", json={"title": "N", "content": "c", "project_id": pid})
    assert r.status_code == 201
    assert r.json()["project_id"] == pid

    r = client.post("/action-items/", json={"description": "AI", "project_id": pid})
    assert r.status_code == 201
    assert r.json()["project_id"] == pid

    r = client.get(f"/projects/{pid}/notes")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get(f"/projects/{pid}/action-items")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_filter_by_project(client):
    r = client.post("/projects/", json={"name": "P1"})
    pid = r.json()["id"]

    client.post("/notes/", json={"title": "n1", "content": "c1", "project_id": pid})
    client.post("/notes/", json={"title": "n2", "content": "c2"})

    r = client.get("/notes/", params={"project_id": pid})
    assert len(r.json()) == 1

    r = client.get("/notes/")
    assert len(r.json()) >= 2


def test_cascade_delete_project(client):
    r = client.post("/projects/", json={"name": "ToDelete"})
    pid = r.json()["id"]

    client.post("/notes/", json={"title": "n", "content": "c", "project_id": pid})
    client.post("/action-items/", json={"description": "a", "project_id": pid})

    dr = client.delete(f"/projects/{pid}")
    assert dr.status_code == 204

    r = client.get(f"/projects/{pid}")
    assert r.status_code == 404


def test_project_validation(client):
    r = client.post("/projects/", json={"name": ""})
    assert r.status_code == 422

    r = client.get("/projects/9999")
    assert r.status_code == 404

    r = client.get("/projects/9999/notes")
    assert r.status_code == 404
