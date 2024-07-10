from . import db

class Product(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    name = db.Column(db.String(249))
    original_price = db.Column(db.String(249))
    discounted_price = db.Column(db.String(249))
    category = db.Column(db.String(249))