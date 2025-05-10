import re
from sqlalchemy import func
from datetime import *


class CartProduct:
    #Each product in the cart is a class for simple attribute access
    def __init__(self, name, quantity, price):
        self.name = name
        self.quantity = quantity
        self.price = price
        self.total = quantity * price

    #increases the quantity by a given amount
    def increasequantity(self, amount):
        self.quantity += amount
        self.total = self.quantity * self.price

    #decreases the quantity by a given amount
    def decreasequantity(self, amount):
        self.quantity -= amount
        self.total = self.quantity * self.price

    #overrides the quantity in the cart
    def updatequantity(self, quantity):
        self.quantity = quantity
        self.total = self.quantity * self.price

class Cart():
    #holds all the products in the user's cart
    def __init__(self):
        self.cartproducts = []

    #gets the total price of all products in the cart
    def gettotalprice(self): 
        totalprice = 0
        if len(self.cartproducts) != 0:
            #if there are items in the cart then return total price
            for product in self.cartproducts:
                totalprice = totalprice + product.total
        return totalprice
    
    def gettotalproducts(self): 
        #gets the total number of products in the cart
        return len(self.cartproducts) 

    def getproducts(self): 
        #gets all products in the cart
        return self.cartproducts
    
    def addproduct(self, product): 
        #adds a product to the cart
        self.cartproducts.append(product)

    def removeproduct(self, product_name): 
        #removes a specified product from the cart
        for product in self.cartproducts:
            if product.name == product_name:
                self.cartproducts.remove(product)
                break

    def emptycart(self): 
        #removes all products from the cart
        self.cartproducts = []

class Validation():
    #handles input validation and the filter function
    def __init__(self):
        self.errors = []

    #resets the errors list
    def reseterrors(self):
        self.errors = []

    #checks email format is valid
    def email(self, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.errors.append("Invalid email address")

    #checks uk postcode is valid 
    def postcode(self, postcode):
        #uses government postcode regex
        if not re.match(r"^([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9]?[A-Za-z])))) [0-9][A-Za-z]{2})$", postcode):
            self.errors.append("Invalid postcode")

    #checks password is valid
    def checkpassword(self,password):
        #removes excess whitespace 
        password = password.strip()

        #checks password length is valid 
        if len(password) < 12:
            self.errors.append("Password must be at lest twelve characters long")

        upper = False
        lower = False
        digit = False
        special = False
        for char in password:
            #checks password contains uppercase letter
            if char.isupper():
                upper = True
            #checks password contains lowercase letter
            elif char.islower():
                lower = True
            #checks password contains a number
            elif char.isdigit():
                digit = True 
            else: 
            #checks password contains a special character
                special = True

        #appends error messages if any of the criteria isn't met
        if not upper:
            self.errors.append("Password must contain at least one uppercase letter")
        if not lower:
            self.errors.append("Password must contain at least one lowercase letter")
        if not digit:
            self.errors.append("Password must contain at least one digit")
        if not special:
            self.errors.append("Password must contain at least one special character")
    
    #checks date is valid
    def checkdate(self, date):
        #checks if date is in correct format
        if re.match(r"^\d{4}-(0[1-9]|1[0-2])$", date):

            year, month = map(int, date.split('-'))
            #checks that credit card expiry date is still valid
            if month == 12:
                expires = datetime(year+1, 1, 1)     
            else:
                expires = datetime(year, month+1, 1) 
                
            if expires < datetime.now():
                self.errors.append("Card has expired")
        else:
            self.errors.append("Invalid date")

    #checks that field only has letters
    def isstring(self, field, string):
        for char in string:
            if char.isnumeric():
                self.errors.append("Invalid " + field)
                break
            
    #checks that field only has numbers
    def onlynumbers(self, field, number):
        try:
            int(number)
        except ValueError:
            self.errors.append("Invalid " + field)

    #checks that field doesn't exceed 255 characters
    def maxlength(self, field, input):
        if len(input) > 255:
            self.errors.append("Invalid " + field + ". Max lenght exceeded ")

    #returns the list of errors
    def geterrors(self):
        return self.errors
    
    #filter and sorter function for admin products/orders
    def sorter(self, column, order, table, searchitem):
        #retrieve all rows which have the search item
        to_order = table.query.filter(column.contains(searchitem))
        #if the search field is blank, return all but order asc/desc
        if searchitem == "" :
            if order == 'asc':
                query = table.query.order_by(column.asc()).all()  
            else:
                query = table.query.order_by(column.desc()).all()
        elif to_order == []:
            query = []
        else:
            #return sorted rows that contain the search query 
            if order == 'asc':
                query = table.query.filter(column.contains(searchitem)).order_by(column.asc())  
            else:
                query = table.query.filter(column.contains(searchitem)).order_by(column.desc())
        return query 


#converts the currency
class CurrencyConverter():
    def __init__(self):
        #default currency gbp
        self.currentcurrency = 3
        self.currencies = ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY"]
        self.symbols = ["$", "€", "¥", "£", "$", "$", "₣", "¥"]
        self.rateagainstpound = ["1.23","1.15","168.75","1","1.88","1.67","1.11","10.12"]

    #sets new currency that the user is using
    def setnew(self,new):
        self.currentcurrency = int(new)

    #returns the current currency
    def currency(self):
        return(str(self.currentcurrency))
    
    #returns the current rate
    def currentrate(self):
        return float(self.rateagainstpound[self.currentcurrency])
    
    #returns the current symbol
    def currentsymbol(self):
        return self.symbols[self.currentcurrency]