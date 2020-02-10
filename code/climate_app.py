import os
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime

app = Flask(__name__)

db_path = os.path.join("..", "Resources", "hawaii.sqlite")
engine = create_engine(
    f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# to view all of the classes that automap found
Base.classes.keys()
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station
# creating session (link) from Python to the DB
session = Session(engine)


@app.route("/")
def home():
    return (
        "<h1>Welcome to Home Page</h1><br>"
        "Routes Available:<br><br>"
        "* List of last one year's precipitation data:"
        "<br>/api/v1.0/precipitation"
        "<br><br>* List of all stations:"
        "<br>/api/v1.0/stations"
        "<br><br>* List of dates and temperature observations from a year from the last data point:"
        "<br>/api/v1.0/tobs"
        "<br><br>* Needs start date in format YYYYMMDD. Returns the min, avg, max of temperature from the start date provided:"
        "<br>/api/v1.0/<start>"
        "<br><br>* Needs start and end date in format YYYYMMDD. Returns the min, avg, max of temperature from the start date till end date provided:"
        "<br>/api/v1.0/<start>/<end></br>"
    )

# finding the last (latest) date in the Measurement Dataset and the year ago date 
latest_date = (session.query(Measurement.date).order_by(Measurement.date.desc()).first())
date_twelve_months_ago = datetime.date(2017, 8, 23) - datetime.timedelta(days=365)


@app.route("/precipitation")
def precipitation():
    prcp_data = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date > date_twelve_months_ago)
        .group_by(Measurement.date)
        .all()
    )

    return jsonify(list(prcp_data))


@app.route("/stations")
def stations():
    total_station = session.query(Station.station, Station.name).distinct().all()
    return jsonify(list(total_station))


@app.route("/tobs")
def tobs():
    tobs_data = (
        session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.date > date_twelve_months_ago)
        .group_by(Measurement.date)
        .all()
    )
    return jsonify(tobs_data)


@app.route("/<start>")
def start(start=None):
	start = datetime.datetime.strptime(start, "%Y%m%d")
	temps_data = (
        session.query(
            Measurement.date,
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs),
        )
        .filter(Measurement.date >= start)
        .group_by(Measurement.date)
        .all()
        )
	return jsonify(temps_data)


@app.route("/<start>/<end>")
def start_end(start=None, end=None):
	start = datetime.datetime.strptime(start, "%Y%m%d")
	end = datetime.datetime.strptime(end, "%Y%m%d")
	temps_data = (
        session.query(
            Measurement.date,
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs),
        )
        .filter(Measurement.date >= start)
        .filter(Measurement.date <= end)
        .group_by(Measurement.date)
        .all()
    	)

	return jsonify(temps_data)


if __name__ == "__main__":
    app.run(debug=True)
