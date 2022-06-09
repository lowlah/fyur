
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website= db.Column(db.String(120)) 
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(400))
    shows = db.relationship('Show', backref="venue", lazy=True)
    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website= db.Column(db.String(120)) 
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(400))
    shows = db.relationship('Show', backref="artist", lazy=True)
    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'

class Show(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False) 
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)   
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    def __repr__(self):
        return f'<Show {self.id} {self.start_time} {self.artist_id} {self.venue_id}>'    
