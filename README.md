# uwtools

Making data extraction for courses from the University of Washington simple.

## Contents

* <a href='#course_catalogs'>course_catalogs</a>
* <a href='#departments'>departments</a>
* <a href='#get_quarter_ranges'>get_quarter_ranges</a>
* <a href='#get_quarter'>get_quarter</a>
* <a href='#time_schedules'>time_schedules</a>
* <a href='#buildings'>buildings</a>
* <a href='#geocode'>geocode</a>
* <a href='#check_campus'>check_campus</a>

## Documentation

### Methods

#### `course_catalogs`

Gathers the Course Catalogs for the given UW Campuses.

<div id='course_catalogs'>
</div>

```python
course_catalogs(campuses=['Seattle', 'Bothell', 'Tacoma'], update=False)
```

#### Args

* *campuses*: `list`, default `['Seattle', 'Bothell', 'Tacoma']`
> The list of campuses to get course catalogs from.
* *update*: `bool`, default `False`
> Whether to parse the UW Course Catalog websites for each campus or to use the stored course catalogs (Updated AUT 2019). If *update=True* the parsing will take between 15-45 seconds, and may flucuate depending on internet connection.

#### Returns

* A `pandas` DataFrame representing the course catalogs for the given campus. An example for `course_catalogs(campuses=['Seattle'])` is shown below.
* If *update=True* a tuple containing the `pandas` DataFrame mentioned above as the first item and an updated departments dictionary as the second argument. Course sections with `to be arranged` meeting times are listed as `NaN` in the `Type`, `Days`, `Time`, `Building`, and `Room Number` columns.
* The columns of the DataFrame are (in this order):

```python
['Campus', 'Department Name', 'Course Number', 'Course Name', 'Credits', 'Areas of Knowledge', 'Quarters Offered','Offered with', 'Prerequisites', 'Co-Requisites', 'Description']
```

```
            Campus Department Name Course Number  ... Prerequisites Co-Requisites                                        Description       
Course_ID                                         ...
AFRAM101   Seattle           AFRAM           101  ...                              History, culture, religion, institutions, poli...       
AFRAM150   Seattle           AFRAM           150  ...                              Introductory survey of topics and problems in ...       
AFRAM214   Seattle           AFRAM           214  ...                              Introduction to various genres of African Amer...       
AFRAM220   Seattle           AFRAM           220  ...                              Examines the history and theory of African Ame...       
AFRAM246   Seattle           AFRAM           246  ...                              Survey of African Americans within the U.S. so...       
...            ...             ...           ...  ...           ...           ...                                                ...       
HONORS398  Seattle          HONORS           398  ...                              Special courses drawn from interdisciplinary g...       
HONORS496  Seattle          HONORS           496  ...                              Allows students completing the Interdisciplina...       
HONORS499  Seattle          HONORS           499  ...                              Faculty supervised Honors independent study or...       
LEAD298    Seattle            LEAD           298  ...                              Varied topics related to leadership studies ta...       
LEAD495    Seattle            LEAD           495  ...                              Guides the creation of a leadership e-portfoli...    
```

