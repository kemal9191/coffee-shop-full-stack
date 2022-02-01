from curses import raw
import os
from urllib.request import Request
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
#DONEEEE

db_drop_and_create_all()

    # ROUTES
'''
Fetches all available drinks
'''
@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    if len(drinks)==0:
        abort(404)
    
    short_drinks = [drink.short() for drink in drinks]

    return jsonify({
        "success":True,
        "drinks": short_drinks
    }), 200


'''
Fetches all available drinks in detail
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drinks_detail(payload):
    drinks_data = Drink.query.all()

    if len(drinks_data)==0:
        abort(404)

    drinks = [drink.long() for drink in drinks_data]

    return jsonify({
        "success": True,
        "drinks": drinks
    }), 200

'''
Creates a new drink and pushes it into db
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    raw_data = request.get_json()
    title = raw_data['title']
    recipe = raw_data['recipe']
    
    drink = Drink(title=title, recipe=json.dumps(recipe))

    try:
        drink.insert()
    except Exception:
        print(str(Exception))
        abort(422)

    return jsonify({
        "success": True,
        "drink": drink.long()
    }), 200


'''
Fetches a drink, and pushes it into db after updating requested parts
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    raw_data = request.get_json()
    drink_to_update = Drink.query.filter(Drink.id==id).one_or_none()

    if not drink_to_update :
        abort(404)

    try:
        title = raw_data.get('title', None)
        recipe = raw_data.get('recipe', None)

        if title:
            drink_to_update.title = title
        if recipe:
            drink_to_update.recipe = json.dumps(raw_data['recipe'])

        drink_to_update.update()

        drinks = [drink_to_update.long()]
        return jsonify({
        "success": True,
        "drinks": drinks
    }), 200
    
    except Exception:
        print(str(Exception))
        abort(422)
    

'''
Deletes the drink
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink_to_delete = Drink.query.get(id)

    if drink_to_delete is None:
        abort(404)
    
    try:
        drink_to_delete.delete()
    except Exception:
        print(str(Exception))
        abort(422)

    return jsonify({
        "success": True,
        "delete": id
    }), 200

    # Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad Request"
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 401


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Not Found"
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable Entity"
    }), 422


@app.errorhandler(405)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "Method Not Allowed"
    }), 405


@app.errorhandler(500)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal Server Error"
    }), 500


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    })

if __name__ == "__main__":
    app.debug = True
    app.run(ssl_context='adhoc')
