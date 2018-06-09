from flask import Flask, render_template, request , session
import datetime
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, logout_user, roles_accepted

app = Flask(__name__)
app.config['DEBUG'] = True
# Configure Flask-SQLAlchemy - sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///item.db'
# Secret key used for the session key
app.config['SECRET_KEY'] = 'super-secret'

app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = 'super-secret'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_POST_REGISTER_VIEW'] = '/'
app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/error'
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    position = db.Column(db.String(250), nullable=True)
    qty = db.Column(db.Integer, nullable=False)

    def __init__(self, name, position, qty):
        self.name = name
        self.position = position
        self.qty = qty


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,backref=db.backref('users', lazy='dynamic'))

class Items_required_p(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    p_id = db.Column(db.Integer)
    name = db.Column(db.String(255),unique = True)
    quantity = db.Column(db.Integer)
    required = db.Column(db.Integer)

    def __init__(self,p_id,name,quantity,required):
        self.p_id = p_id
        self.name = name
        self.quantity = quantity
        self.required = required


class Suppliers(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255), unique=True)

class Supplier_items(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    s_id = db.Column(db.Integer,db.ForeignKey('suppliers.id'))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    date = db.Column(db.String)
    sup = db.relationship('Suppliers',backref=db.backref("Suppliers",uselist = False))

    def __init__(self,s_id,price,quantity,date):
        self.s_id = s_id
        self.price = price
        self.quantity = quantity
        self.date  = date




# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
'''
# Create a user to test with
@app.before_first_request
def create_user():
    db.create_all()
    user_datastore.create_user(email='ashwath', password='password')
    user_datastore.create_role(name='admin', description='admin')
    db.session.commit()
'''

@app.route('/')
@app.route('/<name>')
def welcome_page(name=" Warehouse"):
    return render_template('index.html', name=name)


@app.route('/product/all')
@roles_accepted('admin')
def view_list_products():
    items = Items_required_p.query.all()
    return render_template('list_products.html', product=items)


@app.route('/product/<pid>')
def view_product_by_id(pid):
    admin = Items_required_p.query.filter_by(p_id=pid).first()
    ori_item = Item.query.filter_by(id=pid).first()
    session['product_id'] = pid
    return render_template('show_product.html', product=admin , item = ori_item)


@app.route('/accept_proposal' , methods=['POST'])
@roles_accepted('admin')
def update_required_form():
    required = request.form['required']
    pid = session.get('product_id', None)
    update_this = Items_required_p.query.filter_by(p_id=pid).first()
    update_this.required = '1'
    db.session.commit()
    admin = Items_required_p.query.filter_by(p_id=pid).first()
    ori_item = Item.query.filter_by(id=pid).first()
    session['product_id'] = pid
    return render_template('show_product.html', product=admin , item = ori_item)




@app.route('/product/add')
@roles_accepted('purchase')
def add_product():
    user_datastore.add_role_to_user(user='bal@gmail.com', role='purchase')
    db.session.commit()
    return render_template('add_product.html')


@app.route('/add/product', methods=['POST'])
@roles_accepted('purchase')
def add_product_form():
    p_id = request.form['id']
    name = request.form['name']
    qty = request.form['qty']

    admin = Items_required_p( p_id, name, qty,'0')
    db.session.add(admin)
    db.session.commit()
    return render_template('add_product.html')


@app.route('/supplier/product/<pid>')
def view_product_supplier(pid):
    admin = Items_required_p.query.filter_by(p_id=pid).first()
    return render_template('supplier_product.html', product=admin)


@app.route('/supplier')
@roles_accepted('supplier')
def show_supplier_products():
    items = Items_required_p.query.filter_by(required='1')
    return render_template('supplier.html' , product = items)


@app.route('/supplier_accept' , methods=['POST'])
def supplier_accept():
    date_time = datetime.datetime.now().strftime("%Y-%m-%d")
    s_id = request.form['s_id']
    price = request.form['price']
    quantity = request.form['quantity']
    add_item = Supplier_items(s_id,price,quantity,date_time)
    db.session.add(add_item)
    db.session.commit()
    items = Items_required_p.query.filter_by(required='1')
    return render_template('supplier.html', product=items)


@app.route('/purchase_review')
@roles_accepted('admin')
def purchase_review():
    show_supp = Supplier_items.query.all()
    return render_template('purchase_review.html' , product = show_supp)


@app.route('/error')
def show_error_page():
    return render_template('error.html')


@app.route('/logout')
def user_logout():
    logout_user()
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
