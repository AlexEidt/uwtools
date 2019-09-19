# Get Quarter Ranges

The `get_quarter_ranges` method returns information about the date ranges of quarters at the UW.

### Import

```python
from uwtools import get_quarter_ranges

or

import uwtools.get_quarter_ranges
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`year` | `str` | `None` | The academic year to get quarter date ranges from.<br/>Example: 2019-2020 -> `'1920'`.<br/>Academic years starting from 2014-2015 (`'1415'`) are supported. If `year=None`, then the quarter ranges from the current academic year will be returned. 

### Returns

A *Python Dictionary* with Quarter Abbreviation keys mapping to list of `datetime` objects representing the range of dates for that quarter.

Example for the `1920` Academic Year at UW:

```python

get_quarter_ranges(year='1920')

{'AUT': [
    datetime.date(2019, 9, 25), 
    datetime.date(2019, 12, 6)
    ], 
 'WIN': [
    datetime.date(2020, 1, 6), 
    datetime.date(2020, 3, 13)
    ]
  ...
```

### Storing Information in Files

`datetime` objects are not JSON Serializable, therefore creating a `.json` file to store this information is not possible. The best way to store the data returned from `get_quarter_ranges` is in a variable to access later on.