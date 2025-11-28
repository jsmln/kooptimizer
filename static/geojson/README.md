# GeoJSON Data for District Maps

## Overview
This folder should contain the GeoJSON file with barangay boundaries for Lipa City. The map visualization uses this data to create actual district shapes by merging barangays.

## Required File
- **File Name**: `lipa_barangays.json`
- **Location**: `static/geojson/lipa_barangays.json`
- **Format**: GeoJSON FeatureCollection

## How to Get the GeoJSON Data

### Option 1: Download from GitHub
1. Visit [faeldon/philippines-json-maps](https://github.com/faeldon/philippines-json-maps)
2. Navigate to `geojson/barangays/`
3. Find the file for **Batangas** or specifically **Lipa City**
4. Download and save as `lipa_barangays.json` in this folder

### Option 2: Use PhilGIS.org
1. Visit [philgis.org](http://philgis.org)
2. Search for Lipa City barangay boundaries
3. Export as GeoJSON
4. Save as `lipa_barangays.json` in this folder

### Option 3: Create from QGIS/ArcGIS
1. Open your GIS software (QGIS or ArcGIS)
2. Load Lipa City barangay shapefile
3. Export as GeoJSON
4. Save as `lipa_barangays.json` in this folder

## GeoJSON Structure Expected

The GeoJSON file should have a structure like:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "NAME_3": "Balintawak",
        // or "name", "NAME", "Barangay", "barangay"
        // Any property that contains the barangay name
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[longitude, latitude], ...]]
      }
    },
    // ... more barangays
  ]
}
```

## Barangay Name Property

The code tries to find the barangay name in these property fields (in order):
- `NAME_3`
- `name`
- `NAME`
- `Barangay`
- `barangay`

If your GeoJSON uses a different property name, update the code in:
- `templates/dashboard/admin_dashboard.html` (function `initializeDistrictMap`)
- `templates/dashboard/staff_dashboard.html` (function `initializeStaffDistrictMap`)

## District Mapping

The barangays are automatically mapped to districts based on this mapping:
- **North**: Balintawak, Marawoy, Dagatan, Lumbang, Talisay, Bulacnin, Pusil, Bugtong na Pulo, Inosluban, Plaridel, San Lucas
- **East**: San Francisco, San Celestino, Malitlit, Sto. Toribio, San Benito, Sto. Niño, San Isidro, Munting Pulo, Latag, Sabang, Tipacan, San Jose, Tangob, Antipolo del Norte, Antipolo del Sur, Pinagkawitan
- **West**: Halang, Duhatan, Pinagtong-ulan, Bulaklakan, Pangao, Bagong Pook, Banay-banay, Tambo, Sico, Fernando Air Base, San Salvador, Tangway, Tibig, San Carlos, Mataas na Lupa
- **South**: Adya, Lodlod, Cumba, Quezon, Sampaguita, San Sebastian, Kayumanggi, Anilao, Anilao-Labac, Pag-olingin Bata, Pag-olingin East, Pag-olingin West, Malagonlong, Bolbok, Rizal, Mabini, Calamias, San Guillermo
- **Urban**: Barangay 1, Barangay 2, Barangay 3, Barangay 4, Barangay 5, Barangay 6, Barangay 7, Barangay 8, Barangay 9, Barangay 9-A, Barangay 10, Barangay 11

## Fallback Behavior

If the GeoJSON file is not found, the map will use simplified rectangle shapes as a fallback. This allows the dashboard to work even without the GeoJSON file, but the shapes won't be accurate.

## Testing

After adding the GeoJSON file:
1. Clear your browser cache
2. Refresh the dashboard
3. Check the browser console for any errors
4. The map should display actual district shapes instead of rectangles

