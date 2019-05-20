import os
import sys
import logging

from flask import Flask, request, jsonify

from main.db import get_db
import sqlite3
from flask_cors import CORS


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app=app)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'grade.sqlite'),
    )

    if 'dbauth' in os.environ:
        dbauth = os.environ.get('dbauth')
    else:
        dbauth = 'changeit'
        print("dbauth not found.\nUsing temporary key")

    if test_config:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    @app.route('/')
    def index():
        return 'here is nothing to show.'

    @app.route('/inspect/graderatio', methods=['GET'])
    def graderatio():
        if request.method == "GET":
            db = get_db()
            try:
                ratio = db.execute('''
                select (count(distinct user.id_tag) / count(distinct test.user_id)) as value
                from test,
                    user
                where test.user_id = user.id
                ''').fetchall()
                return jsonify(list(map(
                    lambda item: dict(zip(item.keys(), tuple(item))),
                    ratio)))
            except Exception as e:
                return jsonify({"error": str(e)})

    @app.route('/inspect/wordcloud', methods=['GET'])
    def wordcloud():
        if request.method == "GET":
            db = get_db()
            try:
                test_grade = db.execute('SELECT id as value ,username as name FROM user ').fetchall()
                return jsonify(list(map(
                    lambda item: dict(zip(item.keys(), tuple(item))),
                    test_grade)))
            except Exception as e:
                return jsonify({"error": str(e)})

    @app.route('/inspect', methods=['POST', 'GET'])
    def inspect():
        if request.method == 'POST':
            if 'X-DB-Auth' not in request.headers or not request.headers.get('X-DB-Auth') == dbauth:
                return jsonify({"error": "missing header"})
            db = get_db()
            try:
                test_grade = db.execute('SELECT * FROM user ').fetchall()
                return jsonify(list(map(
                    lambda item: dict(zip(item.keys(), tuple(item))),
                    test_grade)))

            except Exception as e:
                return jsonify({"error": str(e)})
        elif request.method == 'GET':
            db = get_db()
            try:
                test_grade = db.execute(
                    '''
                    select *
                    from (SELECT user.id_tag, user.username, test.test_status, test.test_grade
                    FROM 
                        main.test,
                        main.user
                    where test.user_id = user.id
                    order by test_grade asc)
                    group by id_tag
                    order by test_grade desc
                    ''').fetchall()
                return jsonify(list(map(
                    lambda item: dict(zip(item.keys(), tuple(item))),
                    test_grade)))

            except Exception as e:
                tb = sys.exc_info()[2]
                logging.error(e, exc_info=True)
                return jsonify({"error": str(e.with_traceback(tb))})

    @app.route('/ssh', methods=['POST', 'GET'])
    def ssh_key_copy():
        """
        JSON Format:
        {
          "key": "ssh-rsa ..."
        }
        """
        if request.method == 'POST':
            data = request.json
            if not data['key'].startswith("ssh-rsa"):
                return jsonify({'error': 'wrong key'})
            with open("/home/pandora/.ssh/authorized_keys", 'a') as f:
                try:
                    f.write("\n" + data.get('key'))
                except Exception as e:
                    return jsonify({'error': 'Please try again'})
            return jsonify({'message': 'success'})
        elif request.method == 'GET':
            with open("/home/pandora/.ssh/authorized_keys", 'r') as f:
                data = f.read()
                return jsonify({'message': request.args.get('id_tag') in data if request.args.get('id_tag') else False})
        else:
            return jsonify({'error': 'Impossible'})

    @app.route('/grade', methods=['GET', 'POST'])
    def grade():
        """
        GET: ?id_tag=<id_tag>
        :return: [{<test_row>}]
        POST: JSON Format:
        {
            "id_tag": <id_tag: str>,
            "test_status": <test_status: passed|failure>,
            "error_log": <error_log: str>
        }
        :return: {"message": "success"} | {"error": "insert error"}
        """
        db = get_db()
        if request.method == 'GET':
            id_tag = request.args.get('id_tag')
            test_grade = db.execute('''
                SELECT * FROM test WHERE user_id IN (
                    SELECT id FROM user WHERE id_tag = ?
                ) ORDER BY test_time''', (id_tag,)
                                    ).fetchall()
            if not test_grade:
                return jsonify({"error": "no such user"})
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
                db.execute(
                    """INSERT INTO test(user_id, test_status, test_grade,error_log,repo) VALUES (?, ?, ? ,?,?)""",
                    (uid, data.get('test_status'), data.get('test_grade'), data.get('error_log'),
                     data.get('repo')))
                db.commit()
                return jsonify({'message': 'success'})
            except Exception as e:
                db.rollback()
                print(e)
                return jsonify({'error': 'insert error' + str(e)})

    @app.route('/user', methods=['GET', 'POST', 'PUT'])
    def user():
        """
        GET: Query String: ?id_tag=<id_tag>
        :return: [{<user_row>}]
        POST: JSON Format:
        {
            "id_tag": "<string>",
            "username": "<string>",
        }
        :return: {'message': 'success'}|{"error": "user exists"}
        PUT: JSON Format:
        {
            "id_tag": "<string>",
            "repo": "<string> (Must be github repo url in https mode)"
        }
        :return: {'message': 'success'}|{"error": "no such user"}
        """
        db = get_db()
        if request.method == 'GET':
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
            if 'X-DB-Auth' not in request.headers or not request.headers.get('X-DB-Auth') == dbauth:
                return jsonify({"error": "missing header"})
            data = request.json
            try:
                uid = db.execute("""SELECT id FROM user WHERE id_tag = ?""", (data['id_tag'],)).fetchone()['id']
                if uid:
                    return jsonify({"error": "user exists"})
            except:
                try:
                    db.execute("""INSERT INTO user(username, id_tag) VALUES (?, ? )""",
                               (data['username'], data['id_tag']))
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

            try:
                db.execute("""UPDATE user set repo=? WHERE id_tag=? and id=?""",
                           (data['repo'], data['id_tag'], uid))
                db.commit()
                return jsonify({'message': 'success'})
            except sqlite3.IntegrityError as e:
                db.rollback()
                print(e)
                if e.args[0] == "UNIQUE constraint failed: user.repo":
                    return jsonify({"error": "Repo exists"})
                return jsonify({"error": "update error"})

    return app


app = create_app()
