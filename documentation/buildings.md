# Buildings

The `buildings` method returns information about all buildings at each Campus at UW. 

### Import

```python
from uwtools import buildings

or

import uwtools.buildings
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`campuses` | `list` | `['Seattle', 'Bothell', 'Tacoma']` | The Campuses to get buildings from.


### Returns

A *Python Dictionary* representing the buildings for all UW Campuses in the `campuses` list. Buildings are not separated by campus. To get all buildings from a certain campus, pass that campus into the `campuses` parameters.

### Storing Information in Files

```python

import json
import uwtools

# Get the buildings from the uwtools library as a
# python Dictionary
buildings = uwtools.buildings(struct='dict')

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
    "ACC": "John M. Wallace Hall (formerly Academic Computing Center)",
    "ADMC": "Academic Building",
    "AER": "Aerospace & Engineering Research Building",
    "ALB": "Allen Library",
    "ALD": "Alder Hall",
    "AND": "Anderson Hall",
    "ARC": "Architecture Hall",
    "ART": "Art Building",
    "ATG": "Atmos Sci/Geophysics",
    "BAG": "Bagley Hall",
    "BB": "Birmingham Block",
    "BGH": "Botany Greenhouse",
    "BHS": "Birmingham Hay & Seed",
    "BIOE": "W.H. Foege Bioengineering Building",
    "BLD": "Bloedel Hall",
    "BMM": "Burke Memorial Museum",
    "BNS": "Benson Hall",
    ...
```