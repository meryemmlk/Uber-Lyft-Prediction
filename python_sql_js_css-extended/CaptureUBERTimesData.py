import os
import json
from shapely.geometry import Polygon
from numpy import random
from shapely.geometry import Point
import pandas as pd

# libraries for UBER API
from uber_rides.session import Session
from uber_rides.client import UberRidesClient

# libraries for take the capture date
from datetime import datetime, timedelta

# libraries for capture data each 4 min
import threading

# import geojson file about natal neighborhood
atlanta_neigh = os.path.join('geojson', 'atlanta.geojson')

# load the data and use 'UTF-8'encoding
geo_json_atlanta = json.load(open(atlanta_neigh,encoding='UTF-8'))

# return a number of points inside the polygon
def generate_random(number, polygon, neighborhood):
    list_of_points = []
    minx, miny, maxx, maxy = polygon.bounds
    counter = 0
    while counter < number:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        pnt = Point(x, y)
        if polygon.contains(pnt):
            list_of_points.append([x,y,neighborhood])
            counter += 1
    return list_of_points

number_of_points = 3
neighborhood_names=[]
points_location=[]

# search all features
for feature in geo_json_atlanta['features']:
    # get the name of neighborhood
    neighborhood = feature['properties']['Label']
    # take the coordinates (lat,log) of neighborhood
    geom = feature['geometry']['coordinates']
    # create a polygon using all coordinates
    polygon = Polygon(geom[0])
    # return number_of_points by neighborhood as a list [[log,lat],....]
    points = generate_random(number_of_points,polygon, neighborhood)
    # iterate over all points and print in the map
    for i,value in enumerate(points):
        log, lat, name = value
        # create the neighborhood names list
        neighborhood_names.append(name)
        # create the list with a points that are within a neighborhood
        points_location.append([lat,log])
        
# init a dataframe with a NeighborhoodNames and the points_location
all_data = pd.DataFrame({'NeighborhoodName': neighborhood_names, 'PointLocation': points_location})

# function that captures the time it takes for an UBER car to arrive at each point within a neighborhood
def get_UBERtimes(list_points_location):
    list_neighborhood=[]
    # list for UBER estimate time
    list_points_times=[]
    # list for the date and hour that the data are taken
    list_datetime_capture=[]
    # Configure UBER sesion
    session = Session(server_token='TZ9aAN7GMzp49djfXoMil2HJ7XxCs0Zwo8EWXd88')
    client = UberRidesClient(session)
    # for each point within list_points_location take UBER estimate time and date
    for i, value in enumerate(list_points_location):
        location = neighborhood_names[i]
        lat, lon = value 
        
        try:
            response = client.get_products(lat, lon)
            productid = response.json.get('products')[0]["product_id"]
            # get time of UBER response
            wait_time = client.get_pickup_time_estimates(lat, lon, productid)
            if wait_time.json.get('times') != []:
                list_points_times.append(wait_time.json.get('times')[0]['estimate'])
            else:
                list_points_times.append(0)
            # get date
            list_neighborhood.append(location)
            last_hour_date_time = datetime.now() - timedelta(hours = 1)
            list_datetime_capture.append(last_hour_date_time.strftime('%Y-%m-%d %H:%M:%S'))
        except: 
            print(location)
            print(lat)
            print(lon)
            print(wait_time.json.get('times'))
            pass
    return list_neighborhood, list_points_times, list_datetime_capture

ite = 0

# funtion for capture and save data each two hours
def Capture_UBER_Data ():
    # count captures number
    global ite
    # dataframes columns names
    string = "UBERTime"
    string2 = "CaptureData"
    # lists for UBER estimate time and  date of capture 
    UBERtimes = []
    datatime_capture = []
    # Joint data in one dataframe 
    global points_location
    global all_data
    # total captures number
    global ITER_NUMBER
    
    neighbors, UBERtimes, datatime_capture = get_UBERtimes(points_location)
    df3 = pd.DataFrame({"neighbors": neighbors})
    df1 = pd.DataFrame({string+str(ite): UBERtimes})
    df2 = pd.DataFrame({string2+str(ite): datatime_capture})
    all_data = pd.concat([all_data, df3, df1, df2], axis=1)
    ite+=1
    print ("Capture: # %i" %(ite))
    
    all_data.to_csv(string2+str(ite)+'.csv', encoding='latin1')

# function that repeat the process each 4 minutes for eight days
def do_every (interval, worker_func, iterations = 0):
    if iterations != 1:
        threading.Timer(interval,do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]).start()

    worker_func ()

# capture UBER estimate time for each point in each Neighborhood for eight days each four minutes
# 60/4*24*8 = 2520
ITER_NUMBER = 10
do_every (240, Capture_UBER_Data, ITER_NUMBER)