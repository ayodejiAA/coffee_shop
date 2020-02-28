import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

session = db.session
'''
@TODO uncomment the following line to initialize the dataabase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

## ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def retrieve_drinks():
    result = Drink.query.order_by(Drink.id).all()
    drinks = [drink.short() for drink in result]
    return jsonify({"success": True, "drinks": drinks}), 200


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def retrieve_drinks_detail():
    try:
        result = Drink.query.order_by(Drink.id).all()
        drinks = [drink.long() for drink in result]
        return jsonify( {"success": True, "drinks": drinks}), 200
    except AuthError:
        abort()


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drinks():
    try:
        body = request.get_json()
        title =  body['title'] or None
        recipe = body['recipe'] or None
 
        if not(title and recipe): return jsonify({"status": False, "message":"drink title and recipe must be provided"}), 400
        
        drink = Drink(title=title, recipe=json.dumps(recipe))
        result = drink.insert()
        return jsonify({"success": True, "drinks": drink.long()})
    except AuthError:
        abort()
    except exc.IntegrityError as e:
        session.rollback()
        return jsonify({"status": False, "message" : "drink with this title already exists"}), 409
    except:
        return abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none() 
        if not drink : raise
        body = request.get_json()
        drink.title = body['title'] or drink.title
        drink.recipe = json.dumps(body['recipe']) or drink.recipe
        drink.update()
        return  jsonify({"success": True, "drinks": drink.long()}), 200
    except AuthError:
        abort()
    except:
        if not drink: abort(404)
        abort(422)



'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none() 
        if not drink : raise
        drink.delete()
        return  jsonify({"success": True, "delete": id}), 200
    except AuthError:
        abort()
    except:
        if not drink: abort(404)
        abort(422)

## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": "resource not found"
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False, 
        "error": error.error['code'],
        "message": error.error['description']
    }), error.status_code
