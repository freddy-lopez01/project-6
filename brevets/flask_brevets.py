"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""
import requests
import os
import flask
from flask import request
#from mymongo import insert_brevet, get_brevet
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations


import logging

###
# Globals
###
app = flask.Flask(__name__)
app.debug = True if "DEBUG" not in os.environ else os.environ["DEBUG"]
port_num = True if "PORT" not in os.environ else os.environ["PORT"]



###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
#two more app routes

## API callers based off o the docker_compose.yml file 

API_ADDR = os.environ["API_ADDR"]
API_PORT = os.environ["API_PORT"]
API_URL = f"http://{API_ADDR}:{API_PORT}/api"



#
# 
#
def insert_brevet(brevet_dist, brevet_start_time, control_brevets):
    #db.insert_one()
    #res = requests.get(f"{API_URL}/brevets")
    # This creates a list of dictionaries and we need the last one as pointed out in the lab explanation 
    # and we care about the last one 
    _id = requests.post(f"{API_URL}/brevets", json={"brevet_dist": brevet_dist, "brevet_start_time": brevet_start_time, 
                                                    "control_brevets": control_brevets}).json()
    return _id


def get_brevet():
    #db.find_one
    #res = requests.get(f"{API_URL}/brevets")
    b_list = requests.get(f"{API_URL}/brevets").json()

    brevet_list = b_list[-1]

    # This creates a list of dictionaries and we need the last one as pointed out in the lab explanation 
    # and we care about the last one 
    return brevet_list["brevet_dist"], brevet_list["brevet_start_time"], brevet_list["control_brevets"]



@app.route("/insert", methods=["POST"])
def insert():
    """
    /insert : inserts a to-do list into the database.

    Accepts POST requests ONLY!

    JSON interface: gets JSON, responds with JSON
    """
    #taken from todolist 
    # Read the entire request body as a JSON
    # This will fail if the request body is NOT a JSON.

    input_json = request.json
    # if successful, input_json is automatically parsed into a python dictionary!
    
    # Because input_json is a dictionary, we can do this:
    brevet_dist = input_json["brevet_dist"] # 
    brevet_start_time = input_json["brevet_start_time"] # 
    control_brevets = input_json["control_brevets"]

    brev_list = insert_brevet(brevet_dist, brevet_start_time, control_brevets)

    return flask.jsonify(result={},
                    message="Inserted!", 
                    status=1, # This is defined by you. You just read this value in your javascript.
                    mongo_id=brev_list)




@app.route("/fetch")
def fetch():
    """
    /fetch : fetches the newest to-do list from the database.

    Accepts GET requests ONLY!

    JSON interface: gets JSON, responds with JSON
    """

    #Taken from Todolist
    brevet_dist, brevet_start_time, control_brevets = get_brevet()
    return flask.jsonify(
            result={"brevet_dist": brevet_dist, "brevet_start_time": brevet_start_time, "control_dist": control_brevets}, 
            status=1,
            message="Successfully fetched brevet list!")





@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    brevet_dist_km = request.args.get('brevet_dist_km', 999, type=float)

    start_time = request.args.get("brevet_start_time", "2023-02-22T00:00", type=str)
    start_time = arrow.get(start_time, 'YYYY-MM-DDTHH:mm')
    

    app.logger.debug("km={}".format(km))
    app.logger.debug("brevet_dist={}".format(brevet_dist_km))
    app.logger.debug("start_time={}".format(start_time))

    app.logger.debug("request.args: {}".format(request.args))
    # FIXME!
    # Right now, only the current time is passed as the start time
    # and control distance is fixed to 200
    # You should get these from the webpage!
    open_time = acp_times.open_time(km, brevet_dist_km, start_time).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, brevet_dist_km, start_time).format('YYYY-MM-DDTHH:mm')
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)


#############

app.debug = os.environ["DEBUG"]
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.run(port=os.environ["PORT"], host="0.0.0.0")
