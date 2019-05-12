from main import create_app


def test_index(client):
    response = client.get("/")
    assert response.data == b'here is nothing to show.'
