def test_host_page_returns_html(client):
    response = client.get("/host")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PicMe" in response.text


def test_play_page_returns_html(client):
    response = client.get("/play")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PicMe" in response.text


def test_play_page_accepts_game_code(client):
    response = client.get("/play?code=ABC234")

    assert response.status_code == 200
