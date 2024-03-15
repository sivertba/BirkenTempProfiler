import argparse
import datetime
import requests
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def checkArgs(args: argparse.Namespace) -> argparse.Namespace:
    """
    Validates and processes the arguments needed to compute the profile.

    Args:
        args (argparse.Namespace): The command line arguments.

    Returns:
        argparse.Namespace: The processed command line arguments.

    Raises:
        SystemExit: If the input for total time, start time, or race is invalid.
    """


    if args.minutes is not None and args.hours is not None:
        args.total_time = args.minutes * 60 + args.hours * 3600
    elif args.hours is None:
        args.total_time = args.minutes * 60
    elif args.minutes is None:
        args.total_time = args.hours * 3600
    else:
        print("Invalid input for total time")
        print(f"Minutes: {args.minutes}, Hours: {args.hours}")
        exit(1)

    # Check if the start time is given in ISO format
    try:
        args.datetime_start = datetime.datetime.fromisoformat(args.start)
    except:
        print("Invalid input for start time")
        print(f"Start time: {args.start}")
        exit(1)

    # Check if race is given as a valid input
    if args.race not in ['rennet', 'rittet', 'løpet']:
        print("Invalid race input. Use either 'rennet', 'rittet', or 'løpet'")
        exit(1)

    if args.gpx is not None:
        if not os.path.exists(args.gpx):
            print(f"Invalid path to GPX file: {args.gpx}")
            exit(1)

    return args

def getArgumnets():
    parser = argparse.ArgumentParser(description='Collect user input to compute the temperature profile of the Birken Race')
    parser.add_argument('-r', '--race', type=str, help="Which race, Either 'rennet', 'rittet', or 'løpet'", default='rennet')
    parser.add_argument('-s','--start', type=str, help="The start time in ISO format Norwegian Time", default=datetime.datetime.now().isoformat())

    parser.add_argument('-m', '--minutes', type=int, help="The total time in minutes")
    parser.add_argument('-t','--hours', type=int, help="The total time in hours", default=4)
    parser.add_argument('-f', '--fresh', action='store_true', help="Download all MET data fresh")    

    parser.add_argument('-g', '--gpx', type=str, help="The path to the local GPX file to use")

    parser.add_argument('-d', '--debug', action='store_true', help="Debug mode")


    args = checkArgs(parser.parse_args())

    return args


def getGPXData(race: str, total_time: int, gpxPath) -> str:
    """
    Fetches the GPX data for the selected race and total time.
    From tracker.birkebeiner.no

    Args:
        race (str): the type of race, either 'rennet', 'rittet', or 'løpet'
        total_time (int): the total time in seconds
        gpxPath (str): the path to the local GPX file to use
    Returns:
        str: The GPX data for the selected as a string
    """
    if gpxPath is not None:
        with open(gpxPath, 'r') as f:
            return f.read()

    urlRequstStr = f'http://tracker.birkebeiner.no/splitLive/dumpRoute.php?project={race}&sluttid={total_time}&fileFormat=gpx'

    gpxData = None
    fname = f"{race}_{total_time}.gpx"
    folderPath = "gpxFiles"
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    fname = os.path.join(folderPath, fname)

    if os.path.exists(fname):
        with open(fname, 'r') as f:
            gpxData = f.read()
        return gpxData

    try:
        # Fetch the GPX data
        response = requests.get(urlRequstStr)
        response.raise_for_status()
        gpxData = response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch GPX data using the URL: {urlRequstStr}")
        print(f"Error: {e}")
    
    # file name with race and time
    with open(fname, 'w') as f:
        f.write(gpxData)
 
    return gpxData

def accessChildElements(root):
    """
    Recursively access child elements and attributes until no new children.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML tree.
    """
    for child in root:
        print(child.tag, child.attrib)  # Access tag and attributes
        for subchild in child:
            print(subchild.tag, subchild.text)  # Access text data
            accessChildElements(subchild)

