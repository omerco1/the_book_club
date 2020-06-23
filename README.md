# The Book Club Web Application

Web Programming with Python and JavaScript

The book club is a web application written in flask, html, bootstrap and javascript that utilizes postgressql to create a website for book reviewing! Users are able to leave a review for any book that exists on our database. This project was meant as a learning experience to interact with thirdparty API's (from GoodReads, active SQL databases as well as building my own API backend. 

Link to live demo: 

https://book-reviewing-web-app.herokuapp.com/

This site features a backend API, try it out for youself!

Input: 
GET <url>/api/*isbn*
  
Example Output JSON: 

{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}


Login Screen: 
![alt text](https://raw.githubusercontent.com/omerco1/the_book_club/master/login_screen.png)

Feed Example: 
![alt text](https://raw.githubusercontent.com/omerco1/the_book_club/master/feed.png)

Book Profile Screen: 
![alt text](https://raw.githubusercontent.com/omerco1/the_book_club/master/book_profile.png)

