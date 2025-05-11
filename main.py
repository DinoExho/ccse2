from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
import secrets 
import bcrypt
from models import *
from library import *
from datetime import *
from random import *
from os import *

#configures the app including secret key, database and upload folder path
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + path.join(app.instance_path, 'slimeapp.db')
app.config["UPLOAD_FOLDER"] = path.join("static", "uploads")

if not path.exists(app.config["UPLOAD_FOLDER"]):
    makedirs(app.config["UPLOAD_FOLDER"])

try:
    makedirs(app.instance_path)
except OSError:
    pass

db.init_app(app)

#handles admin user authentication
class Auth():
    def __init__(self):
        pass   
    
    #checks that there hasn't been more than 5 logins within the last 10 minutes
    def exceeded_attempts(self, email):
        #retreives admin info
        Admin = dbAdmin.query.filter_by(email=email).first()
        if Admin:
            event = self.find_login_event(Admin.id)
            if event:
                if event.attempts >= 5:
                    #if reached, then lock account until 10 mins since the first attempt has passed
                    return True
        return False

    #checks the admin credentials are correct
    def check_credentials(self, email, password):

        #gets admin info if the email exists
        Admin = dbAdmin.query.filter_by(email=email).first()
        if not Admin:
            return "Incorrect Credentials"
        
        #if email exists, check password matches
        if not bcrypt.checkpw(password.encode('utf-8'), Admin.password):
            #log attempt
            self.record_attempt(Admin.id, "Unsuccesful Login Attempt", "High")
            return "Incorrect Credentials"
        
        #create a session so only logged in users can access the pages
        session["email"] = email
        #log attempt
        self.record_attempt(Admin.id, "Succesful Login Attempt", "Critical")
        return "correct"

    #checks how many login events for that account and ip in the last 10 minutes
    def find_login_event(self, adminid):
        #retrieves all events for that admin
        adminloginevents = dbLogin_Event.query.filter_by(admin_id=adminid).all()
        ip_address=request.remote_addr
        timestamp=datetime.now()

        if adminloginevents !=[]: #if there are login events for that admin id
            for event in adminloginevents: #for each event in the list
                if event.ip_address == ip_address: #if the stored ip matchies the current one
                    original_time = event.timestamp #start time
                    new_time = original_time + timedelta(minutes=10) #end time
                    if (timestamp <= new_time) and (timestamp >= original_time): #if time is in the range
                        return event


    def record_attempt(self, adminid, message, severity):
        event = self.find_login_event(adminid) #find corresponding event
        if event and message == "Unsuccesful Login Attempt": #if unsuccessful
            event.attempts += 1 #increment attempts
            db.session.commit()
        elif event and message == "Succesful Login Attempt": #if successful
            event.attempts = 0 #reset attempts
            db.session.commit()
        else:
            #record new login attempt
            loginevent = dbLogin_Event(timestamp=datetime.now(), attempts=1, ip_address=request.remote_addr, action_details=message, severity=severity,  admin_id=adminid)
            db.session.add(loginevent)
            db.session.commit()

#initalise the objects
UserCart = Cart()
UserValidation = Validation()
UserCurrency = CurrencyConverter()
UserAuth = Auth()



# <-------------------- Customer Routes -------------------->

@app.route("/")
def index():
    return redirect("/home")

@app.route("/home")
def home():
    # Displays all the products in the current currency
    products = dbProduct.query.all() 
    rate = UserCurrency.currentrate()
    symbol = UserCurrency.currentsymbol()
    currency = UserCurrency.currency()
    # Render the home page with the products and currency information
    return render_template("/customer/home.html", products=products, rate=rate, symbol=symbol, currency=currency)

# Route for changing the currency
@app.route("/home/currency", methods=["POST"])
def changecurrency():
    # If the user wants to change the currency, this function gets triggered
    newcurrency = request.form["currency"]
    redirectpage = request.form["redirectpage"]
    # Set the new currency
    UserCurrency.setnew(newcurrency)
    # Redirect the user back to the page they were on
    return redirect(redirectpage)


