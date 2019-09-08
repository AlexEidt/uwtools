"""
Parses UW Time Schedules for each UW Campus and creates a JSON file with all courses that are available in the
upcoming quarter of UW. If the courses for the upcoming quarter are not available, those from the current quarter
are used. The current quarter is calculated, no need to enter any information.
"""

import json, math, re, calendar, datetime, logging, time, os, requests
import urllib3 as URL
from pkgutil import get_data
from zlib import compress, decompress
from itertools import chain
from datetime import datetime as dttime
from datetime import timedelta as td
from threading import Thread
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup


# Links to the Time Schedules for each UW Campus
CAMPUSES_TIMES = {
    'Seattle': {
            'link': 'https://www.washington.edu/students/timeschd/',
            'schedule': 'https://www.washington.edu/students/timeschd/',
        },
    'Bothell': {
            'link': 'https://www.uwb.edu/registration/time/',
            'schedule': 'http://www.washington.edu/students/timeschd/B/',
        },
    'Tacoma': {
            'link': 'https://www.washington.edu/students/timeschd/T/',
            'schedule': 'https://www.washington.edu/students/timeschd/T/',
        }
}

# Mapping of each quarter to the next quarter
QUARTERS = {
    'AUT': 'WIN', 
    'WIN': 'SPR',
    'SPR': 'SUM',
    'SUM': 'AUT',
    'SUMA': 'AUT',
    'SUMB': 'AUT'
}

COURSE_KEYS = ['Course Name', 'Seats', 'SLN', 'Section', 'Type', 'Days', 'Time', 'Building', 'Room Number']
TIME_SCHEDULES_DIR = 'Time_Schedules'


def get_academic_year(year=None):
    """Returns the current academic school year
    @params
        'year': Optional parameter if user wishes to search for a specific 
                Academic School Year.
    Returns
        The Academic School Year. Example: 2019-2020 -> 1920
    """
    if year is None:
        current_year = dttime.now().year
        if dttime.now().month >= 9:
            return str(current_year)[2:] + str(current_year + 1)[2:]
        return str(current_year - 1)[2:] + str(current_year)[2:]
    else:
        return year


def quarter_dates(year=None):
    """Parses UW's Academic Calendar to find current date ranges
       for every quarter
    @params:
        'year': The academic year to get quarter date ranges from.
                Example: 2019-2020 -> 1920
                Academic years starting from 2014-2015 (1415) are supported.
    Returns
        Dictionary with Quarter Abbreviation keys mapping to list of 
        datetime objects representing the range of dates for that quarter
    """
    # Check Parameters
    if year:
        year = str(year)
        start = int(year[0:2])
        end = int(year[2:])
        assert len(year) == 4 and start >= 14 and end == start + 1, 'Invalid Year Argument'
    # Get the academic school year. Example: 2019-2020 -> 1920
    academic_year = get_academic_year(year=year)

    # Check the UW Academic Calendar for the date ranges for each calendar
    uw_request = requests.get(f'https://www.washington.edu/students/reg/{academic_year}cal.html')
    if uw_request.ok:
        quarter_data = BeautifulSoup(uw_request.text, features='lxml')
        table = quarter_data.find('table')
        index = 0
        temp = []
        start_end = {}
        # Month name to index abbreviation. I.e January -> 1, February -> 2, etc
        month_names = {m: n for n, m in enumerate(calendar.month_name)}
        for date_range in table.find_all('td'):
            text = date_range.text
            if '-' not in text and re.search(r'[A-Z][a-z]+ \d+, \d+', text) and text:
                temp.append(text.replace(',', '', 1))
                if len(temp) == 2:
                    datetimes = []
                    for date in temp:
                        month, day, year = date.split(' ')
                        datetimes.append(datetime.date(int(year), month_names[month], int(day)))
                    start_end[list(QUARTERS.keys())[math.floor(index / 2)]] = [d for d in datetimes]
                    temp.clear()
                index += 1
        return start_end
    return {}


