import smtplib
import sqlite3

import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app=app)
app.app_context().push()






class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(80))
    ticker_symbol = db.Column(db.String(50))
    price_threshold = db.Column(db.Float)
    phone = db.Column(db.Integer)
    frequency = db.Column(db.Integer)
    notification_type = db.Column(db.String(20))


@app.route('/', methods=['POST', 'GET'])
def index():

    #Get the user data of form
    if request.method == "POST":
        user_email = request.form['email_address']
        phone = request.form['phone']
        ticker = request.form['ticker']
        threshold = request.form['threshold']
        day = request.form['day']
        hour = request.form['hour']
        minute = request.form['minute']
        notification_type = request.form['notification_type']

        frequency = int(day)*24*60 + int(hour)*60 + int(minute)

        
        #Store the user input data into database
        notification = Notification(user_email=user_email,
                                    ticker_symbol=ticker, price_threshold=threshold, frequency=frequency, notification_type=notification_type, phone=phone)
        db.session.add(notification)
        db.session.commit()
        return 'Notification settings saved. You will receive a notification when the price of {} reaches or exceeds {} {}.'.format(ticker, threshold, notification_type)
    else:
        return render_template('main.html')


def check_price(ticker, threshold, notification_type, user_email, phone):
    # Retrieve the current price of the stock using the yfinance library
    stock = yf.Ticker(ticker).info
    price = stock['regularMarketPrice']

    # If the price reaches or exceeds the threshold, send a notification
    if price >= threshold:
        send_notification(notification_type, ticker, price, user_email,threshold)
    return price


def send_notification(notification_type, ticker, price, email,threshold):
    if notification_type == 'email':
        # Set up the email message
        from_email = 'stockprice.notifier01@gmail.com'
        to_email = email
        subject = 'Stock notification'
        body = f'The price of the stock with ticker symbol "{ticker}" has reached or exceeded the threshold of {threshold} and price is {price}.'

        msg = f'Subject: {subject}\n\n{body}'

        # Set up the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Log in to the email account
        server.login('stockprice.notifier01@gmail.com', 'axxnwukhrnwsoylv')

        # Send the email
        server.sendmail(from_email, to_email, msg)

        # Close the SMTP server
        server.quit()


if __name__ == '__main__':
   
    db.create_all()

    rows = Notification.query.all()

    # Start the scheduler for each saved notification
    scheduler = BackgroundScheduler()

    for row in rows:
        ticker, threshold, user_email, phone, frequency, notification_type = row.ticker_symbol, row.price_threshold, row.user_email, row.phone, row.frequency, row.notification_type
        print(ticker, threshold, user_email,
              phone, frequency, notification_type)

        scheduler.add_job(func=check_price, trigger='interval', args=[
            ticker, threshold, notification_type, user_email, phone], minutes=frequency)

    scheduler.start()

    app.run(debug=True)
