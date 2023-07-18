from flask import Flask, render_template, url_for, redirect, request, flash, get_flashed_messages, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import relationship
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from flask_share import Share
import csv
import io

app = Flask(__name__)
stocks = ["these are my stocks"]
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'investmates'
db = SQLAlchemy(app)
share = Share(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    stocks = relationship('Stock', backref='user', cascade='all, delete-orphan')
    watchlist = relationship('Watchlist', backref='user', uselist=False)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    purchase_price = db.Column(db.Float, nullable = False)
    purchase_date = db.Column(db.DateTime, nullable = False, default=datetime.utcnow)

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stocks = db.Column(db.String(500), nullable=False, default="")
    current_prices = db.Column(db.String(500), nullable=False, default="")
    day_gains = db.Column(db.String(500), nullable=False, default="")


class RegisterForm(FlaskForm):
    email = StringField(validators=[
                            InputRequired(), Email(), Length(min=6, max=50)], render_kw={"placeholder": "Email"})
    
    username = StringField(validators=[
                            InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                            InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('That email address is already in use. Please log in instead.')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                            InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                            InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

def get_stock_price(stock_name):
    ticker = yf.Ticker(stock_name)
    stock_info = ticker.info
    current_price = stock_info.get('currentPrice')
    if not current_price:
        current_price = stock_info.get('previousClose')
    return current_price

def get_open_price(stock_name):
    ticker = yf.Ticker(stock_name)
    stock_info = ticker.info
    open_price = stock_info.get('open')
    return open_price

def generate_portfolio_chart(user_id):
    stocks_chart = db.session.query(Stock.name, Stock.purchase_date).filter_by(user_id=user_id).all()
    data = pd.DataFrame()

    for stock in stocks_chart:
        ticker = stock[0]
        start_date = stock[1]
        chart_data = yf.download(ticker, start=start_date)
        data = pd.concat([data, chart_data['Close']], axis=1)
    
    combined_prices = data.sum(axis=1)

    fig = go.Figure(data=go.Scatter(x=data.index, y=combined_prices))

    fig.update_layout(
    title='Total Portfolio Value vs Date',
    xaxis_title='Date',
    yaxis_title='Total Portfolio Value',
    width=750,
    height=500,
    margin=dict(l=20, r=20, t=50, b=10)
    )

    fig.update_layout(hovermode="x")

    chart_html = fig.to_html(full_html=False)
    return chart_html

def generate_pnl_chart(user_id):
    stocks = db.session.query(Stock.name, Stock.purchase_date).filter_by(user_id=user_id).all()
    data = pd.DataFrame()

    for stock in stocks:
        ticker = stock[0]
        start_date = stock[1]
        chart_data = yf.download(ticker, start=start_date)
        data = pd.concat([data, chart_data['Close']], axis=1)
    
    combined_prices = data.sum(axis=1)
    purchase_prices = db.session.query(Stock.purchase_price).filter_by(user_id=user_id).all()
    total_purchase_price = sum([price[0] for price in purchase_prices])
    
    pnl_percentage = ((combined_prices - total_purchase_price) / total_purchase_price) * 100

    fig = go.Figure(data=go.Scatter(x=data.index, y=pnl_percentage))

    fig.update_layout(
    title='PnL Percentage vs Date',
    xaxis_title='Date',
    yaxis_title='PnL Percentage',
    width=750,
    height=500,
    margin=dict(l=20, r=20, t=50, b=10)
    )

    fig.update_layout(hovermode="x")

    chart_html = fig.to_html(full_html=False)
    return chart_html

def get_news_articles(user_id):
    stocks = db.session.query(Stock.name).filter_by(user_id=user_id).all()
    article_list = []
    url_set = set()

    if not stocks:
        stocks = [['AAPL'], ['META'], ['TSLA'], ['NVDA']]

    for stock in stocks:
        articles = yf.Ticker(stock[0]).get_news()[:3]

        for article in articles:
            url = article['link']

            if url in url_set:
                continue

            url_set.add(url)

            title = article['title']
            publishTime = article['providerPublishTime']
            publisher = article['publisher']

            try:
                image = article['thumbnail']['resolutions'][0]['url']
            except KeyError:
                image = 'https://s.yimg.com/ny/api/res/1.2/P9MBOkJ1OrZEtuJrIcflFg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTM5NjtjZj13ZWJw/https://s.yimg.com/os/creatr-uploaded-images/2021-02/98384f80-7241-11eb-bfef-f660fde6ffaf'

            time_diff = (datetime.today().timestamp() - publishTime)/60/60

            if time_diff >= 1:
                time = str(int(time_diff)) + ' hours ago'
            else:
                time = str(int(time_diff * 60)) + ' minutes ago'

            article_list.append({'url': url, 'title': title, 'time': time, 'publisher': publisher, 'image': image, 'publishTime': publishTime})
    
    article_list.sort(reverse = True, key = lambda x: x['publishTime'])
    return article_list[:5]

def get_sector_pie(user_id):
    stocks = db.session.query(Stock.name).filter_by(user_id=user_id).all()
    sector_values = {}
    total_portfolio_value = 0

    for stock in stocks:
        ticker = yf.Ticker(stock[0])
        sector = ticker.info.get('sector')
        current_price = get_stock_price(stock[0])

        if sector and current_price:
            if sector in sector_values:
                sector_values[sector] += current_price
            else:
                sector_values[sector] = current_price

            total_portfolio_value += current_price

    data = pd.DataFrame({'Sector': list(sector_values.keys()), 'Value': list(sector_values.values())})
    data['Percentage'] = data['Value'] / total_portfolio_value * 100

    fig = px.pie(data, values='Percentage', names='Sector', title='Portfolio Composition by Sector', color_discrete_sequence=px.colors.sequential.RdBu)

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(legend_title='Sector', width=500, height=500)

    sector_html = fig.to_html(full_html=False)
    return sector_html


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['POST',"GET"])
@login_required
def dashboard():
    stocks = db.session.query(
        Stock.name,
        db.func.count().label('total_quantity'),
        db.func.avg(Stock.purchase_price).label('avg_purchase_price')
    ).filter_by(user_id=current_user.id).group_by(Stock.name).all()

    if request.method == 'POST':
        if 'csvFile' in request.files:
            csv_file = request.files['csvFile']
            if csv_file.filename.endswith('.csv'):
                csv_data = csv.reader(csv_file.read().decode('utf-8').splitlines())
                next(csv_data)

                for row in csv_data:
                    stock_name = row[0]
                    purchase_price = float(row[1])
                    purchase_date = datetime.strptime(row[2], '%d/%m/%Y').date()


                    stock = Stock(name=stock_name, user_id=current_user.id, 
                                  purchase_price=purchase_price, purchase_date=purchase_date)
                    db.session.add(stock)
                db.session.commit()

                flash('Stocks imported successfully!', 'success')
            else:
                flash('Invalid file format. Please select a CSV file.', 'danger')

            return redirect(url_for('dashboard'))
        
        return redirect(url_for('dashboard'))
    
    total_portfolio_value = 0
    total_day_gain = 0
    total_gain = 0
    
    stocks_with_data = []
    for stock in stocks:
        stock_name = stock[0]
        current_price = get_stock_price(stock_name)
        total_quantity = stock[1]
        avg_purchase_price = stock[2]
        total_value = total_quantity * current_price
        open_price = get_open_price(stock_name)
        day_gain = total_quantity * (current_price - open_price)
        total_day_gain += day_gain

        stock_data = (
            stock_name,
            total_quantity,
            '{:.2f}'.format(avg_purchase_price),
            '{:.2f}'.format(current_price),
            '{:.2f}'.format(total_value),
            '{:.2f}'.format(day_gain)
        )
        stocks_with_data.append(stock_data)
        
        total_portfolio_value += total_value
        total_gain += total_value - avg_purchase_price * total_quantity
    
    chart_type = request.args.get('chart_type', 'portfolio')

    if chart_type == 'portfolio':
        chart_html = generate_portfolio_chart(current_user.id)
    elif chart_type == 'pnl':
        chart_html = generate_pnl_chart(current_user.id)

    news_articles = get_news_articles(current_user.id)
    sector_html = get_sector_pie(current_user.id)

    watchlist = current_user.watchlist.stocks.split(',') if current_user.watchlist else []
    watchlist_current_prices = current_user.watchlist.current_prices.split(',') if current_user.watchlist else []
    watchlist_day_gains = current_user.watchlist.day_gains.split(',') if current_user.watchlist else []

    watchlist_data = zip(watchlist, watchlist_current_prices, watchlist_day_gains)

    return render_template('dashboard.html',
        stocks=stocks_with_data,
        total_portfolio_value='{:.2f}'.format(total_portfolio_value),
        total_day_gain='{:.2f}'.format(total_day_gain),
        total_gain='{:.2f}'.format(total_gain),
        chart_html = chart_html,
        chart_type = chart_type,
        news_articles = news_articles,
        watchlist_data = watchlist_data,
        sector_html = sector_html
        )


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        stock_name = request.form.get("Stock").upper()
        if not stock_name:
            return redirect(url_for('dashboard'))
        
        stock_quantity = int(request.form.get("stockQuantity"))
        purchase_price = request.form.get("purchasePrice")
        purchase_date = datetime.strptime(request.form.get("purchaseDate"), '%Y-%m-%d').date()

        for share in range(stock_quantity):
            stock = Stock(name=stock_name, user_id=current_user.id, 
                purchase_price=purchase_price, purchase_date=purchase_date)
            db.session.add(stock)
            db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return render_template('logout.html')


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        watchlist = Watchlist(user_id=new_user.id)
        db.session.add(watchlist)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    stock_symbol = request.form.get('stockInput').upper()
    if stock_symbol:
        watchlist = current_user.watchlist
        if watchlist:
            stocks = watchlist.stocks.split(',')
            if stock_symbol not in stocks:
                stocks.append(stock_symbol)
                watchlist.stocks = ','.join(stocks)
                current_prices = watchlist.current_prices.split(',')
                day_gains = watchlist.day_gains.split(',')
                current_price = get_stock_price(stock_symbol)
                open_price = get_open_price(stock_symbol)
                day_gain = (current_price - open_price)
                current_prices.append('{:.2f}'.format(current_price))
                day_gains.append('{:.2f}'.format(day_gain))
                watchlist.current_prices = ','.join(current_prices)
                watchlist.day_gains = ','.join(day_gains)
        else:
            watchlist = Watchlist(user_id=current_user.id, stocks=stock_symbol)
            current_price = get_stock_price(stock_symbol)
            open_price = get_open_price(stock_symbol)
            day_gain = (current_price - open_price)
            watchlist.current_prices = '{:.2f}'.format(current_price)
            watchlist.day_gains = '{:.2f}'.format(day_gain)
            db.session.add(watchlist)

        db.session.commit()

    return redirect(url_for('dashboard'))

if __name__ == "__main__":  
    with app.app_context():
        db.create_all()
    app.run(debug=True)