# ArcGIS Setup

Beacon uses ArcGIS from the backend only. Do not place the ArcGIS API key in the React frontend.

## Get An API Key

1. Go to https://developers.arcgis.com/.
2. Sign in or create an Esri / ArcGIS Location Platform account.
3. Open the developer dashboard or portal content area.
4. Create API key credentials.
5. Enable the location services Beacon needs:
   - Geocoding addresses.
   - Routing and directions when route analysis moves to ArcGIS routing.
   - Basemaps if Beacon later switches map tiles to Esri.
6. Generate the API key.
7. Copy it when it is created. The full key value may only be shown at creation time.

## Configure Beacon

Set these values in the backend `.env` file:

```env
ARCGIS_GEOCODING_ENABLED=true
ARCGIS_API_KEY=your_real_key_here
ARCGIS_GEOCODE_FOR_STORAGE=true
ARCGIS_GEOCODE_MIN_SCORE=80
ARCGIS_GEOCODE_TIMEOUT_SECONDS=5
```

Restart the backend after changing `.env`.

## Security Notes

- Keep the API key on the backend only.
- Restrict key permissions to the services Beacon actually uses.
- Rotate the key if it is exposed.
- Use stronger Esri authentication before handling private or confidential ArcGIS-hosted data.
