# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite",
                       connect_args={'check_same_thread': False})

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(bind=engine)

# Helper function: Get the date object for 12 months before the last recorded date
def get_year_ago():
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    last_date_obj = dt.datetime.strptime(last_date[0], "%Y-%m-%d").date()
    year_ago = last_date_obj - dt.timedelta(weeks=52, days=1)
    return year_ago

# Helper function: Get the string of the most active station
def get_most_active_station():
    sel = [station.station, func.count(measurement.id)]
    active_stations = session.query(*sel).filter(station.station==measurement.station)\
        .group_by(station.station).order_by(func.count(measurement.id)\
                                            .desc()).all()
    most_active = active_stations[0][0]
    return most_active

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    return (
        """<h1><b>Welcome to the climate app home page.</b></h1><br/><br/>

<b>List of all available api routes:</b><br/>
/api/v1.0/precipitation<br/>
/api/v1.0/stations<br/>
/api/v1.0/tobs<br/>
/api/v1.0/&lt;start&gt;<br/>
/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>
"""
    )


@app.route("/api/v1.0/precipitation")
def get_precipitation():
    year_ago = get_year_ago()
    year_scores = session.query(measurement.date, func.avg(measurement.prcp))\
    .filter(measurement.date >= year_ago).group_by(measurement.date)\
    .order_by(measurement.date).all()
    return jsonify(dict(year_scores))


@app.route("/api/v1.0/stations")
def get_stations():
    sel = [station.station, station.name]
    stations = session.query(*sel).all()
    return jsonify(dict(stations))


@app.route("/api/v1.0/tobs")
def get_most_active_station_tobs():
    year_ago = get_year_ago()
    most_active = get_most_active_station()
    sel = [measurement.date, measurement.tobs]
    most_active_year_temps = session.query(*sel).filter(measurement.date >= year_ago)\
        .filter(measurement.station==most_active).order_by(measurement.date).all()
    
    return jsonify(dict(most_active_year_temps))


@app.route("/api/v1.0/<start>")
def get_tob_stats(start):
    start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
    sel = [func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)]
    result = session.query(*sel).filter(measurement.date >= start_date).all()
    result_dict = {
        "min": result[0][0],
        "max": result[0][1],
        "avg": result[0][2]
    }
    return jsonify(result_dict)


@app.route("/api/v1.0/<start>/<end>")
def get_tob_stats2(start, end):
    start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(end, "%Y-%m-%d").date()
    sel = [func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)]
    result = session.query(*sel).filter(measurement.date >= start_date)\
        .filter(measurement.date <= end_date).all()
    result_dict = {
        "min": result[0][0],
        "max": result[0][1],
        "avg": result[0][2]
    }
    return jsonify(result_dict)


if __name__ == '__main__':
    app.run(debug=True)