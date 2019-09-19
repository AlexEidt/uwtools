# Geocode

The `geocode` method returns information about all buildings coordinates at each Campus at UW. 
<br/>
Currently, information is sourced from a compressed file in the package, as this is much faster than using a geocoder to find coordinates for the hundreds of buildings across all UW Campuses. New buildings do not appear frequently, and the buildings will be updated as buildings are added at UW.

### Import

```python
from uwtools import geocode
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`campuses` | `list` | `['Seattle', 'Bothell', 'Tacoma']` | The Campuses to get building coordinates from.
`buildings` | `list` | `[]` | The list of buildings to geocode. If empty, all buildings are returned.


### Returns

A *Python Dictionary* representing the building coordinates for all UW Campuses in the `campuses` list. Buildings are not separated by campus. To get all buildings from a certain campus, pass that campus into the `campuses` parameters.

### Storing Information in Files

```python

import json
import uwtools

# Get the departments from the uwtools library as a
# python Dictionary
buildings = uwtools.geocode(struct='dict')

with open('FILE_LOCATION', mode='w') as f:
    # Indent and sort_keys are optional parameters, but help when looking 
    # through the .json file
    json.dump(buildings, f, indent=4, sort_keys=True)

```

To read in this information again:

```python

import json

with open('FILE_LOCATION', mode='r') as f:
    buildings = json.loads(f.read())

```

### Dictionary

```
{
    "ACC": {
        "Latitude": "47.653063",
        "Longitude": "-122.314812",
        "Name": "John M. Wallace Hall (formerly Academic Computing Center)"
    },
    "ADMC": {
        "Latitude": "47.244563",
        "Longitude": "-122.437563",
        "Name": "Academic Building"
    },
    "AER": {
        "Latitude": "47.653938",
        "Longitude": "-122.305687",
        "Name": "Aerospace & Engineering Research Building"
    },
    ...
```