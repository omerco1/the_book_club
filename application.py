import os
import uuid
from flask import Flask, session, request, redirect, url_for
from flask_session import Session
from flask import render_template
import sqlalchemy
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, Date, Float, MetaData, BigInteger
from setup_books import load_book_data_from_csv
from flask import jsonify

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
good_reads_key = os.getenv("GOOD_READS")
db = scoped_session(sessionmaker(bind=engine))

class book_profile:

    book_data = dict()
    review_data = dict() 
    username= ''
    average_review = 0 
    average_review_int = 0
    total_num_reviews = 0
    no_reviews = True
    already_reviewed_book = False
    err_msg = ''

    def __init__(self): 
        print("initializing book profile")

    
class userauth:
    timesloggedin = 0
    username = ''
    auth_failed = False
    err_msg = ''
    search_query = ''
    placed_search = False
    blank_search = False 
    search_results = {}

    def authenticate_user(self, user, passw):
        session['username'] = user
        result_proxy = db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": user, "password": passw})
        
        if (result_proxy.rowcount == 0): 
            print('USER NOT FOUND!!!!')
            self.auth_failed = True
            self.err_msg = 'The username or password you entered is incorrect, please try again. '
            return False
        else: 
            query_dict = self.get_dict_from_resultproxy(result_proxy, True)
            incremented_times_logged = query_dict['timesloggedin'] + 1 
            self.timesloggedin = incremented_times_logged
            self.username = query_dict['username']
            db.execute("UPDATE users SET timesloggedin = :timesloggedin WHERE username = :username", {"timesloggedin": incremented_times_logged, "username": user})
            db.commit()         
            return True 

    def __init__(self): 
        print("initializing user auth")

    def get_dict_from_resultproxy(self, result_proxy, singleItem): 
        result = {'items': []}
        ditem = dict()
        for rowp in result_proxy: 
            for column, value in rowp.items():
                ditem = {**ditem, **{column: value}}
            result['items'].append(ditem)
        
        if singleItem: 
            return ditem
        else: 
            return result
    
    def select_username_from_uuid(self, uuid): 
        result_proxy = db.execute("SELECT username FROM users WHERE useruuid = :useruuid", {"useruuid": uuid})
        return self.get_dict_from_resultproxy(result_proxy, True)
    
    def is_username_taken(self, username): 
        return (db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount >= 1)
    
    def get_user_data(self, username): 
        rp = db.execute("SELECT * FROM users WHERE username = :username", {"username": username})
        return self.get_dict_from_resultproxy(rp, True)
    
    def process_search_request(self): 
        if self.search_query =='':
            return 

        search_int = -1 
        if len(self.search_query) < 5: 
            try:
                search_int = int(self.search_query)
            except:    
                search_int= -1 
                
        result_proxy = None 
        if search_int != -1: 
            if search_int < 9999: 
                print('SEARCHING BY YEAR')
                result_proxy = db.execute("SELECT * FROM books WHERE yearpublished = :yearpublished LIMIT 25", {"yearpublished": search_int})
        else:
            #result_proxy = db.execute("SELECT * FROM books WHERE author LIKE :author OR title LIKE :title OR isbn LIKE :isbn", {"author": self.search_query, "title": self.search_query, "isbn": self.search_query})
            result_proxy = db.execute("SELECT * FROM books WHERE author LIKE " + "\'%" + self.search_query + "%\'" + " OR title LIKE "+ "\'%" + self.search_query + "%\'" +" OR isbn LIKE "+ "\'%" + self.search_query + "%\' LIMIT 25" )
        
        result = self.get_dict_from_resultproxy(result_proxy, False)

        if  not len(result['items']): 
            self.blank_search = True
            self.err_msg = "No results found!"
        else: 
            self.blank_search = False
        
        return result
        

ua = userauth()
blankuser = userauth()

