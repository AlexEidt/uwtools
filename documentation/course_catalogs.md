# Course Catalogs

The `course_catalogs` method allows you to quickly parse the UW Course Catalog for any/all UW Campuses. Parsing can be as quick as 5 seconds for all three campuses, but may take up to 45 seconds depending on the strength of your internet connection.

### Import

```python
from uwtools import course_catalogs

or

import uwtools.course_catalogs
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`campuses` | `list` or `dict` | `['Seattle', 'Bothell', 'Tacoma']` | The Campuses to get the course catalogs from. Can either be a `list` of campuses, or a `dict` where the keys are the campuses and values are a list of departments to parse from that campus. The dictionary parameter would resemble this: `{'Seattle': ['EE', 'MSE', 'POLS'], 'Bothell': ['BBUS']}`. You can select which campuses and departments you want to parse.
`struct` | `str` | `'df'` | Short for *Data Structure* and determines the return type for the course catalog.<br/>`'df'` -> *Pandas DataFrame*.<br/>`'dict'` -> *Python Dictionary*
`show_progress` | `bool` | `False` | Displays a progress meter in the console if `True`, otherwise does not. 

### Returns

A *Pandas DataFrame* or *Python Dictionary* (depending on the `struct` parameter) representing the course catalogs for all UW Campuses in the 'campuses' list. 

### Storing Information in Files

Since every time this method is called, the [UW Course Catalog](http://www.washington.edu/students/crscat/) is parsed, it is recommended that you store the data in a file for later use, to prevent parsing the catalog more than necessary.

If you use the default `struct='df'`, you can store the information as a csv file using the following:

```python

import uwtools

# Get the course catalogs from the uwtools library as a
# pandas DataFrame
course_catalog_df = uwtools.course_catalogs(struct='df')

course_catalog_df.to_csv('FILE_LOCATION')

```

To read in this information again:

```python

import pandas as pd

course_catalog = pd.read_csv('FILE_LOCATION')
course_catalog.set_index('Course ID', axis=1, inplace=True)
course_catalog.fillna('', inplace=True)

```

***

If you're not familiar with the *Pandas* library, you can choose `struct='dict'`, and create a `.json` file with the Dictionary as follows:

```python

import json
import uwtools

# Get the course catalogs from the uwtools library as a
# python Dictionary
course_catalog_dict = uwtools.course_catalogs(struct='dict')

with open('FILE_LOCATION', mode='w') as f:
    # Indent and sort_keys are optional parameters, but help when looking 
    # through the .json file
    json.dump(course_catalog_dict, f, indent=4, sort_keys=True)

```

To read in this information again:

```python

import json

with open('FILE_LOCATION', mode='r') as f:
    course_catalog_dict = json.loads(f.read())

```

### Examples

#### Progress Bar

Progress bar will show you how many iterations have passed, as well as iterations per second (it/s) and the elapsed time.

```python
578it [00:23, 17.15it/s]
```

#### DataFrame `[struct='df']`

Columns used in the DataFrame are (in this order):

```
['Campus', 'Department Name', 'College', 'Course Number', 'Course Name', 'Credits', 'Areas of Knowledge', 'Quarters Offered', 'Offered with', 'Prerequisites', 'Co-Requisites', 'Description']
```

**Column Descriptions are listed at the bottom of the page.**

The call to the `course_catalogs` function with the following parameters will yield the DataFrame below.

```python
course_catalogs(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='df', show_progress=False)
```

```
            Campus Department Name  ... Co-Requisites                                        Description
Course ID                           ...
TBECON220   Tacoma          TBECON  ...                Introduces microeconomic theory applied to ind...
TBECON221   Tacoma          TBECON  ...                Involves the study and analysis of the aggrega...
TBECON420   Tacoma          TBECON  ...                Applies tools of intermediate microeconomic th...
TBECON421   Tacoma          TBECON  ...                Focuses on the use of intermediate economic th...
TBECON422   Tacoma          TBECON  ...                Examines the statistical tools that are used t...
...            ...             ...  ...           ...                                                ...
ENVH598    Seattle            ENVH  ...                Supervised project work on a topic related to ...
ENVH599    Seattle            ENVH  ...                Assignment to an environmental research or ser...
ENVH600    Seattle            ENVH  ...                Prerequisite: permission of departmental advis...
ENVH700    Seattle            ENVH  ...                Prerequisite: permission of departmental advis...
ENVH800    Seattle            ENVH  ...                Prerequisite: permission of departmental advis...
```

#### Dictionary `[struct='dict']`

The Dictionary option for the Course Catalogs returns a dictionary with course names (department name followed by the 3-digit course code) as keys, and dictionaries containing all course information as values.

The call to the `course_catalogs` function with the following parameters will yield the Dictionary below.

```python
course_catalogs(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='dict', show_progress=False)
```

```
{
    "AA101": {
        "Areas of Knowledge": "NW",
        "Campus": "Seattle",
        "Co-Requisites": "",
        "College": "College of Engineering",
        "Course Name": "Air and Space Vehicles",
        "Course Number": "101",
        "Credits": "5",
        "Department Name": "AA",
        "Description": "",
        "Offered with": "",
        "Prerequisites": "",
        "Quarters Offered": ""
    },
    "AA198": {
        "Areas of Knowledge": "NW",
        "Campus": "Seattle",
        "Co-Requisites": "",
        "College": "College of Engineering",
        "Course Name": "Special Topics in Aeronautics and Astronautics",
        "Course Number": "198",
        "Credits": "1-5, max. 10",
        "Department Name": "AA",
        "Description": "Introduces the field of Aeronautics and Astronautics. Topics include aircraft flight, rocket propulsion, space travel, and contemporary space missions. May include hands-on activities. For non-majors.",
        "Offered with": "",
        "Prerequisites": "",
        "Quarters Offered": ""
    },
    ...
```

### Column Descriptions
<div id="coldesc"></div>

Column Name | Description 
--- | ---
**Campus** | The campus the course is offered at.
**Department Name** | The name of the department the course is a part of. Denoted by a series of capital letters with no spaces.
**College** | The college the department of the course is in. Example: Electrical Engineering (EE) is in the College of Engineering.
**Course Number** | The 3 digit number identifying the course.
**Course Name** | The name of the course.
**Credits** | The number of credits offered for the course. Some courses have variable credits offered/different credit options. Check out the UW's guide for the credit system [here](http://www.washington.edu/students/crscat/glossary.html).
**Areas of Knowledge** | Areas of Knowledge essentially are credit types. [More Information](https://www.washington.edu/uaa/advising/degree-overview/general-education/).
**Quarters Offered** | The quarters of the year the course is offered. **A**utumn, **W**inter, **Sp**ring, **S**ummer.
**Offered with** | At times, a course may be offered alongside a similar course in a different department. 
**Prerequisites** | Courses that must be taken in order to take the course. 
**Co-Requisites** | Courses that must be taken at the same time the desired course is being taken.
**Description** | The description of the course objectives.