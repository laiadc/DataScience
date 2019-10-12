from flask import Flask, make_response
from flask import abort, jsonify, redirect, render_template
from flask import request, url_for
from forms import ProductForm
from flask import Flask
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bson
from flask_login import LoginManager, current_user
from flask_login import login_user, logout_user
from flask_login import login_required
from forms import LoginForm
from models import User

import json


app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'foodb'

with open("credentials", 'r') as f:
  [name, password, url] = f.read().splitlines()
app.config['MONGO_URI'] = "mongodb+srv://{}:{}@{}".format(name, password, url)
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/foodb'


app.config['SECRET_KEY'] = 'Ihatethis' # Create your own.
app.config['SESSION_PROTECTION'] = 'strong'


mongo = PyMongo(app)
#Create test user
mongo.db.users.insert( {"username":"test", "password":"1234"} )


@app.route('/')
def index():
  return redirect(url_for('products_list'))

@login_required
@app.route(
  '/product/<product_id>/edit/', #Methods: the actions you allow to do in this URL
  methods=['GET', 'POST']) #POST: Replace data in the Database GET: Obtain information of database
def product_edit(product_id):
  form = ProductForm(request.form)
  return render_template('product/edit.html', form=form)

@login_required
@app.route('/product/create/', methods=['GET', 'POST'])
def product_create():
  """Provide HTML form to create a new product."""
  form = ProductForm(request.form)
  if request.method == 'POST' and form.validate():
    mongo.db.products.insert_one(form.data)
    # Success. Send user back to full product list.
    return redirect(url_for('products_list'))
  # Either first load or validation error at this point.
  return render_template('product/edit.html', form=form)



@app.route('/product/<product_id>/')
def product_detail(product_id):
  """Provide HTML page with a given product."""
  # Query: get Product object by ID.
  product = mongo.db.products.find_one({ "_id": ObjectId(product_id) })
  print(product)
  if product is None:
    # Abort with Not Found.
    abort(404)
  return render_template('product/detail.html',
    product=product)

@app.route('/product/')
def products_list():
  """Provide HTML listing of all Products."""
  # Query: Get all Products objects, sorted by date.
  products = mongo.db.products.find()[:]
  return render_template('product/index.html',
    products=products)

@login_required
@app.route('/product/<product_id>/delete/', methods=['DELETE'])
def product_delete(product_id):
  """Delete record using HTTP DELETE, respond with JSON."""
  result = mongo.db.products.delete_one({ "_id": ObjectId(product_id) })
  if result.deleted_count == 0:
    # Abort with Not Found, but with simple JSON response.
    response = jsonify({'status': 'Not Found'})
    response.status = 404
    return response
  return jsonify({'status': 'OK'})



@app.errorhandler(404)
def error_not_found(error):
  return render_template('error/not_found.html'), 404

@app.errorhandler(bson.errors.InvalidId)
def error_not_found(error):
  return render_template('error/database.html'), 404


# Use Flask-Login to track current user in Flask's session.
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'



@login_manager.user_loader
def load_user(user_id):
  """Flask-Login hook to load a User instance from ID."""
  u = mongo.db.users.find_one({"username": user_id})
  if not u:
        return None
  return User(u['username'])

@app.route('/login/', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('products_list'))
  form = LoginForm(request.form)
  error = None
  if request.method == 'POST' and form.validate():
    username = form.username.data.lower().strip()
    password = form.password.data.lower().strip()
    user = mongo.db.users.find_one({"username": form.username.data})
    print(mongo.db.users.find_one({"username": "test"}))
    if user and User.validate_login(user['password'], form.password.data):
      user_obj = User(user['username'])
      login_user(user_obj)
      return redirect(url_for('products_list'))
    else:
      error = 'Incorrect username or password.'
  return render_template('user/login.html',
      form=form, error=error)

@app.route('/logout/')
def logout():
  logout_user()
  return redirect(url_for('products_list'))






if __name__ == '__main__':
    app.run()