@app.route('/', methods=['GET', 'POST'])
def my_form_post():
    session.pop("username", None)
    if request.method == 'POST':
        #SeSSION LOGIC GOES HERE 
        try:
            session.pop('username', None)
        except:
            print('no session to pop')

        userEmail = request.form['username']
        userPassword = request.form['password']

        if userEmail == "" or userPassword =="": 
            return render_template('layout.html', message="Please enter a valid email and password")
        
        if (ua.authenticate_user(userEmail, userPassword)): 
            return redirect(url_for('fetch_feed'))
        else: 
            return render_template('login.html', user = ua)
        #using session, for an already registered user: 
        #redirect(url_for('profile'))
        
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

        user_email = request.form['username']
        user_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if (user_email == "" or user_password == "" or confirm_password == ""): 
            ua.err_msg = "Please enter a valid email and password"
            ua.auth_failed = True 
            return render_template('register.html', user=ua)

        if (user_password != confirm_password):
            ua.err_msg = "The passwords entered don't match!"
            ua.auth_failed = True 
            return render_template('register.html', user=ua)

        # Registering for a new account 
        if ua.is_username_taken(user_email): 
            ua.err_msg = "That email already has an account registered to it, forgot password?"
            ua.auth_failed = True 
            return render_template('register.html', user=ua)

        db.execute("INSERT INTO users (username, password, useruuid, timesloggedin) VALUES (:username, :password, :useruuid, :timesloggedin)", {"username": user_email, "password": user_password, "useruuid": uuid.uuid1(),  "timesloggedin": 1})
        db.commit()

        return render_template('login.html', user = blankuser)
    return render_template('register.html', user=ua)

@app.route("/signout")
def sign_out(): 
    username = '' 
    if session.get("username", None) is not None: 
        username = session.get('username')
    
    session.pop("username", None)
    return redirect(url_for('my_form_post'))

@app.route("/feed", methods=['GET', 'POST'])
def fetch_feed(): 
    username = '' 
    search_request = ''

    if request.method == 'POST':
        ua.search_query = search_request = request.form['searcher']
        ua.placed_search = True 
        ua.search_results = ua.process_search_request()

        print(ua.search_results)
        
    if session.get("username", None) is not None: 
        ua.username = username = session.get('username')
    return render_template('feed.html', user=ua)

@app.route("/feed/<int:book_id>/",  methods=['GET', 'POST'])
def fetch_book(book_id): 

    bp = book_profile()
    username = '' 
    if session.get("username", None) is not None: 
        bp.username = ua.username = username = session.get('username')

    ua.already_reviewed_book = False 
    user = ua.get_dict_from_resultproxy(db.execute("SELECT * FROM users WHERE username = :username", {"username": username}), True)

    if request.method == 'POST': 
        num_stars = request.form['num_stars']
        review_title = request.form['review_title']
        review_body = request.form['rtext_area']

        result_proxy = db.execute("SELECT * FROM reviews WHERE userid = :useruuid AND bookid = :bookid", {"useruuid": user['useruuid'], 'bookid': book_id})

        if result_proxy.rowcount == 0: 
            db.execute("INSERT INTO reviews (bookid, title, reviewbody, userid, numstars) VALUES (:bookid, :title, :reviewbody, :userid, :numstars)", {"userid": user['useruuid'], "bookid": book_id, "title": review_title,  "reviewbody": review_body, 'numstars': num_stars})
            db.commit() 
            bp.no_reviews = False
        else: 
            bp.already_reviewed_book = True
            bp.err_msg = "You already submitted a review for this novel."

    result_proxy = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id})
    bp.book_data = ua.get_dict_from_resultproxy(result_proxy, True)

    result_proxy = db.execute("SELECT * FROM reviews WHERE bookid = :id", {"id": book_id})
    if result_proxy.rowcount == 0: 
        bp.no_reviews = True
    else: 
        bp.no_reviews = False
        bp.review_data = ua.get_dict_from_resultproxy(result_proxy, False)
        
        for item in bp.review_data['items']: 
            item.update(ua.select_username_from_uuid(item['userid']))

    result_proxy = db.execute("SELECT * FROM reviews WHERE userid = :useruuid AND bookid = :bookid", {"useruuid": user['useruuid'], 'bookid': book_id})
    if result_proxy.rowcount > 0: 
        bp.already_reviewed_book = True
        bp.err_msg = "You already submitted a review for this novel."


    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": good_reads_key, "isbns": bp.book_data['isbn']}).json() 
    rating = res['books'][0]

    bp.average_review = rating['average_rating']
    bp.average_review_int = int(float(rating['average_rating']))
    bp.total_num_reviews = rating['ratings_count']
    
    return render_template('book_profile.html', bp=bp)


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
    
    load_book_data = False 
    metadata = MetaData(engine)

    if not table_exists(books_table_name):
        load_book_data = True 

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
    Column('yearpublished', String, nullable=False),
    Column('title', String, nullable=False),
    Column('isbn', String, nullable=False),
    Column('author', String, nullable=False))

    Table(reviews_table_name, metadata,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('bookid', Integer, nullable=False),
    Column('title', String, nullable=False),
    Column('reviewbody', String, nullable=False),
    Column('userid', String, nullable=False),
    Column('numstars', Integer, nullable=False)
    )

    metadata.create_all() 

    if load_book_data: 
        load_book_data_from_csv(local_books_file_name, books_table_name, engine)


