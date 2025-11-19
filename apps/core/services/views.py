# myapp/views.py
from django.shortcuts import render
from django.core.cache import cache
from .services import get_ticketmaster_events

def event_list(request):
    city = request.GET.get('city', 'Philippines') # Default to NY if no city provided
    
    # 1. Check Cache First (Key format: "events_New York")
    cache_key = f"events_{city}"
    events_data = cache.get(cache_key)

    if not events_data:
        # 2. If not in cache, fetch from API
        print(f"Fetching new data for {city}...")
        events_data = get_ticketmaster_events(city=city)
        
        # 3. Save to cache for 1 hour (3600 seconds)
        # This ensures you only hit Ticketmaster once per hour per city
        cache.set(cache_key, events_data, 3600)

    context = {
        'events': events_data,
        'city': city
    }
    
    return render(request, 'myapp/events.html', context)