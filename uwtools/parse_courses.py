""" Creates a tsv file containing course data for each UW Campus """

import re, time, json, os, requests
import pandas as pd
import concurrent.futures as cf
from tqdm import tqdm
from bs4 import BeautifulSoup
from unicodedata import normalize

CAMPUSES = {   
    'Seattle': 'http://www.washington.edu/students/crscat/',                                                                             
    'Bothell': 'http://www.washington.edu/students/crscatb/',                                                               
    'Tacoma': 'http://www.washington.edu/students/crscatt/'                                 
}                                                                                           

COLUMN_NAMES = ['Campus', 'Department Name', 'Course Number', 'Course Name', 'Credits',
                'Areas of Knowledge', 'Quarters Offered', 'Offered with', 
                'Prerequisites', 'Co-Requisites', 'Description']


def check_campus(department_name, department_dict, val):
    """
    Returns the campus/college the given 'department_name' is in
    depending on the value of the 'val' parameter

    @params

        'department_name': The full name of the department to search for

        'department_dict': The dictionary of department information to search through

        'val': Can either be 'Campus' or 'College', used to determine which value
               to return

    Returns
    
        The campus or college the given 'department_name' is in
    """
    # for [c] -> campus, [college] -> Colleges in Campus
    for c, college in department_dict.items():
        for col_name, deps in college.items():
            for dep_a, dep_f in deps.items():
                if val == 'Campus':
                    if dep_f == department_name:
                        return c
                elif val == 'College':
                    if dep_f == department_name or dep_a == department_name:
                        return col_name


find_all_re = re.compile(r'[A-Z& ]+/[A-Z& ]+/[A-Z& ]+\d+')
find_one_re = re.compile(r'[A-Z& ]+/[A-Z& ]+\d+')
find_series_2_re = re.compile(r'[A-Z& ]+\d+, ?\d{3}')
find_series_3_re = re.compile(r'[A-Z& ]+\d+, ?\d{3}, ?\d{3}')
course_re = re.compile(r'[A-Z& ]+')
three_digits = re.compile(r'\d{3}')

def complete_description(description):
    """
    Replaces all occurances of un-numbered courses in the given course description

    @params

        'description': The course description

    Returns 

        Completed courses in description
    """
    local_find_all_re = find_all_re
    local_find_one_re = find_one_re
    local_find_series_2_re = find_series_2_re
    local_find_series_3_re = find_series_3_re
    local_course_re = course_re
    local_three_digits = three_digits

    find_all = re.findall(local_find_all_re, description)
    find_one = re.findall(local_find_one_re, description)
    
    def remove_in(a, b):
        remove = [y for x in a for y in b if y in x]
        a.extend(b)
        for x in remove: a.remove(x)
        return a
            
    if find_one:
        find_all = remove_in(find_all, find_one)
        for i, x in enumerate(find_all):
            completed = []
            find_all[i] = x.replace(' ', '')
            number = re.search(local_three_digits, find_all[i]).group(0)
            for crs in re.findall(local_course_re, find_all[i]):
                completed.append(f'{crs}{number}')
            description = description.replace(x, ' {}'.format('/'.join(completed)), 1)

    find_series_2 = re.findall(local_find_series_2_re, description)
    find_series_3 = re.findall(local_find_series_3_re, description)
    if find_series_2 or find_series_3:
        find_series_2 = remove_in(find_series_3, find_series_2)
        for i, series in enumerate(find_series_2):
            find_series_2[i] = series.replace(' ', '')
            course_dep = re.search(local_course_re, find_series_2[i])
            if course_dep: 
                depmnt = course_dep.group(0)
                description = description.replace(series, f'{depmnt}{find_series_2[i][-3:]}', 1)
    return description


not_offered = re.compile(r'[Nn]ot open to students')
co_req = re.compile(r'[Cc]o-?[Rr]equisites?')
no_credit_if_re = re.compile \
    (r'([Cc]annot|[Mm]ay not) be taken for credit if (credit received for|student has taken)?[A-Z& ]+\d{3}')
