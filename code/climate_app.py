import os
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify, request
import datetime
degree_sign = u"\N{DEGREE SIGN}"

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


# / - Home page - List all routes that are available.
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
        "<br><br>* Needs start date in format YYYY-MM-DD. Returns the min, avg, max of temperature from the start date provided:"
        "<br>/api/v1.0/<start>"
        "<br><br>* Needs start and end date in format YYYY-MM-DD. Returns the min, avg, max of temperature from the start date till end date provided:"
        "<br>/api/v1.0/<start>/<end></br>"
    )


# finding the last (latest) date in the Measurement Dataset and the year ago date 
latest_date = (session.query(Measurement.date).order_by(Measurement.date.desc()).first())
date_twelve_months_ago = datetime.date(2017, 8, 23) - datetime.timedelta(days=365)


# /api/v1.0/precipitation - Convert the query results to a Dictionary using `date` as the key and `prcp` as the value. Return the JSON representation of your dictionary.
@app.route("/precipitation")
def precipitation():

    prcp_data = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date > date_twelve_months_ago)
        .group_by(Measurement.date)
        .all()
    )
   
    # Create a list of dicts with `date` and `prcp` as the key and value
    prcp_list = []
    for prcp in prcp_data:
        prcp_record = {}
        prcp_record["date"] = prcp[0]
        prcp_record["prcp"] = prcp[1]
        prcp_list.append(prcp_record)

    return jsonify(prcp_list)


# /api/v1.0/stations - Return a JSON list of stations from the dataset.
@app.route("/stations")
def stations():

    stations = session.query(Station.station, Station.name).distinct().all()

    station_list = []
    for station in stations:
    	station_record = {}
    	station_record["station"] = station[0]
    	station_record["name"] = station[1]
    	station_list.append(station_record)

    return jsonify(station_list)


# /api/v1.0/tobs - query for the dates and temperature observations from a year from the last data point. Return a JSON list of Temperature Observations (tobs) for the previous year.
@app.route("/tobs")
def tobs():

    tobs_data = (
        session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.date > date_twelve_months_ago)
        .group_by(Measurement.date)
        .all()
    )

    tobs_list = []
    for tob in tobs_data:
    	tob_record = {}
    	tob_record["date"] = tob[0]
    	tob_record["tob"] = tob[1]
    	tobs_list.append(tob_record)

    return jsonify(tobs_list)


# /api/v1.0/<start> - When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
@app.route("/<start>")
def start(start=None):

	try:

		start_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()

		temps_data = (
	        session.query(
	            Measurement.date,
	            func.min(Measurement.tobs),
	            func.round(func.avg(Measurement.tobs), 2),
	            func.max(Measurement.tobs),
	        )
	        .filter(func.date(Measurement.date) >= start_date)
	        .group_by(Measurement.date)
	        .all()
	        )

		temps_list = []
		for temp in temps_data:
			temp_record = {}
			temp_record["date"] = temp[0]
			temp_record[f"min temp {degree_sign}F"] = temp[1]
			temp_record[f"avg temp {degree_sign}F"] = temp[2]
			temp_record[f"max temp {degree_sign}F"] = temp[3]
			temps_list.append(temp_record)

		return jsonify(temps_list)

	except Exception as e:
		return jsonify({"status": "failure", "error": str(e)})


# /api/v1.0/<start> and /api/v1.0/<start>/<end> - When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.
@app.route("/<start>/<end>")
def start_end(start=None, end=None):

	try:
		start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
		end = datetime.datetime.strptime(end, "%Y-%m-%d").date()

		temps_data = (
	        session.query(
	            Measurement.date,
	            func.min(Measurement.tobs),
	            func.round(func.avg(Measurement.tobs), 2),
	            func.max(Measurement.tobs),
	        )
	        .filter(Measurement.date >= start)
	        .filter(Measurement.date <= end)
	        .group_by(Measurement.date)
	        .all()
	    	)

		temps_list = []
		for temp in temps_data:
			temp_record = {}
			temp_record["date"] = temp[0]
			temp_record[f"min temp {degree_sign}F"] = temp[1]
			temp_record[f"avg temp {degree_sign}F"] = temp[2]
			temp_record[f"max temp {degree_sign}F"] = temp[3]
			temps_list.append(temp_record)

		return jsonify(temps_list)

	except Exception as e:
		return jsonify({"status": "failure", "error": str(e)})


# Alternate solution to start and end date date query. This ones works like API search string. Ex: http://127.0.0.1:5000/search_type?start=2015-10-01&end=2015-11-01 
@app.route("/search_type")
def search_type():

	request_start = request.args.get("start")
	request_end = request.args.get("end")

	try:
		base_cmd = session.query(
            Measurement.date,
            func.min(Measurement.tobs),
            func.round(func.avg(Measurement.tobs), 2),
            func.max(Measurement.tobs),
        )

		if request_start:
			start = datetime.datetime.strptime(request_start, "%Y-%m-%d").date()
			base_cmd = base_cmd.filter(Measurement.date >= start)

		if request_end:
			end = datetime.datetime.strptime(request_end, "%Y-%m-%d").date()
			base_cmd = base_cmd.filter(Measurement.date <= end)

		data = base_cmd.group_by(Measurement.date).all()

		return jsonify(data)
	
	except Exception as e:
		return jsonify({"status": "failure", "error": str(e)})



# main script
if __name__ == "__main__":
    app.run(debug=True)
