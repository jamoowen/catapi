import requests
from flask import Flask, render_template, redirect, session, request
from flask_session import Session
from random import randint
from config import api_key, username, user_password, host_name
from mysql.connector import connect, Error


application = Flask(__name__)


application.config["SESSION_TYPE"] = "filesystem"
Session(application)

# connects to mysql server
mydb = connect(
        host=host_name,
        user=username,
        password=user_password,
        database='user_accounts_cats'
    ) 
mycursor = mydb.cursor()

# calls thecatapi in order to retrieve data on cats of a given breed
def lookup(type):
    url = f"https://api.thecatapi.com/v1/images/search?breed_id={type}"
    response = requests.get(url)
    response.headers["x-api-key"] = api_key
    data = response.json()
    cat = data[0]
    return cat

# homepage 
@application.route('/', methods=["GET", "POST"])
def index():
    if request.method== "POST":
        try:
            breed = request.form.get("breed")
            cat = lookup(breed)
            cat_url = cat['url']
            price = randint(50, 500)
            cat_name = cat['breeds'][0]['name']
            return render_template('buy.html', breed=breed, cat=cat, cat_url=cat_url, price=price, cat_name=cat_name)
        except IndexError:
            return render_template('index.html')
        
    return render_template('index.html')



@application.route('/buy', methods=["GET", "POST"])
def buy():
    if request.method=="POST":
        try:
            price = int(request.form.get("cat_price"))
            cat_name = request.form.get("cat_name")
            balance = "SELECT * FROM customers WHERE id=%s"
            user_id = session["user_id"]
            name_user = (user_id,)
            mycursor.execute(balance, name_user)
            details = mycursor.fetchall()[0]
            cash_balance = details[3]
            equity_balance = details[4]

            # if user has sufficient funds, their account balance is credited and the apporpriate value of the purchased cat is recorded
            if cash_balance >= price:
                updated = "UPDATE customers SET cash = %s, cat_equity = %s WHERE id = %s"
                updated_cash = int(cash_balance)-price
                updated_equity = int(equity_balance)+price
                vals = (updated_cash, updated_equity, user_id)
                mycursor.execute(updated, vals)
                mydb.commit()
                return render_template('purchased.html', cat_name=cat_name, balance=equity_balance+price)

            sorry = "You have insufficient funds to purchase this animal"
            return render_template('purchased.html', cat_name=cat_name, sorry=sorry )
        except IndexError:
            print('indexerror¡¡¡')
            return redirect('/')
    return render_template('buy.html')

@application.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method=="POST":

        #
        user_name = request.form.get('username')
        pass_word = request.form.get('password')

        check = "SELECT id FROM customers WHERE username= %s"
        name_user = (user_name, )
        mycursor.execute(check, name_user)

        # ||||   CHECKS IF USER ALREADY EXISTS ||||
        try:
            xresult = mycursor.fetchall()[0][0]
            if xresult:
                print('exists you fool')
                return redirect('/exists')
        except IndexError:
            pass

        # if user doesnt already exist, enters info into database, setting a cookie to the user
        details = "INSERT INTO customers (username, password, cash, cat_equity) VALUES (%s, %s, %s, %s)"
        vals = (user_name, pass_word, 1000, 0)
        mycursor.execute(details, vals)
        mydb.commit()
        check = "SELECT id FROM customers WHERE username= %s"
        name_user = (user_name, )
        mycursor.execute(check, name_user)
        myresult = mycursor.fetchall()[0][0]
        session["user_id"] = myresult
        return redirect('/')
    return render_template('signup.html')

@application.route('/login', methods=["GET", "POST"])
def login():
    session.clear()
    
    if request.method=='POST':
        user_name = (request.form.get('username'),)
        pass_word = request.form.get('password')

        try:
            login_deets = "SELECT * FROM customers WHERE username=%s"
            mycursor.execute(login_deets, user_name)
            myresult = mycursor.fetchall()
            if myresult[0][2] == pass_word:
                session["user_id"] = myresult[0][0]
                return redirect('/')
              
        except IndexError:
            print('errorrrrrrrrr')
            return None
    return render_template('login.html')

@application.route('/purchased', methods=["GET", "POST"])
def purchased():
    return render_template('purchased.html')

@application.route('/exists', methods=["GET", "POST"])
def exists():
    return render_template("exists.html")






if (__name__)==('__main__'):
    application.run()

