from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Fix for PostgreSQL connection string (Render uses postgres:// but SQLAlchemy needs postgresql://)
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///canteen.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_canteen = db.Column(db.Boolean, default=False)
    canteen_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    canteen_name = db.Column(db.String(100), nullable=False)
    items = db.Column(db.JSON, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, preparing, ready, delivered
    reg_no = db.Column(db.String(50), nullable=True)
    hostel_name = db.Column(db.String(100), nullable=True)
    room_no = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Canteen data (in a real app, this would be in the database)

# Mapping of canteen names to their image filenames
CANTEEN_IMAGES = {
    "Juice & Milk Shake Shop (Anandam Cool Down Shop)": "Anandam cooldown shop.jpg",
    "Varshini Canteen": "Varshini canteen.jpg",
    "Aachi Velammal": "Aachi Vellamal.jpg",
    "Raja Restaurant": "Raja Restaurant.jpg",
    "Juice Club": "Juice club.jpg",
    "Bombay Chatwala": "Bombai Chatwala.jpg",
    "Radha Krishna Foods": "Radha Krishna Foods.jpg",
    "Godavari Ruchulu (Andhra Dosa & Meals)": "Godavari Ruchulu.jpg",
    "Healthy Tiffin Centre": "Healthy tiffin center.jpg",
    "Namu's Cake Shop": "Namus cake shop.jpg",
    "Hill View Kerala Mess (ACIC KIF Shop No. KL13)": "Hill view.jpg",
    "The Essence": "The Essence.jpg",
    "Kalki Foods": "Kalki foods.jpg"
}

CANTEENS = {
    "Juice & Milk Shake Shop (Anandam Cool Down Shop)": {
        "password": "1234",
        "categories": {
            "300 ml Juices": [
                {"name": "Kiwi Fruit Juice", "price": 55, "image": "https://images.unsplash.com/photo-1580013759032-c96505e24c1f?w=300&auto=format&fit=crop&q=80"},
                {"name": "Dragon Fruit Juice", "price": 55, "image": "https://images.unsplash.com/photo-1551024601-bc78ca4c7b73?w=300&auto=format&fit=crop&q=80"},
                {"name": "Fig Fruit Juice", "price": 55, "image": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=300&auto=format&fit=crop&q=80"},
                {"name": "Apple Juice", "price": 55, "image": "https://images.unsplash.com/photo-1568702846993-69181d481105?w=300&auto=format&fit=crop&q=80"},
                {"name": "Pomegranate Juice", "price": 50, "image": "https://images.unsplash.com/photo-1601643720153-5e8d6e8f9d6f?w=300&auto=format&fit=crop&q=80"},
                {"name": "Orange Juice", "price": 50, "image": "https://images.unsplash.com/photo-1612230820232-6c88f3a1a3d7?w=300&auto=format&fit=crop&q=80"},
                {"name": "Sathukudi Juice", "price": 50, "image": "https://images.unsplash.com/photo-1601498755722-9b6b8a8a3c5f?w=300&auto=format&fit=crop&q=80"},
                {"name": "Green Grape Juice", "price": 50, "image": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=300&auto=format&fit=crop&q=80"},
                {"name": "Dates Juice", "price": 50, "image": "https://images.unsplash.com/photo-1601001815894-4cd6fae49a0b?w=300&auto=format&fit=crop&q=80"},
                {"name": "Musk Melon Juice", "price": 50, "image": "https://images.unsplash.com/photo-1518621736915-f3b1c41bfd00?w=300&auto=format&fit=crop&q=80"},
                {"name": "Butter Fruit Juice", "price": 50, "image": "https://images.unsplash.com/photo-1512621776958-aeb51d1ee3e1?w=300&auto=format&fit=crop&q=80"},
                {"name": "Mango Juice", "price": 40, "image": "https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=300&auto=format&fit=crop&q=80"},
                {"name": "Grape Juice", "price": 40, "image": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=300&auto=format&fit=crop&q=80"},
                {"name": "Pineapple Juice", "price": 40, "image": "https://images.unsplash.com/photo-15502596055-3f511c3d14d2?w=300&auto=format&fit=crop&q=80"},
                {"name": "Lassi", "price": 40, "image": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=300&auto=format&fit=crop&q=80"},
                {"name": "B & C Juice", "price": 45, "image": "https://images.unsplash.com/photo-1551024601-bc78ca4c7b73?w=300&auto=format&fit=crop&q=80"},
                {"name": "Boost Banana Juice", "price": 40, "image": "https://images.unsplash.com/photo-1571771574825-e71c73a1d3f1?w=300&auto=format&fit=crop&q=80"},
                {"name": "Carrot Juice", "price": 55, "image": "https://images.unsplash.com/photo-1601050684374-9a8b6d6f8d6c?w=300&auto=format&fit=crop&q=80"},
                {"name": "Amla Juice", "price": 55, "image": "https://images.unsplash.com/photo-1580013759032-c96505e24c1f?w=300&auto=format&fit=crop&q=80"},
                {"name": "Chiku Juice", "price": 55, "image": "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=300&auto=format&fit=crop&q=80"},
                {"name": "Banana Juice", "price": 35, "image": "https://images.unsplash.com/photo-1571771574825-e71c73a1d3f1?w=300&auto=format&fit=crop&q=80"},
                {"name": "Papaya Juice", "price": 35, "image": "https://images.unsplash.com/photo-1551024601-bc78ca4c7b73?w=300&auto=format&fit=crop&q=80"},
                {"name": "Watermelon Juice", "price": 35, "image": "https://images.unsplash.com/photo-1564949442896-5f6f7b0e0e8b?w=300&auto=format&fit=crop&q=80"}
            ],
            "200 ml Special Drinks": [
                {"name": "Badam Fruits", "price": 30, "image": "https://images.unsplash.com/photo-1601050686425-3e9b2d2a2a4a?w=300&auto=format&fit=crop&q=80"},
                {"name": "Rose Milk", "price": 30, "image": "https://images.unsplash.com/photo-1601050686425-3e9b2d2a2a4a?w=300&auto=format&fit=crop&q=80"},
                {"name": "Fruit Mixer", "price": 25, "image": "https://images.unsplash.com/photo-1512621776958-aeb51d1ee3e1?w=300&auto=format&fit=crop&q=80"},
                {"name": "Rose Mixer", "price": 25, "image": "https://images.unsplash.com/photo-1601050686425-3e9b2d2a2a4a?w=300&auto=format&fit=crop&q=80"},
                {"name": "Lemon", "price": 15, "image": "https://images.unsplash.com/photo-1601001815894-4cd6fae49a0b?w=300&auto=format&fit=crop&q=80"},
                {"name": "Fresh Lemon", "price": 15, "image": "https://images.unsplash.com/photo-1601001815894-4cd6fae49a0b?w=300&auto=format&fit=crop&q=80"}
            ],
            "Milk Shakes": [
                {"name": "Dragon Fruit Shake", "price": 60, "image": "milkshake.jpg"},
                {"name": "Kiwi Fruit Shake", "price": 60, "image": "milkshake.jpg"},
                {"name": "Fig Fruit Shake", "price": 60, "image": "milkshake.jpg"},
                {"name": "Dates Shake", "price": 60, "image": "dates_milkshake.jpg"},
                {"name": "Apple Shake", "price": 60, "image": "apple_milkshake.jpg"},
                {"name": "Pomegranate Shake", "price": 60, "image": "pomegranate_milkshake.jpg"},
                {"name": "Orange Shake", "price": 60, "image": "orange_milkshake.jpg"},
                {"name": "Italian Shake", "price": 60, "image": "milkshake.jpg"},
                {"name": "Palkova Shake", "price": 60, "image": "palkova_milkshake.jpg"},
                {"name": "Cashew Shake", "price": 60, "image": "cashew_milkshake.jpg"},
                {"name": "Oreo Milk Shake", "price": 60, "image": "oreo_milkshake.jpg"},
                {"name": "Butterscotch Shake", "price": 60, "image": "butterscotch_milkshake.jpg"},
                {"name": "Mango Shake", "price": 60, "image": "mango_milkshake.jpg"},
                {"name": "Grape Shake", "price": 55, "image": "grape_milkshake.jpg"},
                {"name": "Pineapple Shake", "price": 55, "image": "pineapple_milkshake.jpg"},
                {"name": "Vanilla Shake", "price": 55, "image": "vanilla_milkshake.jpg"},
                {"name": "Chocolate Shake", "price": 55, "image": "chocolate_milkshake.jpg"},
                {"name": "Badam Shake", "price": 55, "image": "badam_milkshake.jpg"},
                {"name": "Papaya Shake", "price": 55, "image": "papaya_milkshake.jpg"},
                {"name": "Banana Shake", "price": 55, "image": "banana_milkshake.jpg"}
            ]
        }
    },
    "Varshini Canteen": {
        "password": "1234",
        "main_photo": "https://i.ibb.co/9y3R2Jc/Whats-App-Image-2025-11-05-at-5-11-27-PM.jpg",
        "categories": {
            "Non-Veg Items": [
                {"name": "Chicken 65", "price": 120},
                {"name": "Chicken Lollipop", "price": 120},
                {"name": "Chicken Manchurian", "price": 120},
                {"name": "Chicken Fried Rice", "price": 100},
                {"name": "Chicken Noodles", "price": 100},
                {"name": "Egg Fried Rice", "price": 80},
                {"name": "Egg Noodles", "price": 80},
                {"name": "Fish Fry", "price": 120},
                {"name": "Prawn Fry", "price": 120}
            ],
            "Veg Items": [
                {"name": "Veg Fried Rice", "price": 80},
                {"name": "Veg Noodles", "price": 80},
                {"name": "Paneer Fried Rice", "price": 100},
                {"name": "Paneer Noodles", "price": 100},
                {"name": "Gobi Manchurian", "price": 100},
                {"name": "Mushroom Fried Rice", "price": 100},
                {"name": "Mushroom Noodles", "price": 100}
            ],
            "Tandoori Items": [
                {"name": "Tandoori Chicken (Half)", "price": 180},
                {"name": "Tandoori Chicken (Full)", "price": 300},
                {"name": "Chicken Tikka", "price": 140},
                {"name": "Paneer Tikka", "price": 120},
                {"name": "Malai Tikka", "price": 130}
            ],
            "Chinese Starters": [
                {"name": "Veg Spring Roll", "price": 70},
                {"name": "Chicken Spring Roll", "price": 100},
                {"name": "Paneer 65", "price": 100},
                {"name": "Baby Corn 65", "price": 100}
            ],
            "Tiffin Items": [
                {"name": "Idly (2 pcs)", "price": 20},
                {"name": "Vadai (1 pc)", "price": 10},
                {"name": "Poori (2 pcs)", "price": 30},
                {"name": "Pongal", "price": 35},
                {"name": "Dosa", "price": 30},
                {"name": "Onion Dosa", "price": 50},
                {"name": "Masala Dosa", "price": 50},
                {"name": "Kal Dosa", "price": 40},
                {"name": "Set Dosa", "price": 50}
            ],
            "Parotta Items": [
                {"name": "Parotta (1 pc)", "price": 15},
                {"name": "Veg Kothu Parotta", "price": 70},
                {"name": "Egg Kothu Parotta", "price": 80},
                {"name": "Chicken Kothu Parotta", "price": 100}
            ],
            "Egg Items": [
                {"name": "Half Boil", "price": 15},
                {"name": "Full Boil", "price": 15},
                {"name": "Omelette", "price": 20},
                {"name": "Egg Dosa", "price": 40}
            ],
            "Meals & Biryani": [
                {"name": "Veg Meals", "price": 60},
                {"name": "Mini Meals", "price": 50},
                {"name": "Veg Biryani", "price": 70},
                {"name": "Chicken Biryani", "price": 100},
                {"name": "Egg Biryani", "price": 80},
                {"name": "Mutton Biryani", "price": 130}
            ]
        }
    },
    "Raja Restaurant": {
        "password": "1234",
        "categories": {
            "Menu": [
                {"name": "Idly", "price": 30},
                {"name": "Pongal", "price": 30},
                {"name": "Poori", "price": 30},
                {"name": "Vadai", "price": 7},
                {"name": "Sambar Rice", "price": 40},
                {"name": "Tomato Rice", "price": 40},
                {"name": "Lemon Rice", "price": 40},
                {"name": "Tamarind Rice", "price": 40},
                {"name": "Veg Biryani", "price": 40},
                {"name": "Curd Rice", "price": 40},
                {"name": "Chapati", "price": 15},
                {"name": "Parotta", "price": 15},
                {"name": "Veg Kothu Parotta", "price": 40},
                {"name": "Special Dosa", "price": 40},
                {"name": "Nice Dosa", "price": 40},
                {"name": "Ghee Dosa", "price": 50},
                {"name": "Onion Dosa", "price": 50},
                {"name": "Podi Dosa", "price": 50},
                {"name": "Masala Dosa", "price": 50},
                {"name": "Kal Dosa", "price": 20},
                {"name": "Kara Dosa", "price": 50}
            ]
        }
    },
    "Juice Club": {
        "password": "1234",
        "categories": {
            "Fresh Juices (300 ml)": [
                {"name": "Kiwi Fruit Juice", "price": 60},
                {"name": "Dragon Fruit Juice", "price": 60},
                {"name": "Fig Fruit Juice", "price": 60},
                {"name": "Apple Juice", "price": 55, "image": "https://images.unsplash.com/photo-1568702846993-69181d481105?w=300&auto=format&fit=crop&q=80"},
                {"name": "Pomegranate Juice", "price": 55},
                {"name": "Orange Juice", "price": 55},
                {"name": "Sathukudi Juice", "price": 55},
                {"name": "Grape Juice", "price": 50},
                {"name": "Musk Melon Juice", "price": 50, "image": "https://images.unsplash.com/photo-1518621736915-f3b1c41bfd00?w=300&auto=format&fit=crop&q=80"},
                {"name": "Butter Fruit Juice", "price": 50, "image": "https://images.unsplash.com/photo-1512621776958-aeb51d1ee3e1?w=300&auto=format&fit=crop&q=80"},
                {"name": "Mango Juice", "price": 45},
                {"name": "Watermelon Juice", "price": 40},
                {"name": "Papaya Juice", "price": 40},
                {"name": "Banana Juice", "price": 40}
            ],
            "Milk Shakes (300 ml)": [
                {"name": "Oreo Shake", "price": 70, "image": "https://images.unsplash.com/photo-1579954115565-d70f9a8d7bde?w=300&auto=format&fit=crop&q=80"},
                {"name": "Butterscotch Shake", "price": 70, "image": "https://images.unsplash.com/photo-1579954115565-d70f9a8d7bde?w=300&auto=format&fit=crop&q=80"},
                {"name": "KitKat Shake", "price": 70, "image": "https://images.unsplash.com/photo-1579954115565-d70f9a8d7bde?w=300&auto=format&fit=crop&q=80"},
                {"name": "Chocolate Shake", "price": 70, "image": "https://images.unsplash.com/photo-1579954115565-d70f9a8d7bde?w=300&auto=format&fit=crop&q=80"},
                {"name": "Badam Shake", "price": 60, "image": "https://images.unsplash.com/photo-1601050686425-3e9b2d2a2a4a?w=300&auto=format&fit=crop&q=80"},
                {"name": "Vanilla Shake", "price": 60, "image": "https://images.unsplash.com/photo-1579954115565-d70f9a8d7bde?w=300&auto=format&fit=crop&q=80"},
                {"name": "Banana Shake", "price": 60, "image": "https://images.unsplash.com/photo-1571771574825-e71c73a1d3f1?w=300&auto=format&fit=crop&q=80"},
                {"name": "Mango Shake", "price": 60, "image": "https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=300&auto=format&fit=crop&q=80"},
                {"name": "Pineapple Shake", "price": 60, "image": "https://images.unsplash.com/photo-15502596055-3f511c3d14d2?w=300&auto=format&fit=crop&q=80"},
                {"name": "Papaya Shake", "price": 60, "image": "https://images.unsplash.com/photo-1551024601-bc78ca4c7b73?w=300&auto=format&fit=crop&q=80"}
            ],
            "Special Drinks": [
                {"name": "Rose Milk", "price": 30, "image": "rose_milk.jpg"},
                {"name": "Fruit Mixer", "price": 30},
                {"name": "Lemon", "price": 20},
                {"name": "Fresh Lemon", "price": 20}
            ]
        }
    },
    "Bombay Chatwala": {
        "password": "1234",
        "categories": {
            "Chats": [
                {"name": "Pani Puri", "price": 40},
                {"name": "Masala Puri", "price": 40},
                {"name": "Samosa Chat", "price": 40},
                {"name": "Bhel Puri", "price": 40},
                {"name": "Pav Bhaji", "price": 50},
                {"name": "Chole Bhature", "price": 60},
                {"name": "Raj Kachori", "price": 60},
                {"name": "Aloo Tikki Chat", "price": 45},
                {"name": "Dahi Puri", "price": 45}
            ],
            "Sandwiches": [
                {"name": "Veg Sandwich", "price": 45},
                {"name": "Cheese Sandwich", "price": 55},
                {"name": "Grilled Sandwich", "price": 60},
                {"name": "Paneer Sandwich", "price": 60},
                {"name": "Chocolate Sandwich", "price": 60}
            ],
            "Tandoori Specials": [
                {"name": "Paneer Tikka", "price": 100},
                {"name": "Mushroom Tikka", "price": 100},
                {"name": "Baby Corn Tikka", "price": 100},
                {"name": "Malai Tikka", "price": 120}
            ],
            "Paratha Items": [
                {"name": "Aloo Paratha", "price": 50},
                {"name": "Paneer Paratha", "price": 60},
                {"name": "Gobi Paratha", "price": 55},
                {"name": "Methi Paratha", "price": 55}
            ],
            "Desserts & Drinks": [
                {"name": "Falooda", "price": 80},
                {"name": "Special Lassi", "price": 60},
                {"name": "Dry Fruit Lassi", "price": 70},
                {"name": "Rose Lassi", "price": 50},
                {"name": "Sweet Lassi", "price": 40}
            ]
        }
    },
    "Radha Krishna Foods": {
        "password": "1234",
        "categories": {
            "Tiffin": [
                {"name": "Idly", "price": 10},
                {"name": "Vadai", "price": 10},
                {"name": "Poori", "price": 25},
                {"name": "Pongal", "price": 25},
                {"name": "Dosa", "price": 25},
                {"name": "Masala Dosa", "price": 35},
                {"name": "Onion Dosa", "price": 35},
                {"name": "Kal Dosa", "price": 30},
                {"name": "Set Dosa", "price": 30}
            ],
            "Rice Varieties": [
                {"name": "Sambar Rice", "price": 40},
                {"name": "Tomato Rice", "price": 40},
                {"name": "Lemon Rice", "price": 40},
                {"name": "Curd Rice", "price": 40},
                {"name": "Veg Biryani", "price": 50},
                {"name": "Ghee Rice", "price": 50},
                {"name": "Pulao", "price": 50}
            ],
            "Meals": [
                {"name": "Mini Meals", "price": 50},
                {"name": "Full Meals", "price": 70},
                {"name": "Special Meals", "price": 90}
            ],
            "Starters": [
                {"name": "Gobi 65", "price": 80},
                {"name": "Paneer 65", "price": 100},
                {"name": "Mushroom 65", "price": 100},
                {"name": "Baby Corn 65", "price": 100},
                {"name": "Veg Manchurian", "price": 100}
            ],
            "Chinese Items": [
                {"name": "Veg Fried Rice", "price": 80},
                {"name": "Paneer Fried Rice", "price": 100},
                {"name": "Mushroom Fried Rice", "price": 100},
                {"name": "Gobi Fried Rice", "price": 100},
                {"name": "Veg Noodles", "price": 80},
                {"name": "Paneer Noodles", "price": 100},
                {"name": "Mushroom Noodles", "price": 100},
                {"name": "Gobi Noodles", "price": 100}
            ],
            "Roti Varieties": [
                {"name": "Chapati", "price": 15},
                {"name": "Parotta", "price": 15},
                {"name": "Veg Kothu Parotta", "price": 50},
                {"name": "Egg Kothu Parotta", "price": 60},
                {"name": "Paneer Kothu Parotta", "price": 70}
            ],
            "Tea & Coffee": [
                {"name": "Tea", "price": 10},
                {"name": "Coffee", "price": 10},
                {"name": "Boost", "price": 15},
                {"name": "Badam Milk", "price": 25}
            ],
            "Snacks": [
                {"name": "Samosa", "price": 15},
                {"name": "Cutlet", "price": 15},
                {"name": "Veg Puff", "price": 15},
                {"name": "Egg Puff", "price": 20}
            ]
        }
    },
    "Godavari Ruchulu (Andhra Dosa & Meals)": {
        "password": "1234",
        "categories": {
            "Dosa Varieties": [
                {"name": "Plain Dosa", "price": 40},
                {"name": "Onion Dosa", "price": 50},
                {"name": "Masala Dosa", "price": 50},
                {"name": "Podi Dosa", "price": 50},
                {"name": "Ghee Dosa", "price": 55},
                {"name": "Paneer Dosa", "price": 70},
                {"name": "Mysore Masala Dosa", "price": 60},
                {"name": "Set Dosa", "price": 50},
                {"name": "Rava Dosa", "price": 60},
                {"name": "Rava Onion Dosa", "price": 65}
            ],
            "Andhra Specials": [
                {"name": "Pulihora (Tamarind Rice)", "price": 40},
                {"name": "Tomato Pappu Rice", "price": 50},
                {"name": "Curd Rice", "price": 45},
                {"name": "Lemon Rice", "price": 45},
                {"name": "Sambar Rice", "price": 45},
                {"name": "Veg Biryani", "price": 60},
                {"name": "Ghee Rice", "price": 60}
            ],
            "Combo Meals": [
                {"name": "Mini Meals", "price": 60},
                {"name": "Full Meals", "price": 80},
                {"name": "Andhra Meals", "price": 90},
                {"name": "Special Meals", "price": 100}
            ],
            "Veg Curries": [
                {"name": "Veg Curry", "price": 50},
                {"name": "Aloo Fry", "price": 50},
                {"name": "Gobi Masala", "price": 60},
                {"name": "Paneer Masala", "price": 70},
                {"name": "Mushroom Masala", "price": 70}
            ],
            "Roti & Parotta": [
                {"name": "Chapati", "price": 15},
                {"name": "Parotta", "price": 15},
                {"name": "Veg Kothu Parotta", "price": 50},
                {"name": "Paneer Kothu Parotta", "price": 70}
            ],
            "Beverages": [
                {"name": "Butter Milk", "price": 20},
                {"name": "Lassi", "price": 30},
                {"name": "Fresh Lemon Juice", "price": 20}
            ]
        }
    },
    "Healthy Tiffin Centre": {
        "password": "1234",
        "categories": {
            "Breakfast / Tiffin": [
                {"name": "Idly (2 pcs)", "price": 20},
                {"name": "Vadai (1 pc)", "price": 10},
                {"name": "Poori (2 pcs)", "price": 25},
                {"name": "Pongal", "price": 30},
                {"name": "Upma", "price": 25},
                {"name": "Dosa", "price": 30},
                {"name": "Onion Dosa", "price": 40},
                {"name": "Masala Dosa", "price": 40},
                {"name": "Rava Dosa", "price": 45},
                {"name": "Set Dosa", "price": 35},
                {"name": "Kal Dosa", "price": 35}
            ],
            "Rice Items": [
                {"name": "Sambar Rice", "price": 40},
                {"name": "Tomato Rice", "price": 40},
                {"name": "Lemon Rice", "price": 40},
                {"name": "Curd Rice", "price": 40},
                {"name": "Veg Pulao", "price": 50},
                {"name": "Ghee Rice", "price": 50}
            ],
            "Meals": [
                {"name": "Mini Meals", "price": 50},
                {"name": "Full Meals", "price": 70}
            ],
            "Roti Varieties": [
                {"name": "Chapati", "price": 15},
                {"name": "Parotta", "price": 15},
                {"name": "Veg Kothu Parotta", "price": 50},
                {"name": "Egg Kothu Parotta", "price": 60}
            ],
            "Beverages": [
                {"name": "Tea", "price": 10},
                {"name": "Coffee", "price": 10},
                {"name": "Boost", "price": 15}
            ]
        }
    },
    "Namu's Cake Shop": {
        "password": "1234",
        "categories": {
            "Cakes (per slice or 100g)": [
                {"name": "Black Forest Cake", "price": 60},
                {"name": "White Forest Cake", "price": 60},
                {"name": "Chocolate Truffle", "price": 70},
                {"name": "Butterscotch Cake", "price": 60},
                {"name": "Vanilla Cake", "price": 50},
                {"name": "Red Velvet Cake", "price": 70},
                {"name": "Pineapple Cake", "price": 60},
                {"name": "Choco Lava Cake", "price": 70},
                {"name": "Honey Cake", "price": 50},
                {"name": "Strawberry Cake", "price": 60}
            ],
            "Pastries & Snacks": [
                {"name": "Cup Cake", "price": 30},
                {"name": "Brownie", "price": 50},
                {"name": "Choco Chip Muffin", "price": 40},
                {"name": "Banana Muffin", "price": 40},
                {"name": "Cookies (Pack)", "price": 30},
                {"name": "Tea Cake", "price": 40}
            ],
            "Waffles": [
                {"name": "Plain Waffle", "price": 70},
                {"name": "Chocolate Waffle", "price": 80},
                {"name": "Nutella Waffle", "price": 90},
                {"name": "Strawberry Waffle", "price": 80}
            ],
            "Beverages": [
                {"name": "Cold Coffee", "price": 60},
                {"name": "Hot Coffee", "price": 40},
                {"name": "Iced Mocha", "price": 70},
                {"name": "Milk Shake (any flavour)", "price": 70}
            ]
        }
    },
    "Aachi Velammal": {
        "password": "1234",
        "main_photo": "../Canteens/Aachi Vellamal.jpg",
        "categories": {
            "Tiffin Items": [
                {"name": "Idly (2 pcs)", "price": 20},
                {"name": "Vadai (1 pc)", "price": 10},
                {"name": "Poori (2 pcs)", "price": 25},
                {"name": "Pongal", "price": 30},
                {"name": "Upma", "price": 25},
                {"name": "Dosa", "price": 30},
                {"name": "Onion Dosa", "price": 40},
                {"name": "Masala Dosa", "price": 40},
                {"name": "Kal Dosa", "price": 35},
                {"name": "Set Dosa", "price": 35},
                {"name": "Rava Dosa", "price": 45}
            ],
            "Lunch Items": [
                {"name": "Veg Meals", "price": 60},
                {"name": "Mini Meals", "price": 50},
                {"name": "Sambar Rice", "price": 40},
                {"name": "Curd Rice", "price": 40},
                {"name": "Lemon Rice", "price": 40},
                {"name": "Tomato Rice", "price": 40},
                {"name": "Tamarind Rice", "price": 40},
                {"name": "Veg Biryani", "price": 50},
                {"name": "Ghee Rice", "price": 50}
            ],
            "Dinner": [
                {"name": "Chapati", "price": 15},
                {"name": "Parotta", "price": 15},
                {"name": "Veg Kothu Parotta", "price": 50},
                {"name": "Egg Kothu Parotta", "price": 60},
                {"name": "Paneer Kothu Parotta", "price": 70}
            ],
            "Beverages": [
                {"name": "Tea", "price": 10},
                {"name": "Coffee", "price": 10},
                {"name": "Boost", "price": 15},
                {"name": "Badam Milk", "price": 25}
            ],
            "Combo Offers": [
                {"name": "Idly + Vadai", "price": 25},
                {"name": "Poori + Pongal Combo", "price": 45},
                {"name": "Mini Meals + Drink", "price": 60}
            ]
        }
    },
    "Hill View Kerala Mess (ACIC KIF Shop No. KL13)": {
        "password": "1234",
        "categories": {
            "Kerala Specials": [
                {"name": "Appam (2 pcs)", "price": 30},
                {"name": "Puttu (1 plate)", "price": 35},
                {"name": "Idiyappam (3 pcs)", "price": 30},
                {"name": "Kappa (Tapioca)", "price": 35},
                {"name": "Parotta (1 pc)", "price": 15}
            ],
            "Kerala Curries": [
                {"name": "Kadala Curry", "price": 40},
                {"name": "Egg Curry", "price": 50},
                {"name": "Chicken Curry", "price": 80},
                {"name": "Beef Curry", "price": 90},
                {"name": "Fish Curry", "price": 90},
                {"name": "Prawn Curry", "price": 100}
            ],
            "Rice Varieties": [
                {"name": "Kerala Meals", "price": 70},
                {"name": "Ghee Rice", "price": 60},
                {"name": "Biriyani (Chicken)", "price": 90},
                {"name": "Biriyani (Beef)", "price": 100},
                {"name": "Biriyani (Egg)", "price": 70}
            ],
            "Snacks": [
                {"name": "Pazham Pori (Banana Fritters)", "price": 30},
                {"name": "Uzhunnu Vada", "price": 15},
                {"name": "Parippu Vada", "price": 15},
                {"name": "Banana Chips Packet", "price": 20}
            ],
            "Drinks & Desserts": [
                {"name": "Avil Milk", "price": 50},
                {"name": "Falooda", "price": 70},
                {"name": "Tea", "price": 10},
                {"name": "Black Tea", "price": 10},
                {"name": "Filter Coffee", "price": 15}
            ]
        }
    },
    "The Essence": {
        "password": "1234",
        "categories": {
            "Milkshakes": [
                {"name": "Death by Chocolate", "price": 90},
                {"name": "Oreo Shake", "price": 80},
                {"name": "KitKat Shake", "price": 80},
                {"name": "Brownie Shake", "price": 90},
                {"name": "Butterscotch Shake", "price": 70},
                {"name": "Vanilla Shake", "price": 70},
                {"name": "Strawberry Shake", "price": 70},
                {"name": "Mango Shake", "price": 70},
                {"name": "Cold Coffee Shake", "price": 80}
            ],
            "Ice Cream Sundaes": [
                {"name": "Chocolate Volcano", "price": 100},
                {"name": "Banana Split", "price": 90},
                {"name": "Nutty Delight", "price": 100},
                {"name": "Tutti Frutti", "price": 90},
                {"name": "Caramel Crunch", "price": 100}
            ],
            "Juices (No Added Sugar)": [
                {"name": "Watermelon", "price": 40},
                {"name": "Papaya", "price": 40},
                {"name": "Orange", "price": 50},
                {"name": "Pomegranate", "price": 55},
                {"name": "Apple", "price": 55},
                {"name": "Dragon Fruit", "price": 60},
                {"name": "Kiwi", "price": 60}
            ],
            "Desserts": [
                {"name": "Brownie with Ice Cream", "price": 90},
                {"name": "Chocolate Lava Cake", "price": 100},
                {"name": "Palkova Cup", "price": 50},
                {"name": "Fruit Bowl", "price": 60}
            ]
        }
    },
    "Kalki Foods": {
        "password": "1234",
        "categories": {
            "Snacks": [
                {"name": "Potato Chips (Spicy / Pepper Salt)", "price": 20},
                {"name": "Banana Chips", "price": 20},
                {"name": "Popcorn (Spicy / Cheese)", "price": 20},
                {"name": "Biscuits (Varieties)", "price": 20},
                {"name": "Sweet Rolls", "price": 20},
                {"name": "Seeval Ice / Cola Ice", "price": 20},
                {"name": "Kara Pori", "price": 20}
            ]
        }
    }
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def canteen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_canteen:
            flash('Canteen login required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/init_db')
def init_db():
    try:
        with app.app_context():
            db.create_all()
        return "Database initialized successfully!"
    except Exception as e:
        return f"Error initializing database: {str(e)}", 500

@app.route('/')
def index():
    try:
        if current_user.is_authenticated and current_user.is_canteen:
            return redirect(url_for('canteen_dashboard'))
        return render_template('index.html', canteens=CANTEENS, canteen_images=CANTEEN_IMAGES)
    except Exception as e:
        return f"Error loading homepage: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_canteen:
            return redirect(url_for('canteen_dashboard'))
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        identifier = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Check if this is a canteen login (check against CANTEENS dictionary)
        if identifier in CANTEENS and CANTEENS[identifier]["password"] == password:
            # Check if canteen user exists in database, if not create it
            user = User.query.filter_by(email=identifier, is_canteen=True).first()
            if not user:
                user = User(
                    email=identifier,
                    password=generate_password_hash(password, method='sha256'),
                    is_canteen=True,
                    canteen_name=identifier
                )
                db.session.add(user)
                db.session.commit()
            
            login_user(user, remember=remember)
            return redirect(url_for('canteen_dashboard'))
            
        # Regular user login
        user = User.query.filter_by(email=identifier, is_canteen=False).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            return redirect(url_for('dashboard'))
            
        # If we get here, login failed
        flash('Please check your login details and try again.', 'danger')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('login'))
                
            user = User(
                email=email,
                password=generate_password_hash(password),
                is_canteen=False
            )
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'danger')
        return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_canteen:
        return redirect(url_for('canteen_dashboard'))
    return render_template('dashboard.html', canteens=CANTEENS, canteen_images=CANTEEN_IMAGES)

@app.route('/canteen/<canteen_name>')
@login_required
def canteen_menu(canteen_name):
    if canteen_name not in CANTEENS:
        abort(404)
    return render_template('canteen_menu.html', 
                         canteen_name=canteen_name, 
                         canteen=CANTEENS[canteen_name],
                         canteen_images=CANTEEN_IMAGES)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    if current_user.is_canteen:
        return jsonify({'error': 'Canteen staff cannot place orders'}), 403
        
    if 'cart' not in session:
        session['cart'] = {}
    
    data = request.get_json()
    canteen_name = data.get('canteen_name')
    item_name = data.get('item_name')
    price = float(data.get('price', 0))
    
    if not all([canteen_name, item_name, price]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    cart_key = f"{canteen_name}::{item_name}"
    
    if cart_key in session['cart']:
        session['cart'][cart_key]['quantity'] += 1
    else:
        session['cart'][cart_key] = {
            'item_name': item_name,
            'price': price,
            'quantity': 1,
            'canteen_name': canteen_name,
            'price_mult_quantity': price
        }
    
    # Calculate total for this item
    session['cart'][cart_key]['price_mult_quantity'] = session['cart'][cart_key]['price'] * session['cart'][cart_key]['quantity']
    
    session.modified = True
    return jsonify({
        'success': True, 
        'cart_count': len(session['cart']),
        'item': session['cart'][cart_key]
    })

@app.route('/cart')
@login_required
def view_cart():
    if current_user.is_canteen:
        return redirect(url_for('canteen_dashboard'))
        
    cart = session.get('cart', {})
    total = sum(item.get('price_mult_quantity', 0) for item in cart.values())
    return render_template('cart.html', cart=cart, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if current_user.is_canteen:
        return redirect(url_for('canteen_dashboard'))
        
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        reg_no = request.form.get('reg_no')
        hostel_name = request.form.get('hostel_name')
        room_no = request.form.get('room_no')
        
        if not all([reg_no, hostel_name, room_no]):
            flash('Please fill in all delivery details', 'danger')
            return redirect(url_for('checkout'))
        
        # Group items by canteen
        canteen_orders = {}
        for item in session['cart'].values():
            canteen = item['canteen_name']
            if canteen not in canteen_orders:
                canteen_orders[canteen] = []
            canteen_orders[canteen].append({
                'name': item['item_name'],
                'price': item['price'],
                'quantity': item['quantity']
            })
        
        try:
            # Create orders for each canteen
            for canteen_name, items in canteen_orders.items():
                total_amount = sum(item['price'] * item['quantity'] for item in items)
                order = Order(
                    user_id=current_user.id,
                    canteen_name=canteen_name,
                    items=items,
                    total_amount=total_amount,
                    reg_no=reg_no,
                    hostel_name=hostel_name,
                    room_no=room_no,
                    status='pending'
                )
                db.session.add(order)
            
            db.session.commit()
            session.pop('cart', None)
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_history'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while placing your order. Please try again.', 'danger')
            return redirect(url_for('checkout'))
    
    return render_template('checkout.html', cart=session.get('cart', {}))

@app.route('/order/history')
@login_required
def order_history():
    if current_user.is_canteen:
        return redirect(url_for('canteen_dashboard'))
        
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)

@app.route('/cart/update/<action>/<item_key>')
@login_required
def update_cart_item(action, item_key):
    if current_user.is_canteen:
        return redirect(url_for('canteen_dashboard'))
        
    if 'cart' not in session or item_key not in session['cart']:
        flash('Item not found in cart', 'danger')
        return redirect(url_for('view_cart'))
    
    if action == 'increase':
        session['cart'][item_key]['quantity'] += 1
    elif action == 'decrease':
        if session['cart'][item_key]['quantity'] > 1:
            session['cart'][item_key]['quantity'] -= 1
    
    # Update the price_mult_quantity
    if 'price' in session['cart'][item_key]:
        session['cart'][item_key]['price_mult_quantity'] = \
            session['cart'][item_key]['price'] * session['cart'][item_key]['quantity']
    
    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<item_key>')
@login_required
def remove_from_cart(item_key):
    if current_user.is_canteen:
        return redirect(url_for('canteen_dashboard'))
        
    if 'cart' in session and item_key in session['cart']:
        del session['cart'][item_key]
        session.modified = True
        flash('Item removed from cart', 'success')
    else:
        flash('Item not found in cart', 'danger')
    
    return redirect(url_for('view_cart'))

@app.route('/api/cart/summary')
@login_required
def get_cart_summary():
    if current_user.is_canteen:
        return jsonify({'error': 'Canteen staff cannot view cart'}), 403
        
    cart = session.get('cart', {})
    cart_items = []
    
    for item_key, item in cart.items():
        cart_items.append({
            'id': item_key,
            'name': item.get('item_name', ''),
            'price': item.get('price', 0),
            'quantity': item.get('quantity', 1),
            'total': item.get('price', 0) * item.get('quantity', 1),
            'canteen': item.get('canteen_name', '')
        })
    
    return jsonify({
        'success': True,
        'items': cart_items,
        'total': sum(item['total'] for item in cart_items),
        'count': len(cart_items)
    })

@app.route('/canteen/dashboard')
@login_required
@canteen_required
def canteen_dashboard():
    try:
        orders = Order.query.filter_by(canteen_name=current_user.canteen_name).order_by(Order.created_at.desc()).all()
        return render_template('canteen_dashboard.html', orders=orders)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'danger')
        return render_template('canteen_dashboard.html', orders=[])

@app.route('/order/update_status/<int:order_id>', methods=['POST'])
@login_required
@canteen_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.canteen_name != current_user.canteen_name:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    status = request.json.get('status')
    if status in ['preparing', 'ready', 'delivered']:
        order.status = status
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid status'}), 400

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('cart', None)
    return redirect(url_for('index'))

# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create a default admin user if not exists
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_canteen=False
            )
            db.session.add(admin)
            db.session.commit()

@app.route('/init_db')
def init_db_route():
    with app.app_context():
        db.create_all()
        # Create a default admin user if not exists
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_canteen=False
            )
            db.session.add(admin)
            db.session.commit()
    return "Database tables created successfully!"

if __name__ == '__main__':
    # For local development only
    db_file = os.path.join(os.path.dirname(__file__), 'instance', 'canteen.db')
    if not os.path.exists(os.path.dirname(db_file)):
        os.makedirs(os.path.dirname(db_file))
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
