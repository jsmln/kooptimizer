# # myapp/services.py
# import requests
# import os
# from django.conf import settings

# def get_ticketmaster_events(city='Batangas', limit=20):
#     """
#     Fetches events from Ticketmaster API.
#     Returns a list of simplified event objects.
#     """
#     # Retrieve key from environment variables
#     api_key = os.getenv('TICKETMASTER_API_KEY')
    
#     if not api_key:
#         print("Error: TICKETMASTER_API_KEY is missing.")
#         return []

#     url = 'https://app.ticketmaster.com/discovery/v2/events.json'
    
#     params = {
#         'apikey': api_key,
#         'city': city,
#         'size': limit,
#         'sort': 'date,asc',
#         # 'classificationName': 'Music' # Optional: filter by Music, Sports, etc.
#     }

#     try:
#         response = requests.get(url, params=params, timeout=10)
#         response.raise_for_status() # Raises error for 404, 500, etc.
#         data = response.json()

#         # parsing the deeply nested JSON response
#         events = []
#         if '_embedded' in data and 'events' in data['_embedded']:
#             for event in data['_embedded']['events']:
#                 events.append({
#                     'name': event.get('name'),
#                     'start_date': event['dates']['start'].get('localDate'),
#                     'start_time': event['dates']['start'].get('localTime', 'TBD'),
#                     'venue': event['_embedded']['venues'][0]['name'] if '_embedded' in event else 'TBA',
#                     'image': event['images'][0]['url'] if event.get('images') else '',
#                     'url': event.get('url')
#                 })
#         return events

#     except requests.exceptions.RequestException as e:
#         # Log this error in a real app
#         print(f"API Request failed: {e}")
#         return []