mulitple_re = re.compile(r'[A-Z& ]+\d{3}/[A-Z& ]+\d{3}/[A-Z& ]+\d{3} and')
find_match_re = re.compile(r'([A-Z& ]{2,}\d{3})')  

def get_requisites(description, type_):
    """
    Gets the requisite courses for the given course

    @params

        'description': The course description

        'type_': Either 'Prerequisite' or 'Co-Requisite'

    Returns

        The requisite courses. 
    """
    if type_ not in description:                                                             
        return ''    

    local_not_offered = not_offered
    local_co_req = co_req
    local_no_credit_if_re = no_credit_if_re
    local_mulitple_re = mulitple_re
    local_find_match_re = find_match_re

    description = description.replace(' AND ', ' and ').replace(' OR ', ' or ').replace('; or', '/')
    description = description.replace('and either', ';').replace('and one of', ';')
    description = re.sub(local_no_credit_if_re, '', description)
    description = local_not_offered.split(description.rsplit('Offered:', 1)[0].split(type_, 1)[-1])[0]
    multiple = re.search(local_mulitple_re, description)
    if multiple:
        description = description.replace(multiple.group(0), f'{multiple.group(0)[:-4]};', 1)
    del multiple, local_mulitple_re, local_not_offered, local_no_credit_if_re
    if 'Prerequisite' in type_: description = local_co_req.split(description)[0]   
    del local_co_req                      
    POI = ',POI' if 'permission' in description.lower() else '' 
    new_result = []
    for course in description.split('(')[0].split(';'):
        if ', and' in course:
            new_result.append(course.replace(',', ';'))     
        else:
            new_result.append(course)
    description = ';'.join(new_result)
    del new_result

    if 'with either' in description:
            with_either = description.split('with either')
            description = '{}&&{}'.format(with_either[0], with_either[1].replace(' or ', '/'))
    description = description.replace(' and ', '&&').replace(' or ', ',')

    def extract(course_option, split_char):
        elements = []
        for next_option in filter(None, course_option.split(split_char)):
            find_match(next_option, elements)
        return elements

    def find_match(to_match, to_append):
        match = re.search(local_find_match_re, to_match)
        if match: to_append.append(match.group(0))

    semi_colon = []
    for crs in filter(None, description.split(';')):
        comma = []
        for option in filter(None, crs.split(',')):
            if '/' in option and '&&' not in option:
                comma.append('/'.join(extract(option, '/')))
            elif '/' not in option and '&&' in option:
                comma.append('&&'.join(extract(option, '&&')))
            elif '/' in option and '&&' in option:
                doubleand = ('/'.join(extract(x, '/')) for x in filter(None, option.split('&&')))
                comma.append('&&'.join(doubleand))
            else:
                find_match(option, comma) 
        semi_colon.append(','.join(filter(None, comma)))
    result = ';'.join(filter(None, semi_colon)).replace(' ', '') \
                .strip(',').strip(';').strip('&').replace(';,', ';')
    result = f'{result}{POI}'
    del POI, semi_colon
    result = re.sub(r'&{3,}', '', result)
    result = ','.join(filter(None, result.split(',')))
    result = ';'.join(filter(None, result.split(';')))
    result = ','.join(dict.fromkeys(result.split(','))).replace(';&&', ';').strip('&')
    result = ';'.join(dict.fromkeys(result.split(';')))
    result = result.strip(',').strip(';').strip('&').replace(';,', ';').strip()
    filter_result = []
    for course in result.split(';'):
        if '/' in course and '&&' not in course:
            filter_result.append(course.replace('/', ','))
        elif '/' not in course and '&&' in course and ',' not in course:
            filter_result.append(course.replace('&&', ';'))
        else:
            filter_result.append(course)
    return ';'.join(filter_result)


