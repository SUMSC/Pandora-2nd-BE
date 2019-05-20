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


def test_get_grade(client):
    res = client.get('/grade?id_tag=111')
    assert res.json[0]['user_id'] == 1
    assert res.json[0]['test_status'] == 'passed'
    assert res.json[0]['error_log'] == 'ok'

    res = client.get('/grade?id_tag=222')
    assert res.json[0]['user_id'] == 2
    assert res.json[0]['test_status'] == 'passed'
    assert res.json[0]['error_log'] == 'ok'

    res = client.get('/grade?id_tag=333')
    assert res.json[0]['user_id'] == 3
    assert res.json[0]['test_status'] == 'failure'
    assert res.json[0]['error_log'] == 'error'

    res = client.get('/grade?id_tag=2')
    assert res.json.get('error') == 'no such user'


def test_post_grade(client):
    res = client.post('/grade', headers={'X-DB-Auth': 'changeit'}, json={
        "id_tag": "333",
        "test_status": "passed",
        "error_log": "ok",
        "repo": "https://teset.git"
    })
    assert res.json.get('message') == 'success'

    res = client.post('/grade', headers={'X-DB-Auth': 'wrong'}, json={
        "id_tag": "333",
        "test_status": "passed",
        "error_log": "ok",
        "repo": "https://teset.git"
    })
    assert res.json.get('error') == 'missing header'

    res = client.post('/grade', json={
        "id_tag": "333",
        "test_status": "passed",
        "error_log": "ok",
        "repo": "https://teset.git"
    })
    assert res.json.get('error') == 'missing header'

    res = client.post('/grade', headers={'X-DB-Auth': 'changeit'}, json={
        "id_tag": "wrong",
        "test_status": "passed",
        "error_log": "ok",
        "repo": "https://teset.git"
    })
    assert res.json.get('error') == 'no such user'


def test_post_user(client):
    res = client.post('/user', headers={'X-DB-Auth': 'changeit'}, json={
        "id_tag": "666",
        "username": "temp",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('message') == 'success'

    res = client.post('/user', headers={'X-DB-Auth': 'wrong'}, json={
        "id_tag": "666",
        "username": "temp",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('error') == 'missing header'

    res = client.post('/user', json={
        "id_tag": "666",
        "username": "temp",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('error') == 'missing header'

    res = client.post('/user', headers={'X-DB-Auth': 'changeit'}, json={
        "id_tag": "111",
        "username": "temp",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('error') == 'user exists'


def test_put_user(client):
    res = client.put('/user', headers={'X-DB-Auth': 'changeit'}, json={
        "id_tag": "111",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('message') == 'success'

    res = client.put('/user', headers={'X-DB-Auth': 'wrong'}, json={
        "id_tag": "111",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('error') == 'missing header'

    res = client.put('/user', json={
        "id_tag": "111",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('error') == 'missing header'

    res = client.put('/user', headers={'X-DB-Auth': 'changeit'}, json={
        "id_tag": "999",
        "repo": "https://github.com/temp.git"
    })
    assert res.json.get('error') == 'no such user'
