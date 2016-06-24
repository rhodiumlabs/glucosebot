#!/usr/bin/env python

import urllib
import json
import os
import time

import glucosemodel
from flask import Flask
from flask import request
from flask import make_response
from threading import Thread
from flask import Flask, render_template, session, request


# Flask app should start in global layout
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')

#This method is the webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

# Rewrite this method. Done for Yahoo Weather app
def processRequest(req):
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
    result = urllib.urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res

#Rewrite this
def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "glucosebot"
    }


def generateGlucose(message):
    ptype = str(message['data'][10])
    weight = int(message['data'][0])
    bhour = int(message['data'][1])
    bminute = int(message['data'][2])
    lhour = int(message['data'][3])
    lminute = int(message['data'][4])
    dhour = int(message['data'][5])
    dminute = int(message['data'][6])
    eatingtime = 30
    meal1 = float(message['data'][7])*1801.8/eatingtime
    meal2 = float(message['data'][8])*1801.8/eatingtime
    meal3 = float(message['data'][9])*1801.8/eatingtime

    glucose = glucosemodel.model.run_model(patient_type = ptype,
                modelData = [weight,
                bhour, bminute,
                lhour, lminute,
                dhour, dminute,
                eatingtime, meal1,
                meal2, meal3,
                2000, 1, 0,   0,   0, 1,  0,   0,   0])
    return glucose

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port
    app.run(debug=False, port=port, host='0.0.0.0')