def get_quarter(filter_=False, type_='current'):
    """Calculates the current quarter based on the current date
    @params
        'filter_': Filters out the A and B terms of Summer Quarter if necessary if True
                   otherwise does not
        'type_':   'current': Get the current quarter at UW
                   'upcoming': Get the upcoming quarter at UW
    Returns
        String representing the current quarter(s) 
        NOTE: Summer Quarter has two terms, A and B
    """
    # The range_ list is a list of lists with each list containing two datetime objects
    # representing the time range of each quarter. The time range is the first day of the quarter
    # to the last day before the next quarter begins. 
    # This means that if the current date falls in a quarter break, such as Summer break, the current
    # quarter will be Summer (SUM) and the upcoming quarter will be Autumn (AUT)
    range_ = []
    d = list(quarter_dates().values())
    for i in range(4):
        range_.append([d[i][0] if i < 3 else d[i][0] - td(days=365), 
                        (d[i + 1][0] if i < 3 else (d[0][0] - td(days=1)))])
    current_quarters = [q for q, d in zip(QUARTERS.keys(), range_) if d[0] < datetime.date.today() < d[1]]
    if type_ == 'upcoming':
        return ''.join({QUARTERS[q] for q in current_quarters})
    elif type_ == 'current':
        if filter_:
            return 'SUM' if 'SUM' in current_quarters else ''.join(current_quarters)
        else:
            return ','.join(current_quarters)


def parse_departments(campus, none, year=None, quarter=None):
    """Finds all department schedule websites for the given campus
    @params:
        'campus': The campus to get schedules from
        'year': Must be an int. Years must be >= 2003.
                If a year is entered and a quarter is not, all quarters from that year will be parsed.
        'quarter': Must be a str. Each quarter must be either 'AUT', 'WIN', 'SPR', or 'SUM'.
    NOTE:
        For all academic years before and including 2006-2007, some 
        4-digit (and some older 5-digit) SLN codes will not work.
    """
    # Check parameters
    if year:
        assert type(year) == int, 'Year must be of type int'
        assert year >= 2003, f'Time Schedule parsing only supports Time Schedules from 2003 and on'
    if quarter:
        quarter = quarter.upper()
        assert type(quarter) == str, 'Quarter must of type str'
        assert quarter in QUARTERS.values(), f'{quarter} is not a valid quarter'

    def parse(year, current_quarter, upcoming_quarter):
        """Parses the UW Time Schedule for the given year, and quarter
        @params:
            'year': The year to get Time Schedules from
            'current_quarter': The quarter to parse
            'upcoming_quarter': The quarter after 'current_quarter'
        Returns
            A pandas DataFrame object with the time schedule information for the given year
            and quarter combination for the given campus.
        """
        # Parses the time schedule for the given year and quarter based on availability

        # Find the upcoming and current quarters at UW based on the current date
        if upcoming_quarter == 'WIN' and dttime.now().month in [9, 10, 11, 12] and year is None and quarter is None:
            year += 1
        upcoming_courses_link = '{}{}{}/'.format(CAMPUSES_TIMES[campus]['link'], 
                                upcoming_quarter, year)
        if current_quarter != upcoming_quarter:
            current_courses_link = '{}{}{}/'.format(CAMPUSES_TIMES[campus]['link'], 
                                    current_quarter, dttime.now().year)
        else:
            current_courses_link = 'http://hi.com'

        # Check to see if the Time Schedules for the upcoming quarter is available.
        # If not, the Time Schedule for the current quarter will be parsed instead.
        # If neither of the above can be parsed, the script returns None.
        if requests.get(upcoming_courses_link).ok:
            courses_link = '{}{}{}/'.format(CAMPUSES_TIMES[campus]['schedule'], 
                                            upcoming_quarter.upper(), year)
            schedule_link = upcoming_courses_link
            quarter_for_parsing = upcoming_quarter
        elif requests.get(current_courses_link).ok:
            courses_link = '{}{}{}/'.format(CAMPUSES_TIMES[campus]['schedule'], 
                                            current_quarter.upper(), dttime.now().year)
            schedule_link = current_courses_link
            quarter_for_parsing = current_quarter
        else:
            print(f'Time Schedules for UW {campus} - {upcoming_quarter} {year} are not yet available')
            return None
        
        is_bothell = campus == 'Bothell'

        current_quarter = courses_link.split('/')[-2]
        # The UW Bothell Time Schedule has a different layout than those from Seattle and Tacoma.
        if is_bothell:
            dep_soup = re.compile(r'<h2>[A-Z][a-z]+ \d{4} Time Schedule</h2>').split(
                            requests.get(schedule_link).text, 1)[-1]
            dep_soup = BeautifulSoup(re.compile(r'<hr ?/>').split(dep_soup, 1)[-1], features='lxml')
        else:
            dep_soup = BeautifulSoup(requests.get(schedule_link).text, features='lxml')
        # 'anchor_tag' is a list of all the Department links that will be parsed to gather
        # the necessary Time Schedule Information
        anchor_tag = []
        for link in dep_soup.find_all('a'):
            department = link.get('href')
            if department:
                page = department.replace(courses_link, '', 1)
                if bool('.html' in page or courses_link in department) and '/' not in page:
                    anchor_tag.append((department.split('#', 1)[0], link.text))

        list_items = dep_soup.find_all('li')
        get_course = lambda x: x.rsplit('(', 1)[-1].split(')', 1)[0]
        lowercase_re = re.compile(r'[a-z]+')
        campus_schedules = []

        # Go through the Main Time Schedule page for the given quarter and year and parse each department's page
        for link, li in tqdm(zip(anchor_tag, list_items), total=len(anchor_tag)):
            dep = get_course(li.get_text()).upper() if is_bothell else get_course(link[1])
            dep_schedule = '{}{}'.format(courses_link, link[0].rsplit('/', 1)[-1])
            if not re.search(lowercase_re, dep):
                courses = parse_schedules(BeautifulSoup(requests.get(dep_schedule).text, features='lxml'))
                # If no courses are found for the given department, they are not added to the main list
                if courses:
                    campus_schedules.append(courses)
        total = [y for x in campus_schedules for y in x]
        # Store data in a pandas DataFrame
        df = pd.DataFrame(total, columns=COURSE_KEYS)
        df.set_index('Course Name', inplace=True)
        return df

    if year is None and quarter is None:
        # If no quarter or year given, use the most recent quarter/year
        u_quarter = get_quarter(filter_=True, type_='upcoming')
        c_quarter = get_quarter(filter_=True)
        year = dttime.now().year()
        print('Getting UW Time Schedule Data. Parsing usually takes around 1 minute...')
        df = parse(year, c_quarter, u_quarter)
        return df if df is not None and not df.empty else None
    elif year is None and quarter:
        return None
    elif year and quarter is None:
        # If a year is given with no quarter, all quarters from that year will be parsed
        print('Getting UW Time Schedule Data. Parsing usually takes around 4 minutes...')
        df = pd.DataFrame()
        for i, q in enumerate(['AUT', 'WIN', 'SPR', 'SUM']):
            df = pd.concat([df, parse(year + 1 if i else year, q, q)], axis=0)
        return df if df is not None and not df.empty else None
    elif year and quarter:
        # If a year and quarter are given, parse the Time Schedule for that specific year/quarter
        df = parse(year, quarter, quarter)
        return df if df is not None and not df.empty else None


