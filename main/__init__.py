import os

from flask import Flask, request, jsonify, g
from main.db import get_db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'grade.sqlite'),
    )

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
        with open("/home/pandora/.ssh/authrized_key", 'a') as f:
            f.write("\n" + data['key'])
        return jsonify({'message': 'success'})

    @app.route('/grade', methods=['GET', 'POST'])
    def grade():
        db = get_db()
        if request.method == 'GET':
            username = request.args.get('username')
            test_grade = db.execute('''
                SELECT * FROM test WHERE user_id IN (
                    SELECT id FROM user WHERE username = ?
                ) ORDER BY test_time''', (username,)
                                    ).fetchall()
            if not test_grade:
                return jsonify({"error": "no such user"})
            return jsonify(list(map(
                lambda item: dict(zip(item.keys(), tuple(item))),
                test_grade)))
        if request.method == 'POST':
            data = request.json
            uid = db.execute("""SELECT id FROM user WHERE username = ?""", (data['username'],)).fetchone()['id']
            db.execute("""INSERT INTO test(user_id, test_status, error_log) VALUES (?, ?, ? )""",
                       (uid, data['test_status'], data['error_log']))
            try:
                db.commit()
                return jsonify({'message': 'success'})
            except Exception as e:
                print(e)
                return "error"

    @app.route('/user', methods=['GET', 'POST'])
    def user():
        db = get_db()
        if request.method == 'GET':
            """
            get user info
            """
            id_tag = request.args.get('id_tag')
            userinfo = db.execute('''
                SELECT USERNAME,ID_TAG,REPO FROM user WHERE id_tag=?
            ''', (id_tag,)
                                  ).fetchall()
            if not userinfo:
                return jsonify({"error": "no such user"})
            return jsonify(list(map(
                lambda item: dict(zip(item.keys(), tuple(item))),
                userinfo)))
        elif request.method == 'POST':
            """
            JSON Format:
            {
                "id_tag": "<string>",
                "username": "<string>",
                "repo": "<string> (Must be github repo url in https mode or just 'None')"
            }
            """
            data = request.json
            uid = db.execute("""SELECT id FROM user WHERE id_tag = ?""", (data['id_tag'],)).fetchone()['id']
            if uid:
                return jsonify({"error": "user exists"})
            else:
                db.execute("""INSERT INTO user(username, id_tag, repo) VALUES (?, ?, ? )""",
                           (data['username'], data['id_tag'], data['repo']))
            try:
                db.commit()
                return jsonify({'message': 'success'})
            except Exception as e:
                db.rollback()
                print(e)
                return "error"

    from . import db
    db.init_app(app)

    return app
