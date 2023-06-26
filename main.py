from flask import Flask, render_template, url_for, redirect, request
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
from datetime import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)
stocks = ["these are my stocks"]
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'investmates'
db = SQLAlchemy(app)

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

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    purchase_price = db.Column(db.Float, nullable = False)
    purchase_date = db.Column(db.DateTime, nullable = False, default=datetime.utcnow)


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
    width=900,  # Set the width of the chart
    height=400,  # Set the height of the chart
    margin=dict(l=10, r=10, t=10, b=10)  # Set the margin around the chart
    )

    chart_html = fig.to_html(full_html=False)
    return chart_html

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
    #stocks = Stock.query.filter_by(user_id=current_user.id).all()
    stocks = db.session.query(
        Stock.name,
        db.func.count().label('total_quantity'),
        db.func.avg(Stock.purchase_price).label('avg_purchase_price')
    ).filter_by(user_id=current_user.id).group_by(Stock.name).all()

    if request.method == "POST":
        
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
    
    chart_html = generate_portfolio_chart(current_user.id)

    return render_template('dashboard.html',
        stocks=stocks_with_data,
        total_portfolio_value='{:.2f}'.format(total_portfolio_value),
        total_day_gain='{:.2f}'.format(total_day_gain),
        total_gain='{:.2f}'.format(total_gain),
        chart_html = chart_html
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
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


if __name__ == "__main__":  
    with app.app_context():
        db.create_all()
    app.run(debug=True)