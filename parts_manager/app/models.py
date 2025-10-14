from . import db
from datetime import datetime

part_tag = db.Table('part_tag',
    db.Column('part_id', db.Integer, db.ForeignKey('part.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    package = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100))
    note = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    qr_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('Tag', secondary=part_tag, backref='parts')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