@app.route("/home/product/<int:product_id>")
def product_detail(product_id, added=False):
    try:
        # Check if the 'added' parameter is in the request arguments
        added = request.args['added']
    except KeyError:
        pass
    # Query the database for the product with the given product_id
    product = dbProduct.query.get(product_id)
    rate = UserCurrency.currentrate()
    symbol = UserCurrency.currentsymbol()
    currency = UserCurrency.currency()
    # Render the product detail page with the product and currency information
    return render_template("/customer/product.html", product=product, rate=rate, symbol=symbol, currency=currency, added=added)

@app.route("/faq")
def faq():
    # Get the user's currency
    currency = UserCurrency.currency()
    # Render the FAQ page with the user's currency
    return render_template("/customer/faq.html", currency=currency)

# Route for the order tracking page
@app.route("/trackorder")
def track_order():
    # Render the order tracking page
    return render_template("/customer/trackorder.html", order=None, currency = UserCurrency.currency())

@app.route("/trackorder/view", methods=["POST"])
def view_order():
    if request.method == "POST":
        # Get the reference number and email from the form
        refnum = request.form["refnum"]
        email = request.form["email"]
        # retrieve the order from the database
        order = dbOrder.query.filter_by(ref_number=refnum).first()
        order_id = order.id

        #retrieve the customer and order items
        customer = dbCustomer.query.filter_by(id=order.customer_id).first()
        orderitems = dbOrder_Item.query.filter_by(order_id=order_id).all()
        products = []
        for item in orderitems:
            products = dbProduct.query.filter_by(id=item.product_id).all()

        #check if the email matches the email of the customer
        if customer.email != email:
            return render_template("/customer/trackorder.html", error="No results found", refnum=refnum, email=email, currency = UserCurrency.currency())
        else:
            return render_template("/customer/trackorder.html", order=order, orderitems=orderitems, customer=customer, products=products, currency = UserCurrency.currency())


@app.route("/home/product/<int:product_id>/addedtocart", methods=["GET","POST"])
def addedtocart(product_id):
    if request.method == "POST":
        # Get the product id and quantity from the form
        product = dbProduct.query.get(product_id)
        amount = int(request.form["quantity"])
        exists = False

        # Check if the product is already in the cart
        for item in UserCart.getproducts():
            if product.name == item.name:
                item.increasequantity(amount)
                exists = True
        if not exists:
            UserCart.addproduct(CartProduct(product.name, amount, product.price))
        # if the user accessed from home page, direct to cart
        try:
            test = request.form["identifier"]
            return redirect(url_for('product_detail', product_id=product_id, added=True))
        except KeyError:
            return redirect("/cart")


@app.route("/cart")
def cart():
    # Get the number of products, the total price, the products, and the stock of each product
    numberproducts = UserCart.gettotalproducts()
    totalprice = UserCart.gettotalprice()
    products = UserCart.getproducts()
    productstock = []
    #if the cart is empty, the user cannot checkout
    if numberproducts == 0:
        allowcheckout = False
    else:
        #if the cart is not empty, the user can checkout
        #get the stock of each product in the cart
        for product in products:
            productstock.append(dbProduct.query.filter_by(name = product.name).first())
        allowcheckout = True 

    rate = UserCurrency.currentrate()
    symbol = UserCurrency.currentsymbol()
    currency = UserCurrency.currency()
    totalprice = totalprice * rate
    return render_template("/customer/cart.html", numberproducts=numberproducts, totalprice=totalprice, products=products, allowcheckout=allowcheckout, rate=rate, symbol=symbol, currency=currency, productstock=productstock)

@app.route("/cart/remove",  methods=["POST"])
def remove_from_cart():
    # Remove the product from the cart
    product_name = request.form["product_name"]
    UserCart.removeproduct(product_name)
    return redirect("/cart")

