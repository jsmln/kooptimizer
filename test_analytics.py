from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
import os
import json
import urllib.parse
import webbrowser  # This opens your browser automatically

# --- CONFIGURATION ---
KEY_FILE_PATH = 'cred.json' 
PROPERTY_ID = 514533439 # Make sure this is correct!

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = KEY_FILE_PATH

def run_visual_test():
    client = BetaAnalyticsDataClient()
    print("Querying Google Analytics data...")

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="city")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    )

    response = client.run_report(request)

    # 1. Extract Data for the Chart
    cities = []
    counts = []

    print("--- Data Received ---")
    if not response.rows:
        print("No data found yet (Visit your website to generate data!)")
        # We will use fake data just so you can see the chart working
        cities = ["No Data", "Yet"]
        counts = [0, 0]
    else:
        for row in response.rows:
            city = row.dimension_values[0].value
            user_count = row.metric_values[0].value
            print(f"{city}: {user_count}")
            cities.append(city)
            counts.append(int(user_count))

    # 2. Create the Chart Configuration (QuickChart)
    chart_config = {
        "type": "bar",
        "data": {
            "labels": cities,
            "datasets": [{
                "label": "Active Users",
                "data": counts,
                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                "borderColor": "blue",
                "borderWidth": 1
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": "User Traffic by City"
            }
        }
    }

    # 3. Generate the Link
    # We convert the config to a URL string
    base_url = "https://quickchart.io/chart?c="
    chart_url = base_url + urllib.parse.quote(json.dumps(chart_config))

    print("\n--- Chart Generated! ---")
    print("Opening chart in your browser...")
    webbrowser.open(chart_url)

if __name__ == '__main__':
    run_visual_test()