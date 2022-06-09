#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func
from models import *
import sys
from datetime import datetime
from flask_wtf import form

from sqlalchemy.orm import load_only



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # query Venue table by city and state name 
  unique_areas = Venue.query.options(load_only('city', 'state')).with_entities(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
  data = list()
  for area in unique_areas:
    area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venue_data = list()
    for venue in area_venues:
      venue_data.append({
        "id": venue.id,
        "name": venue.name, 
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==1).filter(Show.start_time>datetime.now()).all())
      })
      data.append({
        "city":  area.city,
        "state": area.state, 
        "venues": venue_data
      })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  data = []
  search_term = request.form.get('search_term', '')
  #ensures it is case insensitive
  results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  for search in results:
    data.append({
      "id": search.id,
      "name": search.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == search.id).filter(Show.start_time > datetime.now()).all()),
    })
  
  response={
    "count": len(results),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  try:
    venue = Venue.query.get(venue_id)
    past_shows_query= db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
    upcoming_shows_query= db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
    past_shows_data=[]
    upcoming_shows_data=[]
    for show in past_shows_query:
      past_shows_data.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

    for show in upcoming_shows_query:
      upcoming_shows_data.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
    })

    data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows_data,
      "upcoming_shows": upcoming_shows_data,
      "past_shows_count": len(past_shows_data),
      "upcoming_shows_count": len(upcoming_shows_data),
    }
  except:
    print(sys.exc_info())
    return abort(404, description="Resource not found")
  return render_template('pages/show_venue.html', venue=data)
 

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # data = data object returned from db insertion
  
  error = False
  try:
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    # will pull multiple items (genres)into a list
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website_link = request.form['website_link']
    #threw an error constraint not defined in models
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
  except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
  finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' +
                  request.form['name'] + ' Could not be listed!')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
  return render_template('pages/home.html')  


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred, Venue could not be deleted.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # data returned from querying the database
  data = db.session.query(Artist).all()
  if not data:
    flash('No Artist found, please list one!')
    return redirect(url_for('create_artist_form'))
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # case-insensitive search on artists with partial string search
  
  data=[]
  search_term = request.form.get('search_term', '')
  results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()

  for search in results:
    data.append({
      "id": search.id,
      "name": search.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == search.id).filter(Show.start_time > datetime.now()).all()),
    })
  
  response={
    "count": len(results),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  try:
    artist_query = db.session.query(Artist).get(artist_id)
    past_shows_query= db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
    past_shows_data=[]
    upcoming_shows_data=[]
    for show in past_shows_query:
      past_shows_data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
    for show in upcoming_shows_query:
      upcoming_shows_data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

    data = {
      "id": artist_query.id,
      "name": artist_query.name,
      "genres": artist_query.genres,
      "city": artist_query.city,
      "state": artist_query.state,
      "phone": artist_query.phone,
      "website": artist_query.website,
      "facebook_link": artist_query.facebook_link,
      "image_link": artist_query.image_link,
      "seeking_venue": artist_query.seeking_venue,
      "seeking_description": artist_query.seeking_description,
      "past_shows": past_shows_data,
      "upcoming_shows": upcoming_shows_data,
      "past_shows_count": len(past_shows_data),
      "upcoming_shows_count": len(upcoming_shows_data),
    }        
  except:
    print(sys.exc_info())
    return abort(404, description="Resource not found")
  return render_template('pages/show_artist.html', artist=data)
  
  

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # populate form with fields from artist with ID <artist_id>
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if artist is None:
    return abort(404, description="Resource not found")

  elif artist: 
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)  
  
  

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False  
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. Artist could not be edited.')
  if not error: 
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # populate form with values from venue with ID <venue_id>
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)
 

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # takes values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False  
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash(f'An error occurred. Venue could not be edited')
  if not error: 
    flash(f'Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion
  error = False
  try:
    artist=Artist() 
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres'),
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False
    artist.seeking_description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: # if error  flash failure
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  if not error:# on successful db insert, flash success 
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = db.session.query(Show).join(Artist).join(Venue).all()
  if not shows:
    flash('No shows to be listed,create one!')
    return redirect(url_for('create_shows'))
  data = []
  for show in shows: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  error= False
  try:
    show = Show()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time = request.form['start_time']
    db.session.add(show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      # unsuccesful db insert,flash failure
      flash('An error occurred. Requested show could not be listed.')
    else:
      # successful db insert, flash success
      flash('Requested show was successfully listed')
  return render_template('pages/home.html')
  
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#


#running flask specifying port

if __name__ == '__main__':
   app.run(host="0.0.0.0")

