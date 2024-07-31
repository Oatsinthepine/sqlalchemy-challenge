# Import the dependencies.
from flask import Flask, jsonify

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from datetime import datetime, timedelta

import numpy as np

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(autoload_with = engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Static api flask route
#################################################
@app.route('/')
def home(): # when enter in home page it illistrates all available urls.
    return (
        f'Welcome, this is the home page for my vacation climate app website.<br/>'
        f'<br/>'
        f'Here is the availiable routes for more information:<br/>'
        f'Here are the static routes: <br/>'
        f'/api/v1.0/precipitation<br/>'
        f'/api/v1.0/stations<br/>'
        f'/api/v1.0/tobs<br/>'
        f'<br/>'
        f'Here is the dynamic routes: <br/>'
        f'#please enter date in this specific format: year-month-date <br/>'
        f'/api/v1.0/start_date/<start_date> <br/>' 
        f'/api/v1.0/start_date/end_date/<start_date>/<end_date> <br/>' 
    )
            
 #Here is the precipitation route.           
@app.route('/api/v1.0/precipitation')
def precipitate():
    '''When user enter this url, this fucntion return the output of precipitation'''
    date = datetime(2017,8,23).date() - timedelta(days = 365)
    precip = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= date).all()
    session.close()

    print("User now seeing last year's precipitation data.")
    # Convert the query results to a list of dictionaries
    precip_data = []
    for result in precip:
        precip_dict = {} #using loop to assign each date as key and prcp as value paired.
        precip_dict["date"] = result.date # access each attribute
        precip_dict["prcp"] = result.prcp
        precip_data.append(precip_dict) 
    
    return jsonify(precip_data)

#Here is the station route.
@app.route('/api/v1.0/stations')
def stations():
    session = Session(engine)
    '''Returns jsonified data for all the stations in the hawaii database.'''
    result = session.query(Station.station).all()
    session.close()
    print('Users now seeing all the stations data.')
    flattened = list(np.ravel(result)) # convert the retreved data into a unidimension list.

    return jsonify(flattened)

#Here is the temperature route.
@app.route('/api/v1.0/tobs')
def tobs():
    '''Returns the most active station data which is USC00519281'''
    session = Session(engine)
    time = datetime(2017,8,23).date() - timedelta(days=365)
    data = session.query(Measurement.tobs).filter(Measurement.station == 'USC00519281', Measurement.date >= time).all()
    session.close()
    flat = list(np.ravel(data))
    print('User now seeing the most active station data.')
    return jsonify(flat)


#################################################
# Dynamic api flask route
#################################################
@app.route('/api/v1.0/start_date/<start_date>')
def data_to_start_date(start_date):
    upto_now = datetime(2017,8,23).date() #covert to datetime form.
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date() #converts a string representation of a date into a datetime object for later calculation
    except ValueError:
        return jsonify({"error" : "Wrong datetime format, should be YYYY-MM-DD."}), 404
    
    # this aggregate func will result in a list contain a tuple, look like this [(min, max, avg)]
    agg_func_lst = [func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)]

    time_interval = upto_now - start_date
    session = Session(engine)
    data_result = session.query(*agg_func_lst).filter(Measurement.date >= time_interval).all()

    session.close()
    print(f'User now see the data from {start_date} to 2017-8-23.')
    #unidemonsionalised = list(np.ravel(data_result))
    if data_result:
        # this data_result[0] will get the one and only tuple inside the list, and assign min_temp, max_temp, avg_temp to
        # the corresponding value inside the tup.
        min_temp, max_temp, avg_temp = data_result[0] 
        #make dictionary and asssign key/value pairs:
        result_dic = {
            'Min_temp':min_temp,
            'Max_temp':max_temp,
            'Avg_temp':avg_temp        
        }
        #jsonify the result on web
        return jsonify(result_dic)
    else: #give error message if no data.
        return jsonify({'error':'No data can be found from your query.'}), 404


@app.route('/api/v1.0/start_date/end_date/<start_date>/<end_date>')
def data_result_2(start_date, end_date):
    # Define the date boundaries based on what is in the database.
    earliest_date = datetime(2010, 1, 1).date()
    latest_date = datetime(2017, 8, 23).date()
    try:
        begin_date = datetime.strptime(start_date,"%Y-%m-%d").date()
        end_date = datetime.strptime(end_date,"%Y-%m-%d").date()
    except ValueError: #check if input is in correct format else give error.
        return jsonify({"error" : "Wrong datetime format, should be YYYY-MM-DD."}), 404
    #when user enter the date that either is out of boundaries it will return error.
    if begin_date < earliest_date or end_date > latest_date:
        return jsonify({"error": f"Dates must be between {earliest_date} and {latest_date}."}), 404
    
    session = Session(engine)
    agg_func_lst_2 = [func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)]
    #here use build-in & operator to apply condition checking.
    result = session.query(*agg_func_lst_2).filter((Measurement.date >= begin_date) & (Measurement.date <= end_date)).all()

    session.close()
    #console logging message.
    print(f"User now see the data from {start_date} to {end_date}.")

    if result: #if it gets something
        min_t, max_t, avg_t = result[0]
        result_dict = {
            'Min_temp':min_t,
            'Max_temp':max_t,
            'Avg_t':avg_t
        }
        return jsonify(result_dict)
    else: #give error message if no data.
        return jsonify({'error':'No data can be found from your query.'}), 404


#################################################
# Flask Routes
#################################################
if __name__ == '__main__':
    app.run(debug=True)