@app.route('/api/<string:isbn>', methods=['GET'])
def isbn_req(isbn):

    if session.get("username", None) is None: 
        return redirect(url_for('my_form_post'))

    result_proxy = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})

    if result_proxy.rowcount == 0: 
        return jsonify({'error': 'Invalid isbn!'}), 404


    result = dict() 
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": good_reads_key, "isbns": isbn}).json()
    gr_res = res['books'][0]

    result.update({'average_rating' : gr_res['average_rating'], 'ratings_count': gr_res['ratings_count']})

    db_book_data = ua.get_dict_from_resultproxy(result_proxy, True)

    result['isbn'] = isbn
    result['year']= db_book_data['yearpublished']
    result['author'] = db_book_data['author']
    result['title'] = db_book_data['title']

    return jsonify(result)

@app.before_first_request
def _run_on_start():
    init_tables() 
    
if __name__ == '__main__':
    app.run(port='5200')
    

# Notes for the future: 
# Defining tables using ORM
# class Flight(db.Model): 
#   __tablename__ = "flights"
#   id = db.Column(db.Integer, primary_key=True)
#   origin = db.Column(db.String, nullable=False) # These represent the columns
#   destination = db.Column(db.String, nullable=False)
#   duration = db.Column(db.Integer, nullable=False)
#
# class Passenger(db.Model): 
#   __tablename__ = "passengers"
#   id = db.Column(db.Integer, primary_key=True)
#   name = db.Column(db.String, nullable=False) 
#   flight_id = db.Column(db.Integer, db.ForeignKey("flights.id"),nullable=False)
#
# db.create_all()
#
# To INSERT: 
# db.session.add(Flight(origin='New York',destination='Paris', duration=540))
#
# Select * from Flights using ORM:
# Flight.query.all()
#
# Select * From flights where origin = paris: 
# Flight.query.filter_by(origin='Paris').all()
#
# Update flights SET duration = 200 WHERE id = 6 
# flight = Flight.query.get(6)
# flight.duration = 200 
# db.session.commit()
#
# Select * from flights JOIN passangers ON flights.id = passengers.flight_id; 
# db.session.query(Flight, Passenger).filter(Flight.id == Passenger.flight_id).all()
#
# Define a relationship on a FLights table (not by actually setting a column) within ORM class 
# passengers = db.relationship("Passenger", backref="flight", lazy=True)
#
# Relationships allow us to simplify associating two tables like so: 
# Passenger.query.filter_by(name="Alice").first().flight # <-- will return the flight object associated with this passenger
#
#
# API Get requests:
# 
# res = request.get(<url>/api/data) # Rather than specifying the params like so (/api/data )you can do this: 
# res =request.get(<url>, params={'api': api, 'base': base})