@app.route("/cart/update", methods=["POST"])
def update_cart():
    # Update the quantity of the product in the cart
    product_name = request.form["product_name"]
    quantity = int(request.form["quantity"])
    stock = dbProduct.query.filter_by(name=product_name).first()
    #check if the quantity is greater than the stock
    if int(stock.stock) >= (quantity):
        #if it is, update the quantity
        for product in UserCart.getproducts():
            if product.name == product_name:
                product.updatequantity(quantity)
    return redirect("/cart")

@app.route("/cart/empty", methods=["POST"])
def empty_cart():
    # Empty the cart
    UserCart.emptycart()
    return redirect("/cart")

@app.route("/cart/checkout")
def checkout():
    # direct user to checkout page
    numberproducts = UserCart.gettotalproducts()
    totalprice = UserCart.gettotalprice()
    products = UserCart.getproducts()
    symbol = UserCurrency.currentsymbol()
    return render_template("/customer/checkout.html", numberproducts=numberproducts, totalprice=totalprice, products=products, symbol=symbol, currency = UserCurrency.currency())


@app.route("/cart/checkout/complete", methods=["POST","GET"])
def ordercomplete():

    #retrieve data from form
    Form = []
    Form.append(["Forename", request.form["forename"]])#0
    Form.append(["Surname", request.form["surname"]])#1
    Form.append(["Email", request.form["email"]])#2
    Form.append(["Street", request.form["street"]])#3
    Form.append(["City", request.form["city"]])#4
    Form.append(["Postcode", request.form["postcode"]])#5
    Form.append(["Card Number", request.form["cardnumber"]])#6
    Form.append(["Expiry Date", request.form["expirydate"]])#7
    Form.append(["CVV", request.form["cvv"]])#8

    #check data is valid
    UserValidation.reseterrors()
    UserValidation.isstring(Form[0][0], Form[0][1])
    UserValidation.isstring(Form[1][0], Form[1][1])
    UserValidation.email(Form[2][1])
    UserValidation.isstring(Form[4][0], Form[4][1])
    UserValidation.postcode(Form[5][1])
    UserValidation.onlynumbers(Form[6][0], Form[6][1])
    UserValidation.checkdate(Form[7][1])
    UserValidation.onlynumbers(Form[8][0], Form[8][1])

    #check length of data
    for field in Form:
        UserValidation.maxlength(field[0],field[1])

    #if data is invalid, return error
    if UserValidation.geterrors():

        return render_template("/customer/checkout.html", errors=UserValidation.geterrors(), currency = UserCurrency.currency())


    #if data is valid, create order
    order_details = UserCart.getproducts() 
    totalprice = UserCart.gettotalprice()
    order_date = datetime.now()
    shipping_date = datetime.now() + timedelta(days=7)
   
    #check if customer exists
    customer = dbCustomer.query.filter_by(email=Form[2][1]).first()
    if not customer:
        #create new customer if they don"t exist
        customer = dbCustomer(forename=Form[0][1], surname=Form[1][1], email=Form[2][1], street=Form[3][1], city=Form[4][1], postcode=Form[5][1])
        db.session.add(customer)
        db.session.commit()

    #creates reference number
    isnew = False
    while isnew == False:
        refnum = "SC-"
        for i in range(16):
            refnum += str(randint(0, 9))
            if not dbOrder.query.filter_by(ref_number=refnum).first(): #checks there isn"t already an order with that refnum
                isnew=True
    
    #create new order
    neworder = dbOrder(ref_number=refnum, total_price=totalprice, order_date=order_date, shipping_date=shipping_date, status="paid", customer_id=customer.id)
    db.session.add(neworder)
    db.session.commit()

    #add order items to order
    for item in order_details:
        product = dbProduct.query.filter_by(name=item.name).first()
        product.stock -= item.quantity
        neworderitem = dbOrder_Item(order_id=neworder.id, product_id=product.id, quantity=item.quantity, price=item.total)
        db.session.add(neworderitem)
    db.session.commit()

    #empty cart
    UserCart.emptycart()
    return render_template("/customer/ordercomplete.html",refnum = refnum, currency = UserCurrency.currency())