def gpx2dict(gpxData: str) -> dict:
    """
    Converts the GPX data to a dictionary.

    Args:
        gpxData (str): The GPX data as a string

    Returns:
        dict: The GPX data as a dictionary
    """
    # Parse the GPX data as an XML tree
    tree = ET.ElementTree(ET.fromstring(gpxData))

    # Get the root element
    root = tree.getroot()
    
    # accessChildElements(root) # Debug function to access all elements and attributes

    # Get the ele elements
    ele = []
    for child in root:
        if 'trk' in child.tag:
            for subchild in child:
                if 'trkseg' in subchild.tag:
                    for subsubchild in subchild:
                        if 'trkpt' in subsubchild.tag:
                            for subsubsubchild in subsubchild:
                                if 'ele' in subsubsubchild.tag:
                                    ele.append(float(subsubsubchild.text))
     
     # Get the time elements
    time = []
    for child in root:
        if 'trk' in child.tag:
            for subchild in child:
                if 'trkseg' in subchild.tag:
                    for subsubchild in subchild:
                        if 'trkpt' in subsubchild.tag:
                            for subsubsubchild in subsubchild:
                                if 'time' in subsubsubchild.tag:
                                    # NOTE: Datetime object is not supported in JSON
                                    # time.append(datetime.datetime.fromisoformat(subsubsubchild.text).astimezone())
                                    time.append(subsubsubchild.text)

    # Get the latitude and longitude elements
    lat = []
    lon = []
    for child in root:
        if 'trk' in child.tag:
            for subchild in child:
                if 'trkseg' in subchild.tag:
                    for subsubchild in subchild:
                        if 'trkpt' in subsubchild.tag:
                            lat.append(float(subsubchild.attrib['lat']))
                            lon.append(float(subsubchild.attrib['lon']))

    # Compute the distance in km from latitude and longitude using geodesic
    distance = [0]
    for i in range(1, len(lat)):
        distance.append(distance[-1] + geodesic((lat[i-1], lon[i-1]), (lat[i], lon[i])).kilometers)

    # Create a dictionary
    gpxDict = {
        'ele': ele,
        'time': time,
        'lat': lat,
        'lon': lon,
        'distance': distance,
    }
    return gpxDict

def shiftTimeGPX(gpxDict: dict, startTime: datetime) -> dict:
    """
    Shifts the time in the GPX data to the start time.

    Args:
        gpxDict (dict): The GPX data as a dictionary.
        startTime (datetime): The start time.

    Returns:
        dict: The GPX data with the time shifted to the start time.
    """

    # Check if the start time is a datetime object
    if not type(startTime) == datetime.datetime:
        startTime = datetime.datetime.fromisoformat(startTime)
    
    # Convert from CET to UTC
    startTime = startTime.astimezone(datetime.timezone.utc)

    # Convert the time to datetime objects
    time = [datetime.datetime.fromisoformat(t) for t in gpxDict['time']]

    # Shift the time to the start time
    time = [startTime + (t - time[0]) for t in time]

    # Convert the time back to strings
    time = [t.isoformat() for t in time]

    gpxDict['time'] = time

    return gpxDict

