# Time Schedules

The `time_schedules` method parses the [UW Time Schedules](https://www.washington.edu/students/timeschd/) and returns this information in a *Pandas DataFrame* or a *Python Dictionary*. Parsing is fast, ranging from 10 to 45 seconds to parse the Time Schedules for **every** UW Campus. If a course has meeting times *to be arranged* or if any information is not given, this information is set to `None`.
<br/>
<br/>
For UW Seattle and Tacoma, Time Schedules are available beginning Winter (WIN) Quarter 2003. Autumn (AUT) Quarter 2002 is not available.
<br/>
UW Bothell's Time Schedule archive begins Autumn (AUT) 2012.

Check out the Time Schedule Archive for [Seattle](https://www.washington.edu/students/timeschd/archive/), [Tacoma](https://www.washington.edu/students/timeschd/T/archive.html) and [Bothell](https://www.uwb.edu/registration/time).
<br/>
You'll notice that for the Tacoma and Bothell archives, the links on the pages do not go back to AUT2002 and AUT2012 (for each campus). These time schedules, however, are still available.

### Import

```python
from uwtools import time_schedules

or

import uwtools.time_schedules
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`year` | `int` | | The year to get Time Schedules from.<br/>**Required**
`quarter` | `str` | | The quarter to get Time Schedules from.<br/>**Required**
`campuses` | `list` | `['Seattle', 'Bothell', 'Tacoma']` | The Campuses to get the Time Schedules from.
`struct` | `str` | `'df'` | Short for *Data Structure* and determines the return type for the Time Schedules.<br/>`'df'` -> *Pandas DataFrame*<br/>`'dict'` -> *Python Dictionary*
`include_datetime` | `bool` | `False` | Adds two columns to the DataFrame/Dict, ['Start', 'End'] which are `datetime` objects representing the start and ending times for the course. This is useful when checking if courses overlap or other analysis relating to duration of courses, etc...<br/>**WARNING**: Including the `datetime` may result in slower performance. ~10-15 seconds.
`show_progress` | `bool` | `False` | Displays a progress meter in the console if `True`, otherwise does not. 
`json_ready` | `bool` | `False` | If `struct='dict'`, and you would like to store the dict in a `.json` file, if `json_ready` is `True`, removes all the `datetime` objects to prevent `TypeErrors` when converting to JSON. 

### Returns

A *Pandas DataFrame* or *Python Dictionary* (depending on the `struct` parameter) representing the Time Schedules for all UW Campuses in the `campuses` list. 

### Storing Information in Files

Since every time this method is called, the [UW Time Schedules](https://www.washington.edu/students/timeschd/) are parsed, it is recommended that you store the data in a file for later use, to prevent parsing the time schedules more than necessary.

If you use the default `struct='df'`, you can store the information as a csv file using the following:

```python

import uwtools

# Get the time schedules from the uwtools library as a
# pandas DataFrame
time_schedule = uwtools.time_schedules(struct='df', include_datetime=True)

time_schedule.to_csv('FILE_LOCATION')

```

To read in this information again:

```python

import pandas as pd

time_schedule = pd.read_csv('FILE_LOCATION', index_col=0)
# If you had include_datetime=True, this next part is necessary to
# read in the 'Start' and 'End' columns are datetimes
time_schedule['Start'] = pd.to_datetime(time_schedule['Start'])
time_schedule['End'] = pd.to_datetime(time_schedule['End'])

```

***

If you're not familiar with the *Pandas* library, you can choose `struct='dict'`, and create a `.json` file with the Dictionary as follows:

```python

import json
import uwtools

# Get the departments from the uwtools library as a
# python Dictionary
time_schedule = uwtools.time_schedules(struct='dict', json_ready=True)

with open('FILE_LOCATION', mode='w') as f:
    # Indent and sort_keys are optional parameters, but help when looking 
    # through the .json file
    json.dump(time_schedule, f, indent=4)

```

To read in this information again:

```python

import json

with open('FILE_LOCATION', mode='r') as f:
    time_schedule = json.loads(f.read())

```

### Examples

#### DataFrame `[struct='df']`

Columns used in the DataFrame (with `datetime=True`) are (in this order):

```
['Course Name', 'Seats', 'SLN', 'Section', 'Type', 'Time', 'Start', 'End', 'Building', 'Room Number', 'Campus', 'Quarter', 'Year']
```

With `datetime=False`, the `'Start'` and `'End'` Columns are removed:

```
['Course Name', 'Seats', 'SLN', 'Section', 'Type', 'Time', 'Building', 'Room Number', 'Campus', 'Quarter', 'Year']
```

**Column Descriptions are listed at the bottom of the page.**

The call to the `time_schedules` function with the following parameters will yield the DataFrame below.

```python
time_schedules(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='df', include_datetime=True)
```

```
     Course Name Seats    SLN Section  Type       Time     Start       End Building Room Number   Campus Quarter  Year
0       TCHIN101    40  22295       A  LECT  1100-1220  11:00:00  12:20:00      WGB       WG210   Tacoma     AUT  2019
1       TEDSS511    10  22001       A  LECT   430-700P  16:30:00  19:00:00                        Tacoma     AUT  2019
2        TEST200    25  22428       A  LECT  1010-1210  10:10:00  12:10:00      JOY         207   Tacoma     AUT  2019
3       TEDSM517     5  21991       A  LECT   430-700P  16:30:00  19:00:00       CP         325   Tacoma     AUT  2019
4       TUNIV200    30  22225       A  LECT                  NaT       NaT                 None   Tacoma     AUT  2019
...          ...   ...    ...     ...   ...        ...       ...       ...      ...         ...      ...     ...   ...
9649      CSE599   140  13322       Y  LECT   530-820P  17:30:00  20:20:00      ECE         125  Seattle     AUT  2019
9650      CSE600    95  13324       A  LECT                  NaT       NaT                 None  Seattle     AUT  2019
9651      CSE601    50  13325       A  LECT                  NaT       NaT                 None  Seattle     AUT  2019
9652      CSE700    30  13326       A  LECT                  NaT       NaT                 None  Seattle     AUT  2019
9653      CSE800    60  13327       A  LECT                  NaT       NaT                 None  Seattle     AUT  2019
```

#### Dictionary `[struct='dict']`

The call to the `departments` function with the following parameters will yield the Dictionary below. The Dictionary is essentially a list of dictionaries, with each item in the list being the data for one course section as UW.

```python
departments(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='dict', json_ready=True)
```

```
[
    {
        "Building": "CP",
        "Campus": "Tacoma",
        "Course Name": "TEDSM517",
        "Quarter": "AUT",
        "Room Number": "325",
        "SLN": "21991",
        "Seats": "5",
        "Section": "A",
        "Time": "430-700P",
        "Type": "LECT",
        "Year": 2019
    },
    {
        "Building": "WGB",
        "Campus": "Tacoma",
        "Course Name": "TCHIN101",
        "Quarter": "AUT",
        "Room Number": "WG210",
        "SLN": "22295",
        "Seats": "40",
        "Section": "A",
        "Time": "1100-1220",
        "Type": "LECT",
        "Year": 2019
    },
    ...
```

### Column Descriptions

Column Name | Description 
--- | ---
**Course Name** | The name of the course. Format is Department Name followed by the 3-digit course code. Example: EE235
**Seats** | The number of seats available for the section.
**SLN** | **S**chedule **L**ine **N**umber. A unique 5-digit course code given to every course section at UW. **NOTE**: For all academic years before and including 2006-2007, some 4-digit (and some older 5-digit) SLN codes will not work.
**Section** | The Section Name of the course section. Lectures usually have a single capital letter, while Quiz, Lab and Studio sections have same the captial letter as their lecture, followed by another capital letter or number to identify them.
**Type** | LECT -> Lecture<br/>QZ -> Quiz Section<br/>LB -> Lab Section<br/>ST -> Studio Section
**Time** | The time as a string given with the course in the Time Schedule. Example: 920-1120. A **P** at the end of the **Time** string indicates PM. Example: 630-920P.
**Start** | The starting time of the course specified in **Time** as a `datetime` object.
**End** | The ending time of the course specified in **Time** as a `datetime` object.
**Building** | The building the course section is in.
**Room Number** | The room number of the room the course section is in.
**Campus** | The campus the course section is offered at.
**Quarter** | The quarter the course section is being offered.
**Year** | The year the course section is being offered.