# <-------------------- Admin Routes -------------------->

@app.route("/admin")
def adminhome():
    #if the user is not logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    
    #get all the data needed for the admin home page
    lowstock = dbProduct.query.filter(dbProduct.stock <= 10).all()
    admins = dbAdmin.query.all()

    today = datetime.now()
    weekago = today - timedelta(days=7)
    recentloginattempts = dbLogin_Event.query.filter(dbLogin_Event.timestamp >= weekago)

    salesreport = []
    for order in dbOrder.query.all(): #for order in all existing order
        orderitems = dbOrder_Item.query.filter_by(order_id = order.id).all() #get all orderitems for that order
        for item in orderitems: #for each item that was retrieved
            found = False
            product = dbProduct.query.filter_by(id=item.product_id).first() #get the product name
            if salesreport !=[]: #if sales report is empty
                for sale in salesreport: #for each item in sales report
                    if sale.name == product.name: #if it is the same product
                        sale.increasequantity(item.quantity) #increase the quantity
                        found = True #set found to true and break the loop
                        break
            if found == False:
                salesreport.append(CartProduct(product.name, item.quantity, product.price))

    return render_template("/admin/index.html", lowstock=lowstock, admins=admins, salesreport=salesreport, recentloginattempts=recentloginattempts)


@app.route("/admin/login", methods=["GET","POST"])
def adminlogin():
    #if the user isn't logged in
    if request.method == "POST":
        #get the email and password from the form
        email = request.form["email"]
        password = request.form["password"]
        #if the user has exceeded the login attempts
        if UserAuth.exceeded_attempts(email):
            message = "Login Attempts Exceeded"
        #if the user has entered the wrong credentials
        elif UserAuth.check_credentials(email, password) != "correct":
            message = UserAuth.check_credentials(email, password)
        else:
            return redirect("/admin")
        return render_template("/admin/login.html", message=message)
            
    return render_template("/admin/login.html")

@app.route("/admin/logout")
def adminlogout():
    #logs the user out and redirects to the login page
    email = session["email"]
    Admin = dbAdmin.query.filter_by(email=email).first()
    UserAuth.record_attempt(Admin.id, "Logged Out", "Medium")
    session.pop("email", None)
    return redirect("/admin/login")

@app.route("/admin/create", methods=["POST"])
def createadmin():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    
    #get the data from the form
    forename = request.form["forename"]
    email = request.form["email"]
    password = request.form["password"]

    #validate the data
    UserValidation.reseterrors()
    UserValidation.email(email)
    UserValidation.isstring("forename", forename)
    UserValidation.maxlength("forename",forename)
    UserValidation.checkpassword(password)
    errors = UserValidation.geterrors()

    #if there are errors, return the errors
    if errors:
        return render_template("/admin/index.html", message=errors)
    
    #if there are no errors, hash the password and create a new admin account
    hashed = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
    newadmin = dbAdmin(forename=forename, email=email, password=hashed)
    db.session.add(newadmin)
    db.session.commit()

    return render_template("/admin/index.html", message="New admin account created")

@app.route("/admin/products")
def adminproducts():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    products = dbProduct.query.all()
    
    return render_template("/admin/products.html", products=products, index = 0)
    
@app.route("/admin/products/filter", methods=["POST"])
def productfilter():
     #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    
    #get the data from the form
    sorter = request.form.get("sorter")
    order = request.form.get("order")
    searchitem = request.form.get("searchitem")
    #sort the products
    column = getattr(dbProduct, sorter) 
    products = UserValidation.sorter(column, order, dbProduct, searchitem)
    return render_template("/admin/products.html", products=products)
    

@app.route("/admin/products/add")
def adminaddproduct():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    return render_template("/admin/newedit.html", product_id=None, product=None)


@app.route("/admin/products/edit/<int:product_id>", methods=["GET","POST"])
def admineditproduct(product_id):
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    product = dbProduct.query.get(product_id)
    return render_template("/admin/newedit.html", product=product, product_id=product_id)