def parse_schedules(department):
    """Creates a dictionary of course, schedule pairings
    @params:
        'department': BeautifulSoup object of the department schedule website
    Returns
        A list of lists. Each nested list contains the following Course Time Data:
            'Course Name', 'Seats', 'SLN', 'Section', 'Type', 
            'Days', 'Time', 'Building', 'Room Number'
        in that order.
    """
    fill = re.compile(r'\d+ */ *\d+[A-Z]?')
    department_schedule = []
    course_schedule = str(department.html).split('<br/>', 2)[-1]
    # All unique courses are split by a <br> in the Time Schedules website
    for sections in course_schedule.split('<br/>'):
        sections = BeautifulSoup(sections, features='lxml')
        table = sections.find('table')
        if table:
            # The 'name' attribute of the first link in each table for each course contains the course name
            name = table.find('a').get('name')
            if name:
                # The <pre> tag in the Time Schedules website contains all the course time information
                for course in sections.find_all('pre'):
                    # Format the 'text' String (which contains all course time information) for later
                    # processing
                    text = course.get_text().replace('\n', '').replace('\r', '').replace('>', '')
                    text = text.replace('Open', '').replace('Closed', '').replace('Restr', '')
                    text = text.replace('IS', '').strip()
                    seats = re.search(fill, text)
                    if seats:
                        seats = re.sub(r'[A-Za-z]+', '', seats.group(0).split('/', 1)[-1].strip())
                    open_closed = fill.split(text, 1)
                    extract = open_closed[0].rsplit(',', 1)[0].rsplit(' ', 1)[0].strip()
                    # Some courses, such as the introductory CHEM courses have only one quiz section that is
                    # labeled as meeting twice a week in the Time Schedule. In order to accurately represent this
                    # course information is displayed in lists to show all times the section meets
                    extra_section = re.search(r'[MTWhF]+\s+\d+\-\d+P?\s+[A-Z\d]+\s+[A-Za-z/\+\-\d]+', 
                                                open_closed[-1])
                    extras = None
                    if len(open_closed) > 1 and extra_section:
                        extras = list(filter(('').__ne__, extra_section.group(0).split(' ')))

                    text = list(filter(('').__ne__, chain([name.upper(), seats], extract.split(' '))))[0:9]

                    if len(text) >= 5:
                        # If the course section contains credits information in the fifth spot, then it is a Lecture
                        if re.search(r'[\*,\[\]\.max\d/ \-]+|(VAR)', text[4]):
                            text[4] = 'LECT'
                        # Courses without a meeting time and location will have their 'Days', 'Time', 'Building', and
                        # 'Room Number' keys be 'N/A'
                        if 'to be arranged' in extract:
                            for i in range(-1, -5, -1):
                                text[i] = 'N/A'
                        course_data = {k: [] for k in COURSE_KEYS}
                        for key, value in zip(COURSE_KEYS, text):
                            course_data[key].append(value)
                        if extras is not None:
                            for key, value in zip(['Days', 'Time', 'Building', 'Room Number'], extras):
                                course_data[key].append(value)
                        # For some sections, the Building and Room Numbers are denoted by *
                        # If this is the case, the * are replaced with N/A for consistency
                        for stat in ['Building', 'Room Number']:
                            for i, value in enumerate(course_data[stat]):
                                # '*' indicates a section meeting time that has not yet been determined
                                if value == '*':
                                    course_data[stat][i] = 'N/A'
                            if not course_data[stat]:
                                course_data[stat].append('N/A')
                        # Course section information is stored in a dictionary for better readibility/debugging
                        # and easier manipulation
                        new_dict = {}
                        two_sections = False
                        for key, value in course_data.items():
                            if len(value) == 2:
                                two_sections = True
                                break
                        for key, value in course_data.items():
                            if len(value) == 1:
                                new_dict[key] = value * 2
                            else:
                                new_dict[key] = value
                        course_sections = []
                        for i in range(2):
                            temp = []
                            for val in new_dict.values():
                                if i == 1 and len(val) > 1:
                                    temp.append(val[i])
                                elif i == 0 and len(val) >= 1:
                                    temp.append(val[i])
                            course_sections.append(temp)
                        if course_sections:
                            if two_sections:
                                for x in course_sections:
                                    if not re.search(r'\d+', x[-1]):
                                        for i in range(-1, -5, -1):
                                            x[i] = 'N/A'
                                    department_schedule.append(x)
                            else:
                                if not re.search(r'\d+', course_sections[0][-1]):
                                    for i in range(-1, -5, -1):
                                        course_sections[0][i] = 'N/A'
                                department_schedule.append(course_sections[0])
    return department_schedule


