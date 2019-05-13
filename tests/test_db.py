import sqlite3

import pytest

from main.db import get_db


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e)


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('main.db.init_db', fake_init_db)
    result = runner.invoke(args=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called


def test_get_user(client):
    res = client.get('/user?id_tag=222')
    assert res.json[0]['username'] == 'bbb'
    assert res.json[0]['id_tag'] == '222'
    assert res.json[0]['repo'] == 'bbb/test'


# TODO: GET /grade
def test_get_grade(client):
    pass


# TODO: POST /grade
def test_post_grade(client):
    pass


# TODO: POST /user
def test_post_user(client):
    pass


# TODO: PUT /user
def test_put_user(client):
    pass
