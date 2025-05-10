from flask_sqlalchemy import SQLAlchemy

#initialise database
db = SQLAlchemy()

#define product table
class dbProduct(db.Model):
    #id, name, description, image, colour, price stock
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, nullable=False)
    colour = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer)

#define customer table
class dbCustomer(db.Model):
    #id, forename, surname, email, street, city, postcode
    id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postcode = db.Column(db.String(10), nullable=False)

#define order table
class dbOrder(db.Model):
    #id, ref_number, total_price, order_date, shipping_date, status, customer_id
    id = db.Column(db.Integer, primary_key=True)
    ref_number = db.Column(db.String(255), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, nullable=False)
    shipping_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey(dbCustomer.id))
    customer_rel = db.relationship('dbCustomer', backref='customer')

#define order_item table
class dbOrder_Item(db.Model):
    #id, order_id, product_id, quantity, price
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(dbOrder.id))
    order_rel = db.relationship('dbOrder', backref='orderitems')
    product_id = db.Column(db.Integer, db.ForeignKey(dbProduct.id))
    product_rel = db.relationship('dbProduct', backref='productitems')
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

#define admin table
class dbAdmin(db.Model):
    #id, forename, email, password
    id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

#define login_event table
class dbLogin_Event(db.Model):
    #id, timestamp, attempts, ip_address, action_details, severity, admin_id
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(255), nullable=False)
    action_details = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(255), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey(dbAdmin.id))
    admin_rel = db.relationship('dbAdmin', backref='logins')