# uwtools

<p align="center">
    <img src="uwtoolslogo.png" alt="UW Tools Logo" width=500>
</p>

The *uwtools* library is inspired by the <a href="https://github.com/pandas-dev/pandas">*Pandas*</a> library, incorporating similar styles in parameter declaration and ease of use.
<br/>
Some features of the library include:

* Easily get quarter date ranges and current/upcoming quarters at UW.
* Easy parsing of the current [Time Schedules](https://www.washington.edu/students/timeschd/) and [Course Catalogs](http://www.washington.edu/students/crscat/) for every UW Campus.
* Times for course sections in Time Schedules converted to `datetime` objects.
* Complete list of buildings with abbreviations, full names and coordinates.
* Data stored and returned in `pandas` DataFrames and `Python` dictionaries for easy searching/manipulation.
* Time Schedule Data is available for courses beginning `WIN 2003`. 

## Installation

```
pip install uwtools
```

***

## <a href="https://github.com/AlexEidt/uwtools/wiki">Documentation</a>

Method | Description
--- | ---
<a href='https://github.com/AlexEidt/uwtools/wiki/Course-Catalogs'>course_catalogs</a> | Parse the UW Course Catalogs
<a href='https://github.com/AlexEidt/uwtools/wiki/Departments'>departments</a> | Get information about UW Departments
<a href='https://github.com/AlexEidt/uwtools/wiki/Academic-Year'>academic_year</a> | Find the academic school year
<a href='https://github.com/AlexEidt/uwtools/wiki/Time-Schedules'>time_schedules</a> | Parse the UW Time Schedules from Winter 2003 - Present for UW Campuses
<a href='https://github.com/AlexEidt/uwtools/wiki/Buildings'>buildings</a> | Get a list of buildings at each UW Campus with full names included
<a href='https://github.com/AlexEidt/uwtools/wiki/Geocode'>geocode</a> | Find coordinates for buildings at each UW Campus

## Dependencies

* <a href="https://2.python-requests.org/en/master/">Requests</a>
* <a href="https://www.crummy.com/software/BeautifulSoup/">BeautifulSoup</a>
* <a href="https://pandas.pydata.org/">Pandas</a>
* <a href="https://github.com/tqdm/tqdm">tqdm</a>