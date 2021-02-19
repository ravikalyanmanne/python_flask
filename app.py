from flask import Flask, jsonify, request, make_response, render_template, session, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
import json
from functools import wraps
import jwt
import datetime

# creating a Flask app 
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') 

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated

@app.route('/unprotected')
def unprotected():
    return jsonify({'message' : 'Anyone can view this!'})

@app.route('/protected')
@token_required
def protected():
    return jsonify({'message' : 'This is only available for people with valid tokens.'})

@app.route('/login')
def login():
    auth = request.authorization

    if auth and auth.password == 'password':
        token = jwt.encode({'user' : auth.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=2)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})


#authentication 
# api = Api(app, prefix="/api/v1")
# auth = HTTPBasicAuth()

# USER_DATA = {
#     "admin": "supersecret"
# }

# @auth.verify_password
# def verify(username, password):
#     if not (username and password):
#         return False
#     return USER_DATA.get(username) == password


cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

db=firestore.client()

docs = db.collection('books_list').get()

x=[]

for doc in docs:
    x.append(doc.to_dict())

#list and create
@app.route('/books',methods=['GET','POST']) 
#@auth.login_required
@token_required
def books():
    if(request.method == 'GET'):
        if len(x)>0:
            return jsonify(x)
        else:
            'Nothing found',404
    if request.method == 'POST':
        iD = request.args.get('id')
        doc_ref=db.collection('books_list').document(iD)
        new_author = request.args.get('author')
        new_lang = request.args.get('language')
        new_title = request.args.get('title')
        doc_ref.set(
            {
            "id" : iD,
            "author" : new_author,
            "language" : new_lang,
            "title" : new_title
            })
        return "created"
        
#read,update and delete
@app.route('/books/<int:id>',methods=['GET','PUT','DELETE'])
#@auth.login_required
@token_required
def single_book(id):
    if request.method == 'GET':
        for book in x:
            if book["id"] == id:
                return jsonify(book)
            pass
    if request.method == 'PUT':
        iD = request.args.get('id')
        new_author = request.args.get('author')
        new_lang = request.args.get('language')
        new_title = request.args.get('title')
        updated_book={
            "id" : iD,
            "author" : new_author,
            "language" : new_lang,
            "title" : new_title
            }
        db.collection('books_list').document(iD).update(updated_book)
        return "updated"
    if request.method == 'DELETE':
        todo_id = request.args.get('docname')
        doc_ref=db.collection('books_list').document(todo_id)
        doc_ref.delete()
        return "deleted"

#filter
@app.route('/filter/',methods=['GET','PUT'])
#@auth.login_required
@token_required
def filter():
    new_lang = request.args.get('language')
    docs=db.collection('books_list').where('language','==',new_lang).get()
    a=[]
    for doc in docs:
        a.append(doc.to_dict())
    return jsonify(a),200

#driver function 
if __name__ == '__main__': 
  
    app.run(debug = True) 