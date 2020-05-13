import os
import uuid
from flask import Flask, session, request, redirect, url_for
from flask_session import Session
from flask import render_template
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

#Generating app SECRET_KEY: 
# import secrets 
# secrets.token_urlsafe(16)
# Note store more sensitive info in 'redis' database
# Session["USERNAME"] = ua.username
app.config["SECRET_KEY"]= 'Cza8wCCc2vKc-qHwzL5YFA'


app.static_folder = 'static'
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

class userauth:
    timesloggedin = 0
    username = ''

    def check_user_or_insert(self, user, passw):
        session['username'] = user
        if (db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": user,"password": passw}).rowcount == 0): 
            db.execute("INSERT INTO users (username, password, userid, timesloggedin) VALUES (:username, :password, :userid, :timesloggedin)", {"username": user, "password": passw, "userid": uuid.uuid1(),  "timesloggedin": 1})
            db.commit()
        else: 
            result_proxy = db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": user, "password": passw})
            query_dict = self.get_dict_from_resultproxy(result_proxy)

            incremented_times_logged = query_dict['timesloggedin'] + 1 
            self.timesloggedin = incremented_times_logged
            self.username = query_dict['username']
            db.execute("UPDATE users SET timesloggedin = :timesloggedin WHERE username = :username", {"timesloggedin": incremented_times_logged, "username": user})
            db.commit()         
        return

    def __init__(self): 
        print("initializing user auth")
        # self.check_user_or_insert(user, passw)

    def get_dict_from_resultproxy(self, result_proxy): 
        ditem = dict() 
        for rowp in result_proxy: 
            for column, value in rowp.items():
                ditem = {**ditem, **{column: value}}
        return ditem
    
    def is_username_taken(self, username): 
        return (db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount >= 1)
    
    def get_user_data(self, username): 
        rp = db.execute("SELECT * FROM users WHERE username = :username", {"username": username})
        return self.get_dict_from_resultproxy(rp)

ua = userauth()

@app.route('/', methods=['GET', 'POST'])
def my_form_post():
    print("IN POST %s " % request.method)
    if request.method == 'POST':
        print("OMER IN HERE")

        #SeSSION LOGIC GOES HERE 
        try:
            session.pop('username', None)
        except:
            print('no session to pop')

        userEmail = request.form['username']
        userPassword = request.form['password']

        if userEmail == "" or userPassword =="": 
            return render_template('layout.html', message="Please enter a valid email and password")
        
        # Registering for a new account 
        # if ua.is_username_taken(userEmail): 
        #     return render_template('layout.html', message="That email already has an account registered to it, forgot password?") 

        ua.check_user_or_insert(userEmail, userPassword)
        #using session, for an already registered user: 
        #redirect(url_for('profile'))
        return render_template('/home.html', user = ua)
    return render_template('index.html')

@app.route("/home")
def home():
    userdata = dict()
    if session.get("username", None) is not None: 
        userdata = ua.get_user_data(session.get('username'))
        return render_template('home.html', user=userdata)
    else: 
        print('Username not found!')
        return redirect(url_for('index'))

@app.route("/signout")
def sign_out(): 
    username = '' 
    if session.get("username", None) is not None: 
        username = session.get('username')
    
    session.pop("username", None)
    return redirect(url_for('my_form_post'))

@app.route("/feed")
def fetch_feed(): 
    username = '' 
    if session.get("username", None) is not None: 
        username = session.get('username')
    return render_template('feed.html', user=username)


def table_exists(name):
    ret = engine.dialect.has_table(engine, name)
    print('Table "{}" exists: {}'.format(name, ret))
    return ret

if __name__ == '__main__':

    books_table_name = 'books'

    if not table_exists(books_table_name):
        print('Building books table...')

    
    app.run(debug=True) 