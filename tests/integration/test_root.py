def test_root_redirects_to_ui(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/ui/"

    ui_response = client.get("/ui/")

    assert ui_response.status_code == 200
    assert ui_response.headers["content-type"].startswith("text/html")
    assert 'href="/host"' in ui_response.text
    assert 'href="/play"' in ui_response.text