parts_re = re.compile(r'([A-Z& ]+\d+)')
quarters = ['A', 'W', 'Sp', 'S']

def get_offered(description):
    """
    Gets the quarters the course is offered

    @params

        'description': The course description

    Returns

        Quarters offered as comma separated list (A, W, Sp, S)
    """
    if 'Offered:' not in description:                                                       
        return ''  
    local_parts_re = parts_re
    local_quarters = quarters
                                                                         
    check_parts = description.rsplit('Offered:', 1)[-1]                                         
    parts = check_parts.split(';')[1] if ';' in check_parts else check_parts
    parts = re.sub(local_parts_re, '', parts)
    result = []
    for quarter in local_quarters:
        if quarter in parts:
            result.append(quarter)
            parts = parts.replace(quarter, '', 1)
    return ','.join(result)        


course_re = re.compile(r'[A-Z&]+')
course_name_re = re.compile(r'[^\(]+')
credits_re = re.compile(r'(I&S)|(DIV)|(NW)|(VLPA)|(QSR)')
credits_num_re = re.compile(r'\([\*,\[\]\.max\d/ \-]+\)')
offered_jointly_re = re.compile(r'([A-Z& ]+\d+)')

def parse_catalogs(campuses=['Seattle', 'Bothell', 'Tacoma'], struct='df', 
                   show_progress=False):
    """
    Parses the UW Course Catalogs for the given campuses

    @params

        'campuses': The Campuses to get the course catalogs from
                    Can either be a list of campuses, or a dictionary where
                    the keys are the campuses and values are a list of departments
                    to parse from that campus

        'struct': The Data Structure to return the course catalog data in
                  'df' -> Pandas DataFrame
                  'dict' -> Python Dictionary

        'show_progress': Displays a progress meter in the console if True,
                         otherwise displays nothing

    Returns

        A Pandas DataFrame/Python Dictionary representing the course catalogs for all UW
        Campuses in the 'campuses' list. 
    """
    assert type(campuses) == list or type(campuses) == dict, 'Type of "campuses" must be list or dict'
    if type(campuses) == dict:
        for key, value in campuses.items():
            if type(key) != str or type(value) != list:
                raise ValueError('''"campuses" dict must have keys of type str and
                                     values of type list''')
    # Check if all campuses in 'campuses' are valid
    assert all([c in ['Seattle', 'Bothell', 'Tacoma'] for c in list(map(str.title, campuses))])
    assert type(struct) == str, 'Type of "struct" must be str'
    assert type(show_progress) == bool, 'Type of "show_progress" must be bool'
    assert struct in ['df', 'dict'], f'{struct} is an invalid argument for "struct"'

    # Progress bar for Course Schedule Parsing
    if show_progress:
        progress_bar = tqdm()

    def parse_campus(department_data, campus):
        """
        Parses all courses from a UW Campus

        @params

            'department_data': BeautifulSoup object with the department list website source
                               for the given 'campus'

            'campus': The campus to get courses from

        Returns

            A pandas DataFrame with all courses in the given campus
        """

        def extract_data(department_link):
            """
            Extracts all course information from a UW Department

            @params:

                'department_link': The url to the UW Department to get course
                                   information from

            Returns

                A list of lists. Each nested list represents one course section with the
                following values (in this order):

                'Campus', 'Department Name', 'Course Number', 'Course Name', 'Credits',
                'Areas of Knowledge', 'Quarters Offered', 'Offered with', 
                'Prerequisites', 'Co-Requisites', 'Description'
            """
            # Update the progress bar
            if show_progress:
                progress_bar.update()

            # Regular expressions for searching course descriptions stored in local variables
            # for better peformance
            local_course_re = course_re
            local_course_name_re = course_name_re
            local_credits_re = credits_re
            local_credits_num_re = credits_num_re
            local_offered_jointly_re = offered_jointly_re
            local_CAMPUSES = CAMPUSES

            # Method used in extracting data from course descriptions found in the local scope
            # are stored in local variables for better performance
            local_complete_description = complete_description
            local_get_offered = get_offered
            local_get_requisites = get_requisites

            # All the courses in the department
            courses = []
            dep_file = department_link.get('href')

            # If the user entered a dict as the 'campuse' parameter, departments
            # are checked here
            try:
                # The String in the conditional is the abbreviated Department Name i.e EE
                # for Electrical Engineering
                if normalize('NFKD', department_link.text).rsplit('(', 1) \
                    [-1].replace(' ', '')[:-1] not in campuses[campus]:
                    return None
            except TypeError:
                pass
                
            # The only links that are used for finding departments are those
            # of the format [a-z]+.html
            if '/' not in dep_file and dep_file.endswith('.html') \
                                   and dep_file not in parsed_departments:
                parsed_departments.add(dep_file)
                department = BeautifulSoup(requests.get( \
                            f'{local_CAMPUSES[campus]}{dep_file}').text, features='lxml')
                for course in department.find_all('a'):
                    course_ID = course.get('name')  
                    if course_ID:
                        course_ID = course_ID.upper()
                        course_title = course.find('b').text
                        # The Course Description
                        description = course.get_text().replace(course_title, '', 1)        
                        instructors = course.find('i')
                        if instructors:
                            description = description.replace(str(instructors.get_text()), '', 1)
                        del instructors
                        course_text = local_complete_description( \
                                        description.rsplit('View course details in MyPlan', 1)[0])
                        # Course Number i.e 351
                        course_number = re.sub(local_course_re, '', course_ID)
                        match_name = re.search(local_course_name_re, course_title)
                        match_credit_num = re.search(local_credits_num_re, course_title)
                        match_credit_types = re.findall(local_credits_re, course_title)
                        # Jointly offered course with the given course
                        if 'jointly with' in course_text:                                                   
                            offered_jointly = course_text.rsplit('jointly with ', 1)[-1].rsplit(';', 1)[0]                                
                            offered_jointly = ','.join(re.findall( \
                                local_offered_jointly_re, offered_jointly)).replace(' ', '') 
                        else:
                            offered_jointly = ''
                        courses.append(
                                # Campus, Department Name and Course Number
                                [campus, course_ID[:-3], course_number, 
                                # Course Name
                                match_name.group(0).split(course_number, 1)[-1].strip() \
                                                            if match_name else '',
                                # Number of credits for the course
                                match_credit_num.group(0)[1:-1] \
                                                            if match_credit_num else '', 
                                # Course Credit Types (I&S, DIV, NW, VLPA, QSR, C)
                                ','.join([list(filter(('').__ne__, x))[0] for x in match_credit_types]) \
                                                            if match_credit_types else '', 
                                local_get_offered(course_text),
                                offered_jointly, local_get_requisites(course_text, 'Prerequisite:'), 
                                local_get_requisites(course_text, 'Co-requisite'), course_text]
                        )
            return courses

        # In the course catalog website, several department links appear multiple times
        # To prevent parsing the same department more than once, parsed departments
        # are tracked in 'parsed_departments'
        parsed_departments = set()
        local_extract_data = extract_data
        department_data = BeautifulSoup(requests.get(department_data).text, features='lxml')

        campus_catalog = []
        # Extract data from department websites in parallel to reduce idle time
        with cf.ThreadPoolExecutor() as executor:
            results = [executor.submit(local_extract_data, department_link) 
                       for department_link in department_data.find_all('a')]
            for result in cf.as_completed(results):
                dptmnt = result.result()
                if dptmnt:
                    campus_catalog.append(dptmnt)

        # DataFrame with all courses in the campus
        return pd.DataFrame(
            [course for department in campus_catalog for course in department], 
            columns=COLUMN_NAMES
        )

    # The pandas DataFrame to store the entire course catalog for each UW Campus entered
    # by the user
    course_catalog = pd.DataFrame()

    # Parse all three campuses in parallel for faster run time as well
    # as get the departments dictionary from the 'get_departments' method
    # to add a 'Colleges' column to categorize all courses in their College.
    with cf.ThreadPoolExecutor() as executor:
        results = []
        campuses_for_dict = campuses
        if type(campuses) == dict:
            campuses_for_dict = list(campuses.keys())
        results.append(executor.submit(get_departments, campuses=campuses_for_dict, struct='dict'))
        for campus, link in CAMPUSES.items():
            if campus.title() in campuses: 
                results.append(executor.submit(parse_campus, link, campus.title()))
        for result in cf.as_completed(results):
            returned = result.result()
            if type(returned) == dict:
                # Departments dict used to create the 'College' column in the main DataFrame
                departments = returned
            else:
                course_catalog = pd.concat([course_catalog, returned])

    # Add Course ID as the index of the DataFrame to allow for easy course searching
    # Course ID = Department Name + Course Number
    # Example: EE235 = EE + 235
    course_catalog['Course ID'] = course_catalog['Department Name'] + course_catalog['Course Number']
    course_catalog['College'] = course_catalog['Department Name'].apply(check_campus, args=(departments, 'College'))
    course_catalog.set_index('Course ID', inplace=True)
    # Re-order indices to place 'College' right after the 'Department Name'
    course_catalog = course_catalog[['Campus', 'Department Name', 'College', 'Course Number', 'Course Name', 'Credits',
                                    'Areas of Knowledge', 'Quarters Offered', 'Offered with', 
                                    'Prerequisites', 'Co-Requisites', 'Description']]
    
    if struct == 'df':
        return course_catalog
    elif struct == 'dict':
        return course_catalog.to_dict(orient='index')


