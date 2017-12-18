
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import firebase_admin
from firebase_admin import db

import flask


app = flask.Flask(__name__)

firebase_admin.initialize_app(options={
    'databaseURL': 'https://hjk-test-storage.firebaseio.com'
})
SUPERHEROES = db.reference('superheroes')

@app.route('/heroes', methods=['POST'])
def create_hero():
    req = flask.request.json
    hero = SUPERHEROES.push(req)
    return flask.jsonify({'id': hero.key}), 201

@app.route('/heroes/<id>')
def read_hero(id):
    return flask.jsonify(_ensure_hero(id))

@app.route('/heroes/<id>', methods=['PUT'])
def update_hero(id):
    _ensure_hero(id)
    req = flask.request.json
    SUPERHEROES.child(id).update(req)
    return flask.jsonify({'success': True})

@app.route('/heroes/<id>', methods=['DELETE'])
def delete_hero(id):
    _ensure_hero(id)
    SUPERHEROES.child(id).delete()
    return flask.jsonify({'success': True})

def _ensure_hero(id):
    hero = SUPERHEROES.child(id).get()
    if not hero:
        flask.abort(404)
    return hero
