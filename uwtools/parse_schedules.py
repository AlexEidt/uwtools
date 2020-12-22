"""
Parses UW Time Schedules for each UW Campus and creates a JSON file with all courses that are available in the
upcoming quarter of UW. If the courses for the upcoming quarter are not available, those from the current quarter
are used. The current quarter is calculated, no need to enter any information.
"""

import json, math, re, calendar, datetime, time, os, requests
from pkgutil import get_data
from zlib import compress, decompress
from itertools import chain
from datetime import datetime as dttime
from datetime import timedelta
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
import concurrent.futures as cf
from multiprocessing import Process


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

def get_academic_year(year):
    """
    Returns the current academic school year

    @params

        'year': A specific Academic School Year.

    Returns

        The Academic School Year. Example: 2019-2020 -> 1920
    """
    if year == dttime.now().year:
        if dttime.now().month >= 9:
            return str(year)[2:] + str(year + 1)[2:]
        return str(year - 1)[2:] + str(year)[2:]
    return str(year)[2:] + str(year + 1)[2:]


def quarter_dates(year=None):
    """
    Parses UW's Academic Calendar to find current date ranges
    for every quarter

    @params

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
    if year is None:
        academic_year = get_academic_year(dttime.now().year)
    else:
        academic_year = year

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
                temp.append(text.replace(',', '', 1).replace('\n', '').replace('\r', ''))
                if len(temp) == 2:
                    datetimes = []
                    for date in temp:
                        data = list(filter(None, date.split(' ')))
                        if len(data) == 3:
                            datetimes.append(datetime.date(int(data[2]), month_names[data[0]], int(data[1])))
                    start_end[list(QUARTERS.keys())[math.floor(index / 2)]] = [d for d in datetimes]
                    temp.clear()
                index += 1
        return start_end
    return {}


def get_quarter(filter_=False, type_='current'):
    """
    Calculates the current quarter based on the current date

    @params

        'filter_': Filters out the A and B terms of Summer Quarter if necessary if True
                   otherwise does not

        'type_':   'current': Get the current quarter at UW
                   'upcoming': Get the upcoming quarter at UW

        'include_year': If True, returns a tuple of the current quarter and corresponding year.

    Returns

        String representing the current quarter(s) 
        NOTE: Summer Quarter has two terms, A and B
    """
    assert type(filter_) == bool, 'Type of "filter_" must be bool'
    assert type(type_) == str, 'Type of "type_" must be str'
    assert type_ in ['current', 'upcoming'], 'Value of "type_" must be "current" or "upcoming"'

    # The range_ list is a list of lists with each list containing two datetime objects
    # representing the time range of each quarter. The time range is the first day of the quarter
    # to the last day before the next quarter begins. 
    # This means that if the current date falls in a quarter break, such as Summer break, the current
    # quarter will be Summer (SUM) and the upcoming quarter will be Autumn (AUT)
    current_dates = quarter_dates()
    previous_dates = quarter_dates(year=get_academic_year(dttime.now().year - 1))
    ranges = list(current_dates.values())[:-2]
    # Change each quarters ending date to be the next quarters starting date minus one day
    for i in range(len(ranges)):
        # If the quarter is the last quarter (SUM), use AUT quarters starting date
        if i == len(ranges) - 1:
            ranges[i][1] = ranges[0][0] - timedelta(days=1)
            continue
        ranges[i][1] = ranges[i + 1][0] - timedelta(days=1)
    ranges += list(current_dates.values())[-2:]
    prev = list(previous_dates.values())
    for i in range(3, 6):
        ranges[i] = prev[i]
    ranges[3][1] = ranges[0][0] - timedelta(days=1)
    current_quarters = [q for q, d in zip(QUARTERS.keys(), ranges) 
                        if d[0] <= datetime.date.today() <= d[1]]
    if type_ == 'upcoming':
        quarter = ''.join({QUARTERS[q] for q in current_quarters})
        if filter_:
            return 'SUM' if 'SUM' in quarter else quarter
        if 'SUM' in quarter:
            return 'SUM, SUMA, SUMB'
        return quarter
    elif type_ == 'current':
        if filter_:
            quarter = ''.join(current_quarters)
            return 'SUM' if 'SUM' in quarter else quarter
        return ', '.join(current_quarters)
    return None


def parse_departments(campus, year, quarter, progress_bar):
    """
    Finds all department schedule websites for the given campus

    @params

        'campus': The campus to get schedules from

        'year': Must be an int. Years must be >= 2003.
                If a year is entered and a quarter is not, all quarters from that year will be parsed.

        'quarter': Must be a str. Each quarter must be either 'AUT', 'WIN', 'SPR', or 'SUM'.

    NOTE:
        For all academic years before and including 2006-2007, some 
        4-digit (and some older 5-digit) SLN codes will not work.

    Returns

        A pandas DataFrame object with the time schedule information for the given year
        and quarter combination for the given campus.
    """
    # Find current quarter at UW based on the current date
    current_courses_link = '{}{}{}/'.format(CAMPUSES_TIMES[campus]['link'], 
                                            quarter, year)

    # Check to see if the Time Schedules for the current quarter is available.
    # If neither of the above can be parsed, the script returns None.
    current_courses_requests = requests.get(current_courses_link)
    if current_courses_requests.ok:
        courses_link = '{}{}{}/'.format(CAMPUSES_TIMES[campus]['schedule'], 
                                        quarter, year)
    else:
        return None
    
    is_bothell = campus == 'Bothell'
    # The UW Bothell Time Schedule has a different layout than those from Seattle and Tacoma.
    if is_bothell:
        dep_soup = re.compile(r'<h2>[A-Z][a-z]+ \d{4} Time Schedule</h2>').split(
                        current_courses_requests.text, 1)[-1]
        dep_soup = BeautifulSoup(re.compile(r'<hr ?/>').split(dep_soup, 1)[-1], features='lxml')
    else:
        dep_soup = BeautifulSoup(current_courses_requests.text, features='lxml')
    # 'anchor_tag' is a list of all the Department links that will be parsed to gather
    # the necessary Time Schedule Information
    anchor_tag = []
    for link in dep_soup.find_all('a'):
        department = link.get('href')
        if department:
            page = department.replace(courses_link, '', 1)
            if '/' not in page and bool('.html' in page or courses_link in department):
                anchor_tag.append((department.rsplit('#', 1)[0], link.text))

    list_items = dep_soup.find_all('li')
    get_course = lambda x: x.rsplit('(', 1)[-1].split(')', 1)[0]
    lowercase_re = re.compile(r'[a-z]+')
    campus_schedules = []

    local_parse_schedules = parse_schedules

    with cf.ThreadPoolExecutor() as executor:
        results = []
        # Go through the Main Time Schedule page for the given quarter and year and parse each department's page
        for link, li in zip(anchor_tag, list_items):
            if progress_bar is not None:
                progress_bar.update()
            dep = get_course(li.get_text()).upper() if is_bothell else get_course(link[1])
            dep_schedule = '{}{}'.format(courses_link, link[0].rsplit('/', 1)[-1])
            if not re.search(lowercase_re, dep):
                results.append(
                    executor.submit(local_parse_schedules, dep_schedule)
                )
        for result in cf.as_completed(results):
            courses = result.result()
            # If no courses are found for the given department, they are not added to the main list
            if courses:
                campus_schedules.append(courses) 
                
    total = [y for x in campus_schedules for y in x] 
    # Store data in a pandas DataFrame
    df = pd.DataFrame(total, columns=COURSE_KEYS)
    df['Campus'] = campus
    df['Year'] = year
    df['Quarter'] = quarter

    return df


fill = re.compile(r'\d+ */ *\d+[A-Z]?')
seats_re = re.compile(r'[A-Za-z]+')
extra_section_re = re.compile(r'[MTWhF]+\s+\d+\-\d+P?\s+[A-Z\d]+\s+[A-Za-z/\+\-\d]+')
lecture_re = re.compile(r'[\*,\[\]\.max\d/ \-]+|(VAR)')

def parse_schedules(department):
    """
    Creates a dictionary of course, schedule pairings

    @params

        'department': The department schedule website

    Returns

        A list of lists. Each nested list contains the following Course Time Data:
            'Course Name', 'Seats', 'SLN', 'Section', 'Type', 
            'Days', 'Time', 'Building', 'Room Number'
        in that order.
    """
    local_fill = fill
    local_seats_re = seats_re
    local_extra_section_re = extra_section_re
    local_lecture_re = lecture_re
    department_schedule = []
    department = BeautifulSoup(requests.get(department).text, features='lxml')
    course_schedule = str(department).split('<br/>', 2)[-1]
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
                    text = course.get_text().replace('\n', '').replace('\r', '').replace('>', '', 1)
                    text = text.replace('Open', '').replace('Closed', '').replace('Restr', '', 1)
                    text = text.replace('IS', '').strip()
                    seats = re.search(local_fill, text)
                    if seats:
                        seats = re.sub(local_seats_re, '', seats.group(0).split('/', 1)[-1].strip())
                    open_closed = local_fill.split(text, 1)
                    extract = open_closed[0].rsplit(',', 1)[0].rsplit(' ', 1)[0].strip()
                    text = list(filter(None, chain([name.upper(), seats], extract.split())))[0:9]
                    if len(text) >= 5:
                        if re.search(local_lecture_re, text[4]):
                            text[4] = 'LECT'
                        if 'to,be,arranged' in ','.join(text):
                            for i in range(-1, -4, -1):
                                text[i] = ''
                        for i, data in enumerate(text):
                            if data == '*' or data == 'to':
                                text[i] = ''
                        # Some courses, such as the introductory CHEM courses have only one quiz section that is
                        # labeled as meeting twice a week in the Time Schedule. In order to accurately represent this
                        # course information is displayed in lists to show all times the section meets
                        extra_section = re.search(local_extra_section_re, open_closed[-1])
                        if len(open_closed) > 1 and extra_section:
                            extras = list(chain(text[0:5], filter(None, extra_section.group(0).split())))
                            department_schedule.append(extras)
                        department_schedule.append(text)
    return department_schedule


# --------------------------Time Methods--------------------------#       
get_time = lambda t: [t[0:1], t[1:]] if len(t) == 3 else [t[0:2], t[2:]]
check_pm = lambda t: ' PM' if t else ' AM'
convert = lambda t: time.strftime('%H:%M:%S', time.strptime(t, '%I:%M %p'))
check_convert_pm = lambda t: convert('12:01 AM') < convert(t) < convert('6:30 AM') or convert('10:30 PM') < convert(t) < convert('11:59 PM')
convert_pm = lambda t, pm: f'{pm[0]} {switch_pm(pm[-1])}' if check_convert_pm(t) else t
switch_pm = lambda t: 'AM' if t.strip() == 'PM' else 'PM'
# --------------------------Time Methods--------------------------#    


def to_time(time1):
    """
    Converts the given time to a time object

    @params

        'time1': Time of format: HHMM-HHMM
                 Example: 930-1120

    Returns 

        The converted times (split by '-') into time
        objects 
    """
    if time1:
        try:
            pm = 'P' in time1
            time1 = time1.replace('P', '', 1)
            times = list(map(get_time, time1.split('-', 1)))
            t1 = f'{times[0][0]}:{times[0][1]}{check_pm(pm)}'
            t2 = f'{times[1][0]}:{times[1][1]}{check_pm(pm)}'
            time1 = convert(convert_pm(t1, t1.rsplit(' ', 1)))
            time2 = convert(convert_pm(t2, t2.rsplit(' ', 1)))
        except Exception:
            return None
        else:
            return time1, time2
    return None


def gather(year, quarter, campuses=['Seattle', 'Tacoma', 'Bothell'], struct='df',
           include_datetime=False, show_progress=False, json_ready=False):
    """
    Gathers the Time Schedules for the given UW Campuses

    @params
    
        'year': The year to get time schedules from

        'quarter': The specific quarter to get time schedules from

        'campuses': The Campuses to get the Time Schedules from

        'struct': The Data Structure to return the Time Schedule data in
                  'df' -> Pandas DataFrame
                  'dict' -> Python Dictionary

        'include_datetime': Adds two columns to the DataFrame/Dict, ['Start', 'End'] which
                            are datetime objects representing the start and ending times for
                            the course. This is useful when checking if courses overlap
                            or other analysis relating to duration of courses, etc...
                            WARNING: Including the datetime may result in slower performance.

        'show_progress': Displays a progress meter in the console if True,
                         otherwise displays nothing

        'json_ready': If struct='dict', and you would like to store the dict in a .json file,
                      json_ready removes all the datetime objects to prevent TypeErrors
                      when converting to JSON. 

    Returns

        A Pandas DataFrame/Python Dictionary representing the Time Schedules 
        for the given courses
    """
    # Check if all campuses in 'campuses' are valid
    assert all([c in ['Seattle', 'Bothell', 'Tacoma'] for c in list(map(str.title, campuses))])
    assert type(struct) == str, 'Type of "struct" must be str'
    assert struct in ['df', 'dict'], f'{struct} is not a valid argument for "struct"'
    assert type(include_datetime) == bool, 'Type of "include_datetime" must be bool'
    assert type(show_progress) == bool, 'Type of "show_progress" must be bool'
    assert type(json_ready) == bool, 'Type of "json_ready" must be bool'

    time_schedules = pd.DataFrame()
    if show_progress:
        progress_bar = tqdm()

    # Parse all UW Time Schedules for each campus in parallel
    with cf.ThreadPoolExecutor() as executor:
        results = []
        for campus in campuses:
            results.append(
                executor.submit(parse_departments, campus.title(), int(year), quarter, 
                                progress_bar if show_progress else None)
            )
        for result in cf.as_completed(results):
            schedule = result.result()
            if schedule is not None:
                time_schedules = pd.concat([time_schedules, schedule])

    if include_datetime:

        def startend(times, start):
            times = to_time(times)
            if times:
                if start:
                    return times[0]
                return times[1]
            return None

        time_schedules['Start'] = pd.to_datetime(
            time_schedules['Time'].apply(startend, args=(True,)), errors='ignore', format='%H:%M:%S'
        ).dt.time
        time_schedules['End'] = pd.to_datetime(
            time_schedules['Time'].apply(startend, args=(False,)), errors='ignore', format='%H:%M:%S'
        ).dt.time
        # Re-order indices of DataFrame
        time_schedules = time_schedules[['Course Name', 'Seats', 'SLN', 'Section', 'Type', 'Time', 
                    'Start', 'End', 'Building', 'Room Number', 'Campus', 'Quarter', 'Year']]

    time_schedules.index = range(len(time_schedules.index))
    time_schedules.index.name = 'Index'
    if struct == 'df':
        return time_schedules
    elif struct == 'dict':
        if json_ready and include_datetime:
            time_schedules.drop(['Start', 'End'], axis=1, inplace=True)
        return time_schedules.to_dict(orient='records')