# Departments

The `departments` method returns information about all departments at each Campus at UW. 

### Import

```python
from uwtools import departments

or

import uwtools.departments
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`campuses` | `list` | `['Seattle', 'Bothell', 'Tacoma']` | The Campuses to get the departments from.
`struct` | `str` | `'df'` | Short for *Data Structure* and determines the return type for the departments.<br/>`'df'` -> *Pandas DataFrame*<br/>`'dict'` -> *Python Dictionary*<br/>`'list'` -> *List*
`flatten` | `str` | `'default'` | If `struct='dict'`<br/>`'default'`: {Campus -> {College -> {Department Name: Department Full Name}}}<br/>`'college'`: {College -> {{Department Name: Department Full Name}}}<br/>`'department'`: {Department Name: Department Full Name}<br/>`'campus'`: {Campus -> {Department Name: Department Full Name}}<br/>`'campege'`: {Campus -> \[College\]}<br/><br/>If `struct='list'`<br/>`'college'`: List of all colleges across all campuses in `campuses`<br/>`'dep-abbrev'`: Short for Department Abbreviation. List of all department abbreviated names across all campuses in `campuses`<br/>`'dep-full'`: Short for Full Department Names. List of all department abbreviated names across all campuses in `campuses`

### Returns

A *Pandas DataFrame*, *Python Dictionary* or *List* (depending on the `struct` parameter) representing the departments for all UW Campuses in the `campuses` list. 

### Storing Information in Files

Since every time this method is called, the [List of Departments from the Course Catalog](http://www.washington.edu/students/crscat/) is parsed, it is recommended that you store the data in a file for later use, to prevent parsing the catalog more than necessary.

If you use the default `struct='df'`, you can store the information as a csv file using the following:

```python

import uwtools

# Get the departments from the uwtools library as a
# pandas DataFrame
departments = uwtools.departments(struct='df')

departments.to_csv('FILE_LOCATION')

```

To read in this information again:

```python

import pandas as pd

departments = pd.read_csv('FILE_LOCATION')
departments.set_index('Department', inplace=True)

```

***

If you're not familiar with the *Pandas* library, you can choose `struct='dict'`, and create a `.json` file with the Dictionary as follows:

```python

import json
import uwtools

# Get the departments from the uwtools library as a
# python Dictionary
departments = uwtools.departments(struct='dict')

with open('FILE_LOCATION', mode='w') as f:
    # Indent and sort_keys are optional parameters, but help when looking 
    # through the .json file
    json.dump(departments, f, indent=4, sort_keys=True)

```

To read in this information again:

```python

import json

with open('FILE_LOCATION', mode='r') as f:
    departments = json.loads(f.read())

```

### Examples

#### DataFrame `[struct='df']`

Columns used in the DataFrame are (in this order):

```
['Department', 'Department Name', 'Campus', 'College']
```

**Column Descriptions are listed at the bottom of the page.**

The call to the `departments` function with the following parameters will yield the DataFrame below.

```python
departments(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='df')
```

```
                           Department Name   Campus                       College
Department
AFRAM                Afro-American Studies  Seattle  College of Arts and Sciences
AES                American Ethnic Studies  Seattle  College of Arts and Sciences
AAS                 Asian-American Studies  Seattle  College of Arts and Sciences
CHSTU                      Chicano Studies  Seattle  College of Arts and Sciences
SWA                                Swahili  Seattle  College of Arts and Sciences
...                                    ...      ...                           ...
TCMP                    Community Planning   Tacoma                 Urban Studies
TGIS        Geographic Information Systems   Tacoma                 Urban Studies
TSUD         Sustainable Urban Development   Tacoma                 Urban Studies
TUDE                          Urban Design   Tacoma                 Urban Studies
TURB                         Urban Studies   Tacoma                 Urban Studies
```

#### Dictionary `[struct='dict']`

The call to the `departments` function with the following parameters will yield the Dictionary below.

```python
departments(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='dict', flatten='default')
```

```
{
    "Bothell": {
        "Computing and Software Systems": {
            "ACMPT": "Applied Computing",
            "CSS": "Computing and Software Systems",
            "CSSAP": "Application Programming",
            "CSSIE": "Information Engineering",
            "CSSSA": "Systems Analysis"
        },
        "Educational Studies": {
            "BEDUC": "Education",
            "LEDE": "Leadership Development for Educators"
        },
        "Interactive Media Design": {
            "BIMD": "Interactive Media Design"
        },
        ...
```

#### List `[struct='list']`

The call to the `departments` function with the following parameters will yield the List below.

```python
departments(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='list', flatten='dep-abbrev')
```

```
['AFRAM', 'AES', 'AAS', 'CHSTU', 'SWA', 'TAGLG', 'AIS', 'ANTH', 'ARCHY', 'BIOA', 'AMATH', 'CFRM', 'ARCTIC', 'ART', 'ARTH', 'DESIGN', 'ASIAN', 'BENG', 'CHIN', 'HINDI', 'INDN', 'INDO', 'JAPAN', 'KOREAN', 'SNKRT', 'THAI', 'URDU', 'VIET', 'ASTBIO', 'ASTR', 'BIOL', 'CSSS', 'CSDE', 'HUM', 'CHEM', 'CLAR', 'CLLI', 'CLAS', 'GREEK', 'LATIN', 'COM', 'COMMLD', 'CHID', 'CMS', 'CLIT', 'DANCE', 'DXARTS', 'DISST', 'DRAMA', 'ECON', 'ENGL', 'FRENCH', 'ITAL', 'GWSS', 'GENST', 'INDIV', 'GEOG', 'GERMAN', 'HSTAM', 'HSTCMP', 'HSTAFM', 'HSTAS', 'HSTLAC', 'HSTEU', 'HSTAA', 'HSTRY', 'HPS', 'INTSCI', 'ISS', 'RELIG', 'JSIS', 'JSISA', 'JSISB', 'JSISC', 'JSISD', 'JSISE', 'JEWST', 'LSJ', 'ASL', 'LING', 'MATH', 'MUSIC', 'MUSAP', 'MUSED', 'MUSEN', 'MUHST', 'MUSICP', 'ARAB', 'ARAMIC', 'COPTIC', 'EGYPT', 'GEEZ', 'BIBHEB', 'MODHEB', 'NEARE', 'PRSAN', 'TURKIC', 'CHGTAI', 'KAZAKH', 'KYRGYZ', 'UYGUR', 'UZBEK', 'TKISH', 'UGARIT', 'NBIO',...
```

### Column Descriptions

Column Name | Description 
--- | ---
**Department** | The abbreviated name of the department.
**Department Name** | The full name of the department.
**Campus** | The Campus the Department is in.
**College** | The School/College the Department is in. Example: Electrical Engineering (EE) is in the College of Engineering.