def gather(campuses=['Seattle', 'Bothell', 'Tacoma'], year=None, quarter=None):
    """Gathers the Time Schedules for the given UW Campuses
    @params:
        'campuses': The Campuses to get the Time Schedules from
        'year': The year to get time schedules from
        'quarter': The specific quarter to get time schedules from
    Returns:
        A Pandas DataFrame representing the Time Schedules
    """
    assert int(year) >= 2003, 'Only years supported are from 2003-Present'
    if 2003 <= int(year) <= 2019:
        total = pd.DataFrame()
        for campus in campuses:
            archived_schedules = str(decompress(get_data(__package__, 
                                     f'Time_Schedules/{campus}_Compressed')).decode())
            df = pd.DataFrame([x.split('\t') for x in archived_schedules.split('\n')], 
                            columns=['Index'] + COURSE_KEYS + ['Campus', 'Quarter', 'Year'])
            df.drop('Index', axis=1, inplace=True)
            if year and not quarter:
                df = df[df['Year'] == str(year)]
            elif not year and quarter:
                df = df[df['Quarter'] == str(quarter)]
            elif year and quarter:
                df = df[(df['Year'] == str(year)) & (df['Quarter'] == quarter)]
            elif not year and not quarter:
                df = df[1:-1]
            total = pd.concat([total, df], axis=0)
        return total if total is not None and not total.empty else None
    else:
        df = pd.DataFrame()
        for campus in campuses:
            df = pd.concat([df, parse_departments(campus, None, 
                            year=int(year) if year else None, quarter=quarter)])
        return df if df is not None and not df.empty else None
