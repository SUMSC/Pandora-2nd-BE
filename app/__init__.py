import os
import sqlite3
from flask import Flask, request, jsonify

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'grade.sqlite'),
    )

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
        f.write("\n"+data['key'])
      return jsonify({'message': 'success'})

    @app.route('/init_db', methods=['GET', 'POST'])


    @app.route('/grade', methods=['GET', 'POST'])
    def grade():
      pass
    
    from . import db
    db.init_app(app)
    
    return app