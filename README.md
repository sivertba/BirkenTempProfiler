 **README.md**

# Temperature Profile for Birken Race

To see an example go [here](https://folk.ntnu.no/sivertba/birken/)

This Python script computes and visualizes the temperature profile for the Birken Races, such as the long-distance cross-country ski race in Norway. It combines GPX data from a chosen route and race time with weather forecast data from the Norwegian Meteorological Institute (MET Norway) to create an interactive plot showing the estimated temperature range along the course.

## Key Features

- Fetches GPX data for a specified route and race time from the Birken website.
- Retrieves weather forecast data (temperature) for each point in the GPX data using MET Norway's API.
- Shifts the GPX time data to match the user-provided start time.
- Combines GPX and weather data into a single dictionary.
- Generates a visual plot with:
    - Distance on the x-axis
    - Elevation on the secondary y-axis
    - Temperature range (low and high) on the primary y-axis
- Stores the combined data as a JSON file (fullDict.json) for potential reuse.
- Saves the plot as an interactive HTML file (temperatureProfile.html).

## Usage

1. Install required Python libraries:
   ```bash
   conda env create -f envirnoment.yml
   ```

2. Run the script from the command line, providing necessary arguments:
   ```bash
   python birkentempprofiler.py -r rennet -s "2024-03-16T08:00:00" -t 5 -f
   ```
   - Replace `rennet` with the desired race type (rennet, rittet, or løpet).
   - Adjust the start time (`-s`) and total time (`-t`) as needed.
   - Use the `-f` flag to download fresh weather data (not cached).
   - Use '-h' to see additional features.

## Output

- `fullDict.json`: Contains the combined GPX and weather data in JSON format.
- `temperatureProfile.html`: An interactive plot visualizing the temperature profile and elevation along the race course. Open this file in a web browser to view the plot.

## Additional Notes

- This script utilizes external data sources and APIs, which may have usage restrictions or rate limits.
- The accuracy of the temperature profile depends on the accuracy of the weather forecast data.
- Consider the potential time required to fetch and process data, especially for longer race times.

## For More Information

- Birken website: [https://birkebeiner.no/en/ski](https://birkebeiner.no/en/ski)
- MET Norway weather API: [https://api.met.no/](https://api.met.no/)
