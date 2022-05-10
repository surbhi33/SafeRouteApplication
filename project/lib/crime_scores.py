import requests
import json
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors


def get_json(url):
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    route_info = json.loads(response.text)
    
    return route_info


def waypoints_and_distance(json_text):
    route_waypoints = []
    for i in range(len(json_text['routes'])):
        startpoints = []
        for point in json_text['routes'][i]['legs'][0]['steps']:
            
            start =  point['start_location']
            start_lat = start['lat']
            start_lng = start['lng']
    
            end = point['end_location']
            end_lat = end['lat']
            end_lng = end['lng']
    
            meters = point['distance']['value']
    
            startpoints.append((start_lat, start_lng, meters))
        startpoints.append((end_lat, end_lng, 0))
        route_waypoints.append(startpoints)
        
    return route_waypoints


def add_equal_spaced_points(route_list, k=1):
    all_routes_extra_points = []
    distance_list = []
    for x, route in enumerate(route_list):
        
        new_points = []
        total_distance = 0
        for i in range(len(route) - 1):
            j = i + 1
            start = route[i][:2]
            end = route[j][:2]
            meters = route[i][2]
            total_distance += meters/10
            new_lat = np.linspace(start[0], end[0], meters//k, endpoint=False)   # endpoint false so we dont double count
            new_lng = np.linspace(start[1], end[1], meters//k, endpoint=False)
            points = list(zip(new_lat, new_lng))
            new_points += points
        
        distance_list.append(total_distance)
        new_points.append(end)
        all_routes_extra_points.append(new_points)
    
    return all_routes_extra_points, distance_list


def knn_crime_score(points_list, crime_data, radius=0.000100):
    # fit knn to crime data
    lat_lng_data = crime_data[['Latitude', 'Longitude']].copy()
    neigh = NearestNeighbors(n_jobs=-1, radius=radius)
    neigh.fit(lat_lng_data)
    scores = []
    text_array = []
    for route in points_list:
        dist, indexes = neigh.radius_neighbors(route)
        # join the indexes into an array
        joined = np.concatenate(indexes)
        # get on the unique indexes
        unique_index = np.unique(joined)
        
        # take those indexes and grab the rows from the dataframe
        local_crime = crime_data.iloc[unique_index, :]

        street_crimes = local_crime.groupby(by = ['street']).\
                sum().reset_index()[['street','Crime Index']].\
                sort_values(by = 'Crime Index', ascending = False)
                
        street_crimes = street_crimes[street_crimes['Crime Index'] > 1200]
        try:
            dang_street = street_crimes.iloc[0,0]
            sec_dang_street = street_crimes.iloc[1,0]
            text_array.append(f'Please be careful while walking on {dang_street} and {sec_dang_street}')
        except:
            text_array.append('')
        crime_index_80th_percentile = local_crime['Crime Index'].quantile(0.8)
        crime_for_date = local_crime.groupby('Incident Date').agg(crime_count=('Crime Index', 'count'))
        count_80th_percentile = crime_for_date['crime_count'].quantile(0.8)
        
        crime_score = crime_index_80th_percentile * count_80th_percentile
        scores.append(round(crime_score))

    return scores,text_array


def calculate_crime_score(url):
    # read in crime data
    crime_data = pd.read_csv('../data/sf_crime_road.csv')
    crime = crime_data[['Unnamed: 0', 'Incident Date', 'Latitude', 'Longitude', 'Crime Index','street']].copy()
    
    route_json = get_json(url)    # get json data
    route_points = waypoints_and_distance(route_json)
    all_routes, distances = add_equal_spaced_points(route_points)
    crime_scores,text = knn_crime_score(all_routes, crime)
    
    return list(crime_scores),text


def generate_url_and_scores(start=None, end=None):
    api_key = os.environ['API_KEY']
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={end}&alternatives=true&mode=walking&key={api_key}"
    score = calculate_crime_score(url)
    return score




