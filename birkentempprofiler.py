import argparse
import datetime
import requests
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

    return args

def getArgumnets():
    parser = argparse.ArgumentParser(description='Collect user input to compute the temperature profile of the Birken Race')
    parser.add_argument('-r', '--race', type=str, help="Which race, Either 'rennet', 'rittet', or 'løpet'", default='rennet')
    parser.add_argument('-s','--start', type=str, help="The start time in ISO format Norwegian Time", default=datetime.datetime.now().isoformat())

    parser.add_argument('-m', '--minutes', type=int, help="The total time in minutes")
    parser.add_argument('-t','--hours', type=int, help="The total time in hours", default=4)

    parser.add_argument('-d', '--debug', action='store_true', help="Debug mode")

    args = checkArgs(parser.parse_args())

    return args


def getGPXData(race: str, total_time: int) -> str:
    """
    Fetches the GPX data for the selected race and total time.
    From tracker.birkebeiner.no

    Args:
        race (str): the type of race, either 'rennet', 'rittet', or 'løpet'
        total_time (int): the total time in seconds
    Returns:
        str: The GPX data for the selected as a string
    """

    urlRequstStr = f'http://tracker.birkebeiner.no/splitLive/dumpRoute.php?project={race}&sluttid={total_time}&fileFormat=gpx'

    gpxData = None
    try:
        # Fetch the GPX data
        response = requests.get(urlRequstStr)
        response.raise_for_status()
        gpxData = response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch GPX data using the URL: {urlRequstStr}")
        print(f"Error: {e}")

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
    urlRequstStr = f'https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={lat}&lon={lon}&altitude={int(alt)}'
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

    try:
        r = requests.get(urlRequstStr.strip(), headers=headers, timeout=10)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch MET data using the URL: {urlRequstStr}")
        print(f"Error: {e}")
        return None

    return r.json()

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


def appendMET2GPX(gpxDict: dict) -> dict:
    """
    Appends the MET data to the GPX data.

    Args:
        gpxDict (dict): The GPX data as a dictionary.

    Returns:
        dict: The GPX data with the MET data appended.
    """

    # Get the MET data for each point in the GPX data
    temp_low = []
    temp_high = []
    for i in range(len(gpxDict['lat'])):
        outputMET = _METurlRequstFunction(gpxDict['lat'][i],gpxDict['lon'][i],gpxDict['ele'][i])

        # find values for temperature closest to the time in the GPX data
        index = _findClosestTimeIndex(gpxDict['time'][i], outputMET)

        temp_high.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['air_temperature_percentile_90'])
        temp_low.append(outputMET['properties']['timeseries'][index]['data']['instant']['details']['air_temperature_percentile_10'])

        # print progress
        print(f"Coordinates checked: {i}/{len(gpxDict['lat'])}", end='\r')

    gpxDict['temp_low'] = temp_low
    gpxDict['temp_high'] = temp_high

    return gpxDict

def plotFullDict(fullDict: dict):
    """
    Plots the full dictionary containing the GPX and MET data.

    Args:
        fullDict (dict): The full dictionary containing the GPX and MET data.
    """

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['temp_low'], mode='lines', name='Temperature Low'))
    fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['temp_high'], mode='lines', name='Temperature High'))
    fig.add_trace(go.Scatter(x=fullDict['distance'], y=fullDict['ele'], mode='lines', name='Elevation'), secondary_y=True)

    
    fig.update_layout(
        title="Elevation Profile",
        xaxis_title="Distance (km)",
        yaxis_title="Elevation (m)",
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="RebeccaPurple"
        )
    )
    fig.show()
    return fig

if __name__ == "__main__":
    args = getArgumnets()

    if not args.debug or not os.path.exists('fullDict.json'):
        gpxData = getGPXData(args.race, args.total_time)
        gpxDict = gpx2dict(gpxData)
        gpxDict = shiftTimeGPX(gpxDict, args.datetime_start)
        fullDict = appendMET2GPX(gpxDict)
    
    else:
        with open('fullDict.json', 'r') as f:
            fullDict = json.load(f)
    
    # save the full dictionary to a json file
    with open('fullDict.json', 'w') as f:
        json.dump(fullDict, f)


    plotFullDict(fullDict)

    print("Done!")