def _METurlRequstFunction(lat,lon,alt):
    import time
    urlRequstStr = f'https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={lat}&lon={lon}&altitude={int(alt)}'
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    
    max_retries = 5
    for i in range(max_retries):
        try:
            r = requests.get(urlRequstStr.strip(), headers=headers, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            time.sleep(5*(i+1))
    
    print(f"Failed to fetch MET data using the URL: {urlRequstStr}")
    print(f"Error: {e}")
    return None


def _findClosestTimeIndex(time, METdata):
    """
    Finds the closest time index in the timeseries to the given time.

    Args:
        time (datetime): The time to find the closest time to.
        METdata (dict): The MET data as a dictionary.
    Returns:
        int: The index of the closest time in the timeseries.
    """

    timeseries = METdata['properties']['timeseries']
    times = [datetime.datetime.fromisoformat(t['time']) for t in timeseries]

    if not type(time) == datetime.datetime:
        time = datetime.datetime.fromisoformat(time)

    closestTime = min(times, key=lambda x: abs(x - time))

    return times.index(closestTime)


def appendMET2GPX(gpxDict: dict, fresh: bool) -> dict:
    """
    Appends the MET data to the GPX data.

    Args:
        gpxDict (dict): The GPX data as a dictionary.
        fresh (bool): Whether to download fresh MET data or not.

    Returns:
        dict: The GPX data with the MET data appended.
    """
    import os
    import pickle

    # Check if the MET data should be downloaded fresh
    if not fresh and os.path.exists('METdata.pkl'):
        with open('METdata.pkl', 'rb') as f:
            METdata = pickle.load(f)
    else:
        METdata = {}
        fresh = True

    # Get the MET data for each point in the GPX data
    temp_low = []
    temp_high = []
    humidity = []
    wind_speed = []
    cloud_area_fraction = []
    wind_from_direction = []
    for i in range(len(gpxDict['lat'])):
        METDataKey = f"{gpxDict['lat'][i]}_{gpxDict['lon'][i]}_{gpxDict['ele'][i]}".replace('.','_')
        if fresh:
            outputMET = _METurlRequstFunction(gpxDict['lat'][i],gpxDict['lon'][i],gpxDict['ele'][i])
            METdata[METDataKey] = outputMET
        else:
            outputMET = METdata[METDataKey]

        # find values for temperature closest to the time in the GPX data
        index = _findClosestTimeIndex(gpxDict['time'][i], outputMET)

        temp_high.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['air_temperature_percentile_90'])
        temp_low.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['air_temperature_percentile_10'])
        humidity.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['relative_humidity'])
        wind_speed.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['wind_speed'])
        cloud_area_fraction.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['cloud_area_fraction'])
        wind_from_direction.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['wind_from_direction'])


        # print progress
        print(f"Coordinates checked: {i}/{len(gpxDict['lat'])}", end='\r')

    gpxDict['temp_low'] = temp_low
    gpxDict['temp_high'] = temp_high
    gpxDict['humidity'] = humidity
    gpxDict['wind_speed'] = wind_speed
    gpxDict['cloud_area_fraction'] = cloud_area_fraction
    gpxDict['wind_from_direction'] = wind_from_direction

    # Save the MET data to a pickle file
    with open('METdata.pkl', 'wb') as f:
        pickle.dump(METdata, f)
        
    return gpxDict

def plotFullDict(fullDict: dict, args: argparse.Namespace):
    """
    Args:
        fullDict (dict): The full dictionary containing the GPX and MET data.
        args (argparse.Namespace): The command line arguments.
    """

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['temp_low'], mode='lines', name='Temperature Low'))
    fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['temp_high'], mode='lines', name='Temperature High'))


    fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['ele'], mode='markers+lines', name='Elevation'), secondary_y=True)

    title = f"Start Time: {args.datetime_start.isoformat()} CET, Duration: {args.total_time//3600}h {args.total_time%3600//60}m"
    
    fig.update_layout(
        title=title,
        xaxis_title="Distance (km)",
        yaxis_title="Temperature (°C)",
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="RebeccaPurple"
        )
    )

    # # Update 2nd yaxis
    # fig.update_yaxes(title_text="Elevation (m)", secondary_y=True)

    # # Add wind speed and humidity to the ele trace
    # fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['wind_speed'], mode='lines', name='Wind Speed'), secondary_y=True)
    # fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['humidity'], mode='lines', name='Humidity'), secondary_y=True)

    return fig

if __name__ == "__main__":
    args = getArgumnets()

    if not args.debug or not os.path.exists('fullDict.json'):
        gpxData = getGPXData(args.race, args.total_time, args.gpx)
        gpxDict = gpx2dict(gpxData)
        gpxDict = shiftTimeGPX(gpxDict, args.datetime_start)
        fullDict = appendMET2GPX(gpxDict, args.fresh)
    
    else:
        with open('fullDict.json', 'r') as f:
            fullDict = json.load(f)
    
    # save the full dictionary to a json file
    with open('fullDict.json', 'w') as f:
        json.dump(fullDict, f)


    fig = plotFullDict(fullDict, args)

    # Save the figure as html
    fig.write_html("temperatureProfile.html")

    print("Done!")