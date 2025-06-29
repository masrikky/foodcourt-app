# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer') # 'customer', 'admin', 'kantin'
    orders = db.relationship('Order', backref='customer', lazy=True)
    ratings = db.relationship('Rating', backref='customer', lazy=True)
    # managed_kantin = db.relationship('Kantin', backref='manager', uselist=False, lazy=True) # Ini opsional, bisa juga dihapus jika tidak digunakan eksplisit dari User

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Kantin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    menus = db.relationship('Menu', backref='kantin', lazy=True)
    last_order_at = db.Column(db.DateTime, default=datetime.utcnow) 
    
    # PASTIKAN DUA BARIS INI ADA DI models.py milikmu!
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # FOREIGN KEY BARU
    manager = db.relationship('User', backref=db.backref('managed_kantin', uselist=False)) # RELASI BARU

    def __repr__(self):
        return f'<Kantin {self.name}>'

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    kantin_id = db.Column(db.Integer, db.ForeignKey('kantin.id'), nullable=False)
    image_url = db.Column(db.String(255), default='https://via.placeholder.com/150')

    def __repr__(self):
        return f'<Menu {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending') # 'pending', 'completed', 'cancelled'
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False) # Harga saat item dipesan

    menu = db.relationship('Menu', backref=db.backref('order_items', lazy=True))

    def __repr__(self):
        return f'<OrderItem {self.id} (Menu: {self.menu_id})>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text)
    rating_date = db.Column(db.DateTime, default=datetime.utcnow)

    menu = db.relationship('Menu', backref=db.backref('ratings', lazy=True))

    def __repr__(self):
        return f'<Rating {self.id} (Menu: {self.menu_id}, Score: {self.score})>'
