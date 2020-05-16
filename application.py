import os
import uuid
from flask import Flask, session, request, redirect, url_for
from flask_session import Session
from flask import render_template
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, Date, Float, MetaData

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

app.config["SECRET_KEY"]= 'Cza8wCCc2vKc-qHwzL5YFA'
app.static_folder = 'static'
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

class userauth:
    timesloggedin = 0
    username = ''
    auth_failed = False

    def check_user_or_insert(self, user, passw):
        session['username'] = user
        if (db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": user,"password": passw}).rowcount == 0): 
            db.execute("INSERT INTO users (username, password, useruuid, timesloggedin) VALUES (:username, :password, :useruuid, :timesloggedin)", {"username": user, "password": passw, "useruuid": uuid.uuid1(),  "timesloggedin": 1})
            db.commit()
            self.timesloggedin = 1 
            self.username = user
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
blankuser = userauth()

@app.route('/', methods=['GET', 'POST'])
def my_form_post():

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
        return render_template('/login.html', user = ua)
    return render_template('login.html', user=blankuser)

@app.route("/home")
def home():
    userdata = dict()
    if session.get("username", None) is not None: 
        userdata = ua.get_user_data(session.get('username'))
        return render_template('home.html', user=userdata)
    else: 
        print('Username not found!')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print('attempting to register') 
    return render_template('register.html', user=ua)

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



def init_tables():
    print('Checking/Creating tables... ')

    books_table_name = 'books'
    users_table_name = 'users'
    reviews_table_name = 'reviews'
    local_books_file_name = 'books.csv'
    
    metadata = MetaData(engine)

    Table(users_table_name, metadata,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('username', String, nullable=False),
    Column('password', String, nullable=False),
    Column('useruuid', String, nullable=False),
    Column('timesloggedin', Integer, nullable=False))

    # if not table_exists(books_table_name):
    # create table sql query (doesnt work): 
    #db.execute("CREATE TABLE %s (bookid SERIAL NOT NULL PRIMARY KEY, title TEXT NOT NULL, isbn TEXT NOT NULL, author TEXT NOT NULL, yearpublished INT NOT NULL)" % books_table_name)

    # Create a table with the appropriate Columns
    Table(books_table_name, metadata,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('yearpublished', Integer, nullable=False),
    Column('title', String, nullable=False),
    Column('isbn', String, nullable=False),
    Column('author', String, nullable=False))

    Table(reviews_table_name, metadata,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('datae', Date, nullable=False),
    Column('title', String, nullable=False),
    Column('reviewbody', String, nullable=False),
    Column('userid', String, nullable=False),
    Column('numstars', String, nullable=False)
    )

    metadata.create_all() 

@app.before_first_request
def _run_on_start():
    app.run(debug=True) 
    init_tables()



    