@app.route("/admin/products/update", methods=["POST","GET"])
def adminupdateproduct():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    
    if request.method == "POST":
        #get the data from the form
        product_id = request.form["product_id"]
        name = request.form["name"]
        description = request.form["description"]

        #check if an image has been uploaded
        image = request.files["image"]
        filename = secure_filename(image.filename)
        if filename != "":
            image_path = path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(image_path)
            img = "/static/uploads/" + filename

        colour = request.form["colour"]
        price = request.form["price"]
        stock = request.form["stock"]

        #check if the product already exists
        try:
            testint = int(product_id)
            product = dbProduct.query.get(product_id)
            product.name = name
            product.description = description
            #if an image has been uploaded, update the image
            if filename != "":
                to_remove = product.image.replace("/static/uploads/","")
                image_path = path.join(app.config["UPLOAD_FOLDER"], to_remove)
                remove(image_path)
                product.image = img
            product.colour = colour
            product.price = price
            product.stock = stock

        #if the product doesn't exist, create a new product
        except ValueError:
            product = dbProduct(name=name, description=description, image=img, colour=colour, price=price, stock=stock)
            db.session.add(product)
        db.session.commit()
        return redirect("/admin/products")

@app.route("/admin/products/delete", methods=["GET","POST"])
def admindeleteproduct():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    
    #get the product id from the form
    product_id = request.form["product_id"]
    #delete the product
    product = dbProduct.query.get(product_id)
    remove(product.image)
    db.session.delete(product)
    db.session.commit()
    return redirect("/admin/products")

@app.route("/admin/orders")
def adminorders():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    orders = dbOrder.query.all()
    return render_template("/admin/orders.html", orders=orders, index = 0)

@app.route("/admin/orders/<int:order_id>")
def adminvieweditorder(order_id):
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    
    #get the order, customer and order items
    order = dbOrder.query.get(order_id)
    order_id = order.id
    customer = dbCustomer.query.filter_by(id=order.customer_id).first()
    orderitems = dbOrder_Item.query.filter_by(order_id=order_id).all()
    products = []
    for item in orderitems:
        products = dbProduct.query.filter_by(id=item.product_id).all()

    return render_template("/admin/order.html", order=order, orderitems=orderitems, customer=customer, products=products)

@app.route("/admin/orders/filter", methods=["POST"])
def orderfilter():
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    #get the data from the form
    sorter = request.form.get("sorter")
    order = request.form.get("order")
    searchitem = request.form.get("searchitem")
    #sort the orders
    column = getattr(dbOrder, sorter) 
    orders = UserValidation.sorter(column, order, dbOrder, searchitem)
    return render_template("/admin/orders.html", orders = orders)
    
@app.route("/admin/orders/<int:order_id>/update", methods=["GET","POST"])
def adminupdateorder(order_id):
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
        
    if request.method == "POST":
        #get the data from the form
        order_id = request.form["order_id"]
        order = dbOrder.query.get(order_id)
        #update the order
        order.ref_number = request.form["ref_number"]
        order.total_price = request.form["total_price"]
        order.order_date = request.form["order_date"]
        order.shipping_date = request.form["shipping_date"]
        order.status = request.form["status"]

        #get the customer data
        customer_id = request.form["customer_id"]
        customer = dbOrder.query.get(customer_id)
        #update the customer data
        customer.forename = request.form["forename"]
        customer.surname = request.form["surname"]
        customer.email = request.form["email"]
        customer.street = request.form["street"]
        customer.city = request.form["city"]
        customer.postcode = request.form["postcode"]

        db.session.commit()
    return redirect("/admin/orders")

@app.route("/admin/orders/updatestatus/<int:order_id>", methods=["POST"])
def adminupdatestatus(order_id):
    #if the user isn't logged in, redirect to login page
    if "email" not in session:
        return redirect("/admin/login")
    #get the data from the form
    status = request.form["status"]
    order = dbOrder.query.get(order_id)
    order.status = status
    db.session.commit()
    return redirect("/admin/orders")



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)