import json

# Load the GeoJSON file
with open('output.geojson', 'r') as file:
    geojson_data = json.load(file)

# Define the list of ZIP codes of interest
zip_codes = {92014, 92037, 92064, 92065, 92101, 92102,
             92103, 92104, 92105, 92106, 92107, 92108, 92109, 
             92110, 92111, 92113, 92114, 92115, 92116, 92117, 
             92119, 92120, 92121, 92122, 92123, 92124, 92126,
             92127, 92128, 92129, 92130, 92131, 92139, 92154, 92173}

# Filter features by ZIP code and save into separate files
for zip_code in zip_codes:
    filtered_features = [feature for feature in geojson_data['features'] if feature['properties'].get('ZIP') == str(zip_code)]
    
    print(filtered_features)
    if filtered_features:
        new_geojson = {
            'type': 'FeatureCollection',
            'features': filtered_features
        }
        
        # Save the filtered GeoJSON to a file
        with open(f'/path/to/save/{zip_code}_features.geojson', 'w') as outfile:
            print("d")
            json.dump(new_geojson, outfile, indent=4)