def get_departments(campuses=['Seattle', 'Tacoma', 'Bothell'], struct='df',
                    flatten='default'):
    """
    Returns the departments at UW for each campus

    @params

        'campuses': The Campuses to get the departments from

        'struct':   The Data Structure to return the department data in
                    'df' -> Pandas DataFrame
                    'dict' -> Python Dictionary

        'flatten':  If struct='dict', return a flattened dictionary of departments.
                    If struct='list', return a list of items specified by the 'flatten' parameter.

                    Flatten options:

                    struct='dict':

                        'default':

                            Campus
                                College
                                    Department Abbreviation -> Department Full Name

                        'college':

                            College
                                Department Abbreviation -> Department Full Name

                        'department':

                            Department Abbreviation -> Department Full Name

                        'campus':

                            Campus
                                Department Abbreviation -> Department Full Name

                        'campege':

                            Campus
                                College

                    struct='list':

                        'college': Returns a list of all colleges in every campus given
                                   in 'campuses'

                        'dep-abbrev': Returns a list of all departments (abbreviations) 
                                      in every campus given in 'campuses'

                        'dep-full': Returns a list of all departments (full names) in
                                    every campus given in 'campuses     

    Returns

        struct='df' or struct='dict':

            A Pandas DataFrame/Python Dictionary of the Departments for every
            campus given in 'campuses'

        struct='list':

            A list of values specified by the 'flatten' parameter
    """
    assert type(campuses) == list, 'Type of "campuses" must be list'
    # Check if all campuses in 'campuses' are valid
    assert all([c in ['Seattle', 'Bothell', 'Tacoma'] for c in list(map(str.title, campuses))])
    assert type(struct) == str, 'Type of "struct" must be str'
    assert struct in ['df', 'dict', 'list'], f'{struct} is not a valid argument for "struct"'
    assert type(flatten) == str, 'Type of "flatten" must be str'
    assert flatten in ['default', 'college', 'department', 'campus', 
                       'campege', 'dep-abbrev', 'dep-full'], f'{flatten} is not a valid argument for "flatten"'
    if struct == 'list':
        assert flatten in ['college', 'dep-abbrev', 'dep-full'], f'''{flatten} is not a valid 
                                argument for "flatten" with 'struct="list"' '''

    # Get UW Campus Course Catalog page sources, used for parallel processing
    campus_source = lambda x: (requests.get(CAMPUSES[x]).text, x)

    # Dictionary with UW Campus to Department Dictionary mappings
    departments = {}

    # Department Parsing
    with cf.ThreadPoolExecutor() as executor:
        pages = [executor.submit(campus_source, campus.title()) for campus in campuses]
        for f in cf.as_completed(pages):
            # Source -> Page Source for given UW Campus Course Catalog
            source, campus = f.result()
            departments[campus] = {}
            source = BeautifulSoup(source.rsplit('class="col-md-4 uw-sidebar"', 1)[0], features='lxml')
            # College Names at UW i.e. College of Built Environments, College of Engineering, etc...
            college_names = [c.get_text() for c in source.find_all('h2', {'id': re.compile(r'[A-Za-z]+')})]
            colleges = str(source).split('<h2 id=')
            for i, college in enumerate(colleges[1:]):
                departments[campus][college_names[i]] = {}
                college = BeautifulSoup(college, features='lxml')
                # Department Names are found in the anchor tags on the course catalog website
                for dep_name in college.find_all('a'):
                    # There are some non-breaking spaces ('\xa0', encoding='ISO-8859-1') which
                    # are removed through the 'normalize' function
                    dep_name = normalize('NFKD', dep_name.text)
                    try:
                        full_name, abbrev = dep_name.rsplit('(', 1)
                    except ValueError:
                        pass
                    else:
                        if '(' in dep_name and '--' not in dep_name:
                            abbrev = abbrev.replace(' ', '')[:-1]
                            if not abbrev.startswith('See'):
                                departments[campus][college_names[i]][abbrev] = \
                                    full_name.strip()

    if struct == 'df':
        df = pd.DataFrame().from_dict(
            # Flatten dict for DataFrame construction
            # [dn] -> Department Name, [dfull] -> Full Name, [c] -> Campus
            {dep_abb: dep_full for college in departments.values() 
                               for department in college.values()
                               for dep_abb, dep_full in department.items()}, 
            orient='index', columns=['Department Name']
        )
        df.index.name = 'Department'
        df['Campus'] = df['Department Name'].apply(check_campus, args=(departments, 'Campus'))
        df['College'] = df['Department Name'].apply(check_campus, args=(departments, 'College'))
        return df
    elif struct == 'dict':
        if flatten == 'default':
            return departments
        elif flatten == 'college':
            return {cname: dep for college in departments.values() for cname, dep in college.items()}
        elif flatten == 'department':
            return {dep_abb: dep_full for college in departments.values() 
                               for department in college.values()
                               # [dep_abb] -> Abbreviated Department Name
                               # [dep_full] -> Full Department Name
                               for dep_abb, dep_full in department.items()}
        elif flatten == 'campus':
            campus = {}
            # [camp] -> Campus, [col] -> College
            for camp, col in departments.items():
                campus[camp] = {}
                # [dep] -> Department dict
                for dep in col.values():
                    # [dn] -> Abbreviated Department Name
                    # [df] -> Full Department Name
                    for dn, df in dep.items():
                        campus[camp][dn] = df
            return campus
        elif flatten == 'campege':
            return {campus: list(clg.keys()) for campus, clg in departments.items()}
    elif struct == 'list':
        if flatten == 'college':
            return [name for college in departments.values() for name in college.keys()]
        elif flatten == 'dep-abbrev':
            return [dep_abb for college in departments.values() 
                            for col_name in college.values() 
                            for dep_abb in col_name.keys()]
        elif flatten == 'dep-full':
            return [dep_full for college in departments.values() 
                             for col_name in college.values() 
                             for dep_full in col_name.values()]