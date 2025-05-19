import pytest
from flask import Flask
from datetime import datetime, timedelta
import os
import bcrypt
from main import app, db 
from models import *
from library import * 

# Configuration for testing
TEST_DB_URI = "sqlite:///:memory:" 
UPLOAD_FOLDER = "test_uploads"

# Create the test upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ------------------- TEST FIXTURES -------------------

# configures test app and database
@pytest.fixture()
def test_app():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DB_URI
    app.config["SECRET_KEY"] = "test_secret_key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture()
def test_client(test_app):
    return test_app.test_client()


# ------------------- HELPER FUNCTIONS -------------------

# creates temp admin user for testing
def create_admin(email, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    admin = dbAdmin(forename="test", email=email, password=hashed)
    db.session.add(admin)
    db.session.commit()
    return admin

# creates temp product for testing
def create_product(name, price, stock, image = "test_uploads/amber.webp"):
    product = dbProduct(name=name, description="this is a test", price=price, stock=stock, image=image, colour="Red")
    db.session.add(product)
    db.session.commit()
    return product

# creates temp customer for testing
def create_customer(email):
    customer = dbCustomer(forename="test", surname="test", email=email, street="25 test road", city="test town", postcode="cv4 7al")
    db.session.add(customer)
    db.session.commit()
    return customer

# creates temp order for testing
def create_order(customer_id):
    order_date = datetime.now()
    shipping_date = order_date + timedelta(days=7)
    order = dbOrder(ref_number="SC-1234567890123456", order_date=order_date, shipping_date=shipping_date, status="paid", customer_id=customer_id, total_price=10.0)
    db.session.add(order)
    db.session.commit()
    return order

# admin login helper function
def admin_login(client, email, password):
    client.post("/admin/login", data={"email": email, "S3curePword!": password}, follow_redirects=True)


# ------------------- ADMIN USER TESTS -------------------

# tests if admin can login
def test_admin_home(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    response = test_client.get("/admin")
    assert response.status_code == 302

# tests if admin can create admins
def test_admin_create_admin(test_client):
    create_admin(email="admin2@gmail.com", password="AnotherPword!")
    admin_login(test_client, "admin2@gmail.com", "AnotherPword!")
    response = test_client.get("/admin")
    assert response.status_code == 302

# tests if admin can view products
def test_admin_products(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    response = test_client.get("/admin/products")
    assert response.status_code == 302

# tests if admin can create products
def test_admin_create_product(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    response = test_client.post("/admin/products/update", data={
        "name": "Amber Slime",
        "description": "amber test slime",
        "price": 15.99,
        "stock": 5,
        "colour": "Amber",
        "image": os.path.join(app.config["UPLOAD_FOLDER"], "/test_uploads/amber.webp")
    }, follow_redirects=True)
    assert response.status_code == 200

# tests if admin can update products
def test_admin_update_product(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    product = create_product(name="Old Slime", price=10.0, stock=3)
    response = test_client.post(f"/admin/products/update", data={
        "product_id": product.id,
        "name": "Rose Slime",
        "description": "rose test slime",
        "price": 12.99,
        "stock": 10,
        "colour": "Rose",
        "image": os.path.join(app.config["UPLOAD_FOLDER"], "/test_uploads/rose.webp")
    }, follow_redirects=True)
    assert response.status_code == 200

# tests if admin can delete products
def test_admin_delete_product(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    product = create_product(name="Delete Me", price=5.0, stock=1)
    response = test_client.post("/admin/products/delete", data={
        "product_id": product.id
    }, follow_redirects=True)
    assert response.status_code == 200

# tests if admin can view orders
def test_admin_orders(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    response = test_client.get("/admin/orders")
    assert response.status_code == 302

# tests if admin can view order details
def test_admin_order_details(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    customer = create_customer(email="orderdetail@gmail.com")
    order = create_order(customer_id=customer.id)
    response = test_client.get(f"/admin/orders/{order.id}")
    assert response.status_code == 302

# tests if admin can update orders
def test_admin_update_order(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    customer = create_customer(email="customer@gmail.com")
    order = create_order(customer_id=customer.id)
    response = test_client.post(f"/admin/orders/{order.id}/update", data={
        "status": "shipped",
        "customer_id": customer.id,
        "forename": "test forename",
        "surname": "test surname",
        "email": "test@gmail.com",
        "street": "25 test road",
        "city": "test town",
        "postcode": "cv4 7al",
    }, follow_redirects=True)
    assert response.status_code == 200

# tests if admin can update order status
def test_admin_update_order_status(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    customer = create_customer(email="customer@gmail.com")
    order = create_order(customer_id=customer.id)
    response = test_client.post(f"/admin/orders/updatestatus/{order.id}", data={
        "status": "delivered"
    }, follow_redirects=True)
    assert response.status_code == 200

# tests if admin can log out 
def test_admin_logout(test_client):
    create_admin(email="admin@gmail.com", password="S3curePword!")
    admin_login(test_client, "admin@gmail.com", "S3curePword!")
    response = test_client.get("/admin/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

    
# ------------------- CLIENT USER TESTS -------------------

# tests if customer can view home page
def test_home(test_client):
    response = test_client.get("/")
    assert response.status_code == 302
    response = test_client.get("/home")
    assert response.status_code == 200
    assert b"Products" in response.data

# tests if customer can view product page
def test_product_detail(test_client):
    product = create_product(name="Test Slime", price=12.99, stock=8)
    response = test_client.get(f"/home/product/{product.id}")
    assert response.status_code == 200
    assert b"Test Slime" in response.data

# tests if customer can view faq page
def test_faq(test_client):
    response = test_client.get("/faq")
    assert response.status_code == 200
    assert b"FAQs" in response.data


# tests if customer can add product to cart
def test_add_to_cart(test_client):
    product = create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": []}
    response = test_client.post(f"/home/product/{product.id}/addedtocart", data={"quantity": 2}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Slime" in response.data
    assert b"2" in response.data

# tests if customer can view cart
def test_cart(test_client):
    product = create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": []}
    test_client.post(f"/home/product/{product.id}/addedtocart", data={"quantity": 2}, follow_redirects=True)
    response = test_client.get("/cart")
    assert response.status_code == 200
    assert b"Your Cart" in response.data
    assert b"Test Slime" in response.data

# tests if customer can remove product from cart
def test_remove_from_cart(test_client):
    create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": [{"name": "Test Slime", "quantity": 2, "price": 12.99, "total": 25.98}]}
    response = test_client.post("/cart/remove", data={"product_name": "Test Slime"}, follow_redirects=True)
    assert response.status_code == 200

# tests if customer can update product quantity in cart
def test_update_cart(test_client):
    create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": [{"name": "Test Slime", "quantity": 2, "price": 12.99, "total": 25.98}]}
    response = test_client.post("/cart/update", data={"product_name": "Test Slime", "quantity": 3}, follow_redirects=True)
    assert response.status_code == 200
    assert b"3" in response.data

# tests if customer can empty cart
def test_empty_cart(test_client):
    create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": [{"name": "Test Slime", "quantity": 2, "price": 12.99, "total": 25.98}]}
    response = test_client.post("/cart/empty", follow_redirects=True)
    assert response.status_code == 200

# tests if customer can checkout
def test_checkout(test_client):
    create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": [{"name": "Test Slime", "quantity": 2, "price": 12.99, "total": 25.98}]}
    response = test_client.get("/cart/checkout")
    assert response.status_code == 200
    assert b"Checkout" in response.data

# tests that order can be completed
def test_order_complete(test_client):
    #tests with valid data
    create_product(name="Test Slime", price=12.99, stock=8)
    with test_client.session_transaction() as client_session:
        client_session["cart"] = {"products": [{"name": "Test Slime", "quantity": 2, "price": 12.99, "total": 25.98}]}
    response = test_client.post("/cart/checkout/complete", data={
        "forename": "test",
        "surname": "test",
        "email": "test@gmail.com",
        "street": "25 test road",
        "city": "test town",
        "postcode": "cv4 7al",
        "cardnumber": "1234567890",
        "expirydate": "2025-04",
        "cvv": "123"
    }, follow_redirects=True)

    assert response.status_code == 200
    #tests with invalid data - no forename
    response = test_client.post("/cart/checkout/complete", data={
        "forename": "",
        "surname": "test",
        "email": "no",
        "street": "25 test road",
        "city": "test town",
        "postcode": "cv4 7al",
        "cardnumber": "1234567890",
        "expirydate": "2025-04",
        "cvv": "123"
    }, follow_redirects=True)
    assert response.status_code == 200

# tests if customer can view track order page
def test_track_order(test_client):
    response = test_client.get("/trackorder")
    assert response.status_code == 200
    assert b"Track Orders" in response.data

# tests if customer can view order details
def test_view_order(test_client):
    customer = create_customer(email="test@gmail.com")
    order = create_order(customer_id=customer.id)
    # tests with valid data
    response = test_client.post("/trackorder/view", data={"refnum": order.ref_number, "email": "test@gmail.com"})
    assert response.status_code == 200
    assert b"Order Details" in response.data
    # tests with invalid data - invalid email
    response = test_client.post("/trackorder/view", data={"refnum": order.ref_number, "email": "invalid@gmail.com"})
    assert response.status_code == 200
    assert b"No results found" in response.data