Column Name | Description 
:--- | ---
**Campus** | The campus the course is offered at.
**Department Name** | The name of the department the course is a part of. Denoted by a series of capital letters with no spaces.
**Course Number** | The 3 digit number identifying the course.
**Course Name** | The name of the course.
**Credits** | The number of credits offered for the course. Some courses have variable credits offered/different credit options. Check out the UW's guide for the credit system [here](http://www.washington.edu/students/crscat/glossary.html).
**Areas of Knowledge** | Areas of Knowledge essentially are credit types. [More Information](https://www.washington.edu/uaa/advising/degree-overview/general-education/).
**Quarters Offered** | The quarters of the year the course is offered. **A**utumn, **W**inter, **Sp**ring, **S**ummer.
**Offered with** | At times, a course may be offered alongside a similar course in a different department. 
**Prerequisites** | Courses that must be taken in order to take the course. 
**Co-Requisites** | Courses that must be taken at the same time the desired course is being taken.
**Description** | The description of the course objectives.

Prerequisites and Co-Requisites are separated by the following symbols: `&&`, `;`, `,`, and `/`. These symbols show the and/or relationships between requisite courses. All course separated by a `;` indicate that any one of those courses is enough to statisfy the requirement. Courses separated by a `,` indicate that any course in the list of comma separated values between semi-colons is enough to satisfy the requirement. The `&&` and `/` symbols are used to group courses, with `&&` meaning *and* and `/` meaning *or*.

Examples:

**BIOL423**: 
Prerequisite: *either BIOL 180 and BIOL 356, or BIOL 180 and FISH 250, or a minimum grade of 3.4 in BIOL 180 or BIOL 240.*
 
Prerequisites after parsing: 
*BIOL180&&BIOL356,BIOL180&&FISH250,BIOL180,BIOL240*

**EE235**:
Prerequisite: *either MATH 136, MATH 307, or AMATH 351, any of which may be taken concurrently; PHYS 122; either CSE 142 or CSE 143, either of which may be taken concurrently.*

Prerequisites after parsing:
*MATH136,MATH307,AMATH351;PHYS122;CSE142,CSE143*

***

#### `departments`

Returns the departments at UW for each campus.

<div id='departments'>
</div>

```python
departments(campuses=['Seattle', 'Tacoma', 'Bothell'])
```

#### Args

* *campuses*: `list`, default `['Seattle', 'Bothell', 'Tacoma']`
> The list of campuses to get departments from. An example would be `EE -> Electrical Engineering` at UW Seattle.

#### Returns

* A dictionary with department name abbreviations to full names. An example for `departments(campuses=['Seattle'])` is shown below.

```
{
    "Seattle": {
        "AA": "Aeronautics and Astronautics",
        "AAS": "Asian-American Studies",
        "ACCTG": "Accounting",
        "ADMIN": "Administration",
        "AE": "Aerospace Engineering",
        "AES": "American Ethnic Studies",
        "AFRAM": "Afro-American Studies",
        "AIS": "American Indian Studies",
        "AMATH": "Applied Mathematics",
        ...
```

***

#### `get_quarter_ranges`

Parses UW's Academic Calendar to find date ranges for every quarter in the current academic year.

<div id='get_quarter_ranges'>
</div>

```python
get_quarter_ranges(year=None)
```

#### Args

* *year*: `int`, default `None`
>  The academic year to get quarter date ranges from. Example: `2019-2020 -> 1920` would correspond to the call `get_quarter_ranges(year=2019)`. Academic years starting from `2014-2015 (1415)` are supported.

#### Returns

* Dictionary with Quarter Abbreviation keys mapping to list of datetime objects representing the range of dates for that quarter at UW.

```
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

***

#### `get_quarter`

Calculates the current quarter at UW based on the current date. If the current date falls on a quarter break, such as Summer break, the current quarter will be Summer (SUM) and the upcoming quarter will be Autumn (AUT).

<div id='get_quarter'>
</div>

```python
get_quarter(filter_=False, type_='current')
```

#### Args

* *filter_*: `bool`, default *False*
> Filters out the A and B terms of Summer Quarter if `True` otherwise does not.
* *type_*: `str`, default `'current'`
> `'current'`: Get the current quarter at UW. `'upcoming'`: Get the upcoming quarter at UW.
> Quarters: `AUT -> Autumn`
> `WIN -> Winter`
> `SPR -> Spring`
> `SUM -> Summer`
> `SUMA -> Summer A Term`
> `SUMB -> Summer B Term`

#### Returns

* String representing the current quarter(s). NOTE: Summer Quarter has two terms, A and B.

***

#### `time_schedules`

Gathers the Time Schedules for the given UW Campuses, Quarter and Year.

<div id='time_schedules'>
</div>

```python
time_schedules(campuses=['Seattle', 'Bothell', 'Tacoma'], year=None, quarter=None)
```

#### Args

* *campuses*: `list`, default `['Seattle', 'Bothell', 'Tacoma']`
> The list of campuses to get time schedules from. 
* *year*: `int`, default `None`
> The year to get Time Schedules from. If a year is given with no quarter, then every quarter from the academic year *beginning* with the given `year` arg will be returned. Example: `year = 2017 -> AUT2017, WIN2018, SPR2018, SUM2018`. Years 2003 - Present are supported. If the year is not in this range, an `AssertionError` is raised.
* *quarter* `str`, default `None`
> The specific quarter from which to get time schedules. If a quarter is given with no year, `None` is returned.

If `year` and `quarter` are `None`, then all time schedules from 2003 - 2019 for every campus in `campuses` will be shown. This may take a bit to load in.

#### Returns

* A `pandas` DataFrame containing all time schedule data for the given `campuses`, `year` and `quarter`. 
* Time schedules from 2003 - 2019 are archived in files for quicker access. Any time schedules beyond these years will be parsed from UW's Time Schedule website for the given campuses if they are available. Otherwise, `None` will be returned. 

```
       Course Name Seats    SLN Section  Type Days      Time Building Room Number   Campus Quarter  Year
252721   ARCTIC401    30  10467       A  LECT  TTh  930-1120      CMU         228  Seattle     SPR  2017
252722   ARCTIC498    30  10468       A  LECT                                      Seattle     SPR  2017
252723   HONORS212    30  14933       A  LECT  TTh   130-320      SMI         102  Seattle     SPR  2017
252724   HONORS212    25  14934       B  LECT   MW  1230-220      DEN         259  Seattle     SPR  2017
252725   HONORS212    12  14935      BA    QZ    F  1230-120      THO         331  Seattle     SPR  2017
...            ...   ...    ...     ...   ...  ...       ...      ...         ...      ...     ...   ...
262015     SOCW598    15  19338       G  LECT    W  600-850P      SWS         026  Seattle     SPR  2017
262016     SOCW598    25  19339       H  LECT   Th  830-1120      SWS         038  Seattle     SPR  2017
262017     SOCW599    35  19358       A                                            Seattle     SPR  2017
262018     SOCW600    10  19359       A                                            Seattle     SPR  2017
262019     SOCW700     5  19360       A                                            Seattle     SPR  2017
```

***

#### `buildings`

Buildings at each UW Campus.

<div id='buildings'>
</div>

```python
buidlings(campuses=['Seattle', 'Bothell', 'Tacoma'], update=False)
```

#### Args

* *campuses*: `list`, default `['Seattle', 'Bothell', 'Tacoma']`
> The list of campuses to get buidlings from.
* *update*: `bool`, default `False`
> If `True`, update the buildings by scraping the buildings website at UW. If `False`, read in the stored values. This should hardly ever be necessary as new buildings do not appear frequently.

#### Returns

* A dictionary with building name abbreviations to full names. An example for `buildings(campuses=['Seattle']), update=False` is shown below.

```
"Seattle": {
        "ACC": "John M. Wallace Hall (formerly Academic Computing Center)",
        "AER": "Aerospace & Engineering Research Building",
        "ALB": "Allen Library",
        "ALD": "Alder Hall"
        ...
```

***

#### `geocode`

Geocodes UW Buildings.

<div id='geocode'>
</div>

```python
geocode(buildings=[], campuses=['Seattle', 'Bothell', 'Tacoma'])
```

#### Args

* *buildings*: `list`, default `[]`
> The list of buildings to geocode (get coordinates for)
* *campuses*: `list`, default `['Seattle', 'Bothell', 'Tacoma']`
> The list of campuses that contain the buildings in `buildings`

#### Returns

* A dictionary with coordinate and full name information for each building. An example for `geocode(buildings=[], campuses=['Seattle'])` is shown below.

```
{
    "ACC": {
        "Latitude": "47.653063",
        "Longitude": "-122.314812",
        "Name": "John M. Wallace Hall (formerly Academic Computing Center)"
    },
    "AER": {
        "Latitude": "47.653938",
        "Longitude": "-122.305687",
        "Name": "Aerospace & Engineering Research Building"
    },
    ...
```

***

#### `check_campus`

Checks which campus a building is on.

<div id='check_campus'>
</div>

```python
check_campus(building)
```

#### Args

* *building*: `str`
> The building to check

#### Returns

* `None` if the building is in none of the UW Campuses. Otherwise, returns the campus the building is on as a String. Either `Seattle`, `Bothell`, or `Tacoma`.


