import os

from flask import Flask, request, jsonify
from flask_cors import CORS

from main.db import get_db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'grade.sqlite'),
    )

    if 'dbauth' in os.environ:
        dbauth = os.environ.get('dbauth')
    else:
        dbauth = 'changeit'
        print("dbauth not found, using temporary key")

    if test_config:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def index():
        return 'here is nothing to show.'

    @app.route('/ssh', methods=['POST'])
    def ssh_key_copy():
        """
        JSON Format:
        {
          "key": "ssh-rsa ..."
        }
        """
        data = request.json
        if not data['key'].startswith("ssh-rsa"):
            return jsonify({'error': 'wrong key'})
        with open("/home/pandora/.ssh/authorized_key", 'a') as f:
            f.write("\n" + data['key'])
        return jsonify({'message': 'success'})

    @app.route('/grade', methods=['GET', 'POST'])
    def grade():
        """
        GET: ?id_tag=<id_tag>
        :return: [{<test_row>}]
        POST: JSON Format:
        {
            "id_tag": <id_tag: str>,
            "test_status": <test_status: passed|failure>,
            "error_log": <error_log: str>,
            "repo": <repo: str>
        }
        :return: {"message": "success"} | {"error": "insert error"}
        """
        db = get_db()
        if request.method == 'GET':
            id_tag = request.args.get('id_tag')
            try:
                uid = db.execute("""SELECT id FROM user WHERE id_tag = ?""", (id_tag,)).fetchone()['id']
            except:
                return jsonify({"error": "no such user"})
            test_grade = db.execute('''SELECT * FROM test WHERE user_id=? ORDER BY test_time''', (uid,)).fetchall()
            if not test_grade:
                return jsonify([])
            return jsonify(list(map(
                lambda item: dict(zip(item.keys(), tuple(item))),
                test_grade)))
        if request.method == 'POST':
            if 'X-DB-Auth' not in request.headers or not request.headers.get('X-DB-Auth') == dbauth:
                return jsonify({"error": "missing header"})
            data = request.json
            try:
                uid = db.execute("""SELECT id FROM user WHERE id_tag = ?""", (data['id_tag'],)).fetchone()['id']
            except:
                return jsonify({'error': 'no such user'})
            try:
                db.execute("""INSERT INTO test(user_id, test_status, error_log, repo) VALUES (?, ?, ?, ?)""",
                           (uid, data['test_status'], data['error_log'], data['repo']))
                db.commit()
                return jsonify({'message': 'success'})
            except Exception as e:
                db.rollback()
                print(e)
                return jsonify({'error': 'insert error'})

    @app.route('/user', methods=['GET', 'POST', 'PUT'])
    def user():
        """
        GET: Query String: ?id_tag=<id_tag>
        :return: [{<user_row>}]
        POST: JSON Format:
        {
            "id_tag": "<string>",
            "username": "<string>",
            "repo": "<string> (Must be github repo url in https mode or just 'None')"
        }
        :return: {'message': 'success'}|{"error": "user exists"}
        PUT: JSON Format:
        {
            "id_tag": "<string>",
            "repo": "<string> (Must be github repo url in https mode or just 'None')"
        }
        :return: {'message': 'success'}|{"error": "no such user"}
        """
        db = get_db()
        if request.method == 'GET':
            id_tag = request.args.get('id_tag')
            userinfo = db.execute('''
                SELECT USERNAME,ID_TAG,REPO FROM user WHERE id_tag=?
            ''', (id_tag,)).fetchall()
            if not userinfo:
                return jsonify({"error": "no such user"})
            return jsonify(list(map(
                lambda item: dict(zip(item.keys(), tuple(item))),
                userinfo)))
        elif request.method == 'POST':
            if 'X-DB-Auth' not in request.headers or not request.headers.get('X-DB-Auth') == dbauth:
                return jsonify({"error": "missing header"})
            data = request.json
            try:
                uid = db.execute("""SELECT id FROM user WHERE id_tag = ?""", (data['id_tag'],)).fetchone()['id']
                if uid:
                    return jsonify({"error": "user exists"})
            except:
                pass

            try:
                db.execute("""INSERT INTO user(username, id_tag, repo) VALUES (?, ?, ? )""",
                           (data['username'], data['id_tag'], data.get('repo')))
                db.commit()
                return jsonify({'message': 'success'})
            except Exception as e:
                db.rollback()
                print(e)
                return jsonify({"error": "insert error"})
        elif request.method == 'PUT':
            if 'X-DB-Auth' not in request.headers or not request.headers.get('X-DB-Auth') == dbauth:
                return jsonify({"error": "missing header"})
            data = request.json
            try:
                uid = db.execute("""SELECT id FROM user WHERE id_tag = ?""", (data['id_tag'],)).fetchone()['id']
            except:
                return jsonify({"error": "no such user"})
            else:
                print(data)
                db.execute("""UPDATE user set repo=? WHERE id_tag=? and id=?""",
                           (data['repo'], data['id_tag'], uid))
            try:
                db.commit()
                return jsonify({'message': 'success'})
            except Exception as e:
                db.rollback()
                print(e)
                return jsonify({"error": "update error"})

    from . import db
    db.init_app(app)

    return app
	
app = create_app()
