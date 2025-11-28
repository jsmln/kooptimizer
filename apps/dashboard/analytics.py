# apps/dashboard/analytics.py
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
import os
from django.conf import settings

def get_analytics_data():
    """Fetches active user data from GA4 for the last 30 days."""
    try:
        # Ensure credentials path is set
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GA_KEY_FILE_PATH
        
        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{settings.GA_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        )
        response = client.run_report(request)

        # Format data for Chart.js
        labels = []
        data = []
        
        # GA4 returns dates unsorted sometimes, so sort them
        sorted_rows = sorted(response.rows, key=lambda x: x.dimension_values[0].value)

        for row in sorted_rows:
            # Convert '20231025' to 'Oct 25' for better readability
            date_str = row.dimension_values[0].value
            formatted_date = f"{date_str[4:6]}/{date_str[6:8]}" 
            labels.append(formatted_date)
            data.append(int(row.metric_values[0].value))
            
        return {"labels": labels, "data": data}

    except Exception as e:
        print(f"Analytics Error: {e}")
        return {"labels": [], "data": []} # Return empty if API fails