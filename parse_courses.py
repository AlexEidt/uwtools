""" Creates a tsv file containing course data for each UW Campus """

import re, time, json, os, pkgutil, requests
import pandas as pd
from threading import Thread
from zlib import compress, decompress
from pkgutil import get_data
from tqdm import tqdm
from bs4 import BeautifulSoup

CAMPUSES = {   
    'Seattle': 'http://www.washington.edu/students/crscat/',                                                                             
    'Bothell': 'http://www.washington.edu/students/crscatb/',                                                               
    'Tacoma': 'http://www.washington.edu/students/crscatt/'                                 
}                                                                                           

COLUMN_NAMES = ['Campus', 'Department Name', 'Course Number', 'Course Name', 'Credits',
                'Areas of Knowledge', 'Quarters Offered', 'Offered with', 
                'Prerequisites', 'Co-Requisites', 'Description']


def complete_description(description):
    """Replaces all occurances of un-numbered courses in the given course description
    @params
        'description': The course description
    Returns 
        Completed courses in description
    """
    find_all_re = re.compile(r'[A-Z& ]+/[A-Z& ]+/[A-Z& ]+\d+')
    find_one_re = re.compile(r'[A-Z& ]+/[A-Z& ]+\d+')
    find_series_2_re = re.compile(r'[A-Z& ]+\d+, ?\d{3}')
    find_series_3_re = re.compile(r'[A-Z& ]+\d+, ?\d{3}, ?\d{3}')
    course_re = re.compile(r'[A-Z& ]+')
    three_digits = re.compile(r'\d{3}')

    find_all = re.findall(find_all_re, description)
    find_one = re.findall(find_one_re, description)
    
    def remove_in(a, b):
        remove = [y for x in a for y in b if y in x]
        for x in b: a.append(x)
        for x in remove: a.remove(x)
        return a
            
    if find_one:
        find_all = remove_in(find_all, find_one)
        for i, x in enumerate(find_all):
            completed = []
            find_all[i] = x.replace(' ', '')
            number = re.search(three_digits, find_all[i]).group(0)
            for crs in re.findall(course_re, find_all[i]):
                completed.append(f'{crs}{number}')
            description = description.replace(x, '{}{}'.format(' ', '/'.join(completed)), 1)

    find_series_2 = re.findall(find_series_2_re, description)
    find_series_3 = re.findall(find_series_3_re, description)
    find_series_2 = remove_in(find_series_3, find_series_2)
    for i, series in enumerate(find_series_2):
        find_series_2[i] = series.replace(' ', '')
        number = find_series_2[i][-3:]
        depmnt = None
        course_dep = re.search(course_re, find_series_2[i])
        if course_dep: 
            depmnt = course_dep.group(0)
            description = description.replace(series, f'{depmnt}{number}', 1)
    return description


def get_requisites(description, type):
    """Gets the requisite courses for the given course
    @params
        'description': The course description
        'type': Either 'Prerequisite' or 'Co-Requisite'
    Returns 
        The requisite courses. 
        If type='Prerequisite', courses are separated by ';', '/', '&&', and/or ','
    """
    if type not in description:                                                             
        return ''    

    not_offered = re.compile(r'[Nn]ot open to students')
    co_req = re.compile(r'[Cc]o-?[Rr]equisites?')
    no_credit_if_re = re.compile(r'([Cc]annot|[Mm]ay not) be taken for credit if (credit received for|student has taken)?[A-Z& ]+\d{3}')
    mulitple_re = re.compile(r'[A-Z& ]+\d{3}/[A-Z& ]+\d{3}/[A-Z& ]+\d{3} and')
    find_match_re = re.compile(r'([A-Z& ]{2,}\d{3})')  

    description = description.replace(' AND ', ' and ').replace(' OR ', ' or ').replace('; or', '/')
    description = description.replace('and either', ';').replace('and one of', ';')
    description = re.sub(no_credit_if_re, '', description)
    description = not_offered.split(description.split('Offered:')[0].split(type)[1])[0]
    multiple = re.search(mulitple_re, description)
    if multiple:
        description = description.replace(multiple.group(0), f'{multiple.group(0)[:-4]};', 1)
    if 'Prerequisite' in type: description = co_req.split(description)[0]                         
    POI = ',POI' if 'permission' in description.lower() else '' 
    new_result = []
    for course in description.split('(')[0].split(';'):
        if ', and' in course:
            new_result.append(course.replace(',', ';'))     
        else:
            new_result.append(course)
    description = ';'.join(new_result)

    if 'with either' in description:
            with_either = description.split('with either')
            description = '{}&&{}'.format(with_either[0], with_either[1].replace('or', '/'))
    description = description.replace('and', '&&').replace('or', ',')

    def extract(course_option, split_char):
        elements = []
        for next_option in list(filter(('').__ne__, course_option.split(split_char))):
            find_match(next_option, elements)
        return elements

    def find_match(to_match, to_append):
        match = re.search(find_match_re, to_match)
        if match: to_append.append(match.group(0))

    semi_colon = []
    for crs in list(filter(('').__ne__, description.split(';'))):
        comma = []
        for option in list(filter(('').__ne__, crs.split(','))):
            if '/' in option and '&&' not in option:
                comma.append('/'.join(extract(option, '/')))
            elif '/' not in option and '&&' in option:
                comma.append('&&'.join(extract(option, '&&')))
            elif '/' in option and '&&' in option:
                doubleand = ['/'.join(extract(x, '/')) for x in list(filter(('').__ne__, option.split('&&')))]
                comma.append('&&'.join(doubleand))
            else:
                find_match(option, comma) 
        semi_colon.append(','.join(list(filter(('').__ne__, comma))))
    result = ';'.join(list(filter(('').__ne__, semi_colon))).replace(' ', '')
    result = result.strip(',').strip(';').strip('&').replace(';,', ';')
    result = f'{result}{POI}'
    result = re.sub(r'&{3,}', '', result)
    result = ','.join(list(filter(('').__ne__, result.split(','))))
    result = ';'.join(list(filter(('').__ne__, result.split(';'))))
    result = ','.join(list(dict.fromkeys(result.split(',')))).replace(';&&', ';').strip('&')
    result = ';'.join(list(dict.fromkeys(result.split(';'))))
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


def get_offered(description):
    """Gets the quarters the course is offered
    @params
        'description': The course description
    Returns 
        Quarters offered as comma separated list (A, W, Sp, S)
    """
    if 'Offered:' not in description:                                                       
        return ''  
        
    parts_re = re.compile(r'([A-Z& ]+\d+)')
                                                                         
    check_parts = description.split('Offered:')[1]                                         
    parts = check_parts.split(';')[1] if ';' in check_parts else check_parts
    parts = re.sub(parts_re, '', parts)
    result = []
    quarters = ['A', 'W', 'Sp', 'S']
    for quarter in quarters:
        if quarter in parts:
            result.append(quarter)
            parts = parts.replace(quarter, '')
    return ','.join(result)                      


def parse_catalogs(campuses=['Seattle', 'Bothell', 'Tacoma']):
    """Creates a .tsv file for every UW campus
    Returns
        A Tuple. The first element is a pandas DataFrame with the scanned Course Catalogs for
        each UW Campus. The second element is a python dictionary with the department names to
        abbreviations for each UW Campus.
    """
    assert type(campuses) == list, 'Type of "campuses" must be a list'
    print('Scanning the UW Course Catalogs. Parsing usually takes 15-45 seconds...')
    
    total_course_df = pd.DataFrame()
    total_department_dict = {} # Department abbreviations to names for all UW Campuses

    def read_department_courses(course_data, campus):
        """Creates a .tsv file with all the course offered on the given 'campus'
        Initalizes 'departments.json' to include a dictionary of all department
        abbreviations to actual department name for each UW Campus.
        @params
            'course_data': BeautifulSoup object with the department list website for the given 'campus'
            'campus': The campus to get the courses from
        """
        course_re = re.compile(r'[A-Z&]+')
        course_name_re = re.compile(r'[^\(]+')
        credits_re = re.compile(r'(((I&S)|(DIV)|(NW)|(VLPA)|(QSR))[,\s/]?)+')
        credits_num_re = re.compile(r'\([\*,\[\]\.max\d/ \-]+\)')
        offered_jointly_re = re.compile(r'([A-Z& ]+\d+)')

        course_list = []
        parsed_departments = set()
        campus_dict = {}
        for dep_link in course_data.find_all('a'):
            dep_file = dep_link.get('href')
            if dep_file not in parsed_departments and '/' not in dep_file and '.html' in dep_file:
                parsed_departments.add(dep_file)
                department = BeautifulSoup(requests.get(f'{CAMPUSES[campus]}{dep_file}').text, features='lxml')
                for course in department.find_all('a'):
                    course_ID = course.get('name')  
                    if course_ID:
                        course_ID = course_ID.upper()
                        course_title = str(course.find('b').text)
                        # The Course Description
                        description = course.get_text().replace(course_title, '', 1)        
                        instructors = course.find('i')
                        if instructors:
                            description = description.replace(str(instructors.get_text()), '', 1)
                        course_text = complete_description(description.rsplit('View course details in MyPlan', 1)[0])
                        # Department Name i.e 'BIOL'
                        department_name = course_ID[:-3]
                        # Course Number i.e 351
                        course_number = re.sub(course_re, '', course_ID)
                        match_name = re.search(course_name_re, course_title)
                        # Course Name i.e Introduction to Computer Programming I
                        course_name = match_name.group(0).split(course_number, 1)[-1].strip() if match_name else ''
                        match_credit_num = re.search(credits_num_re, course_title)
                        # Number of credits for the course
                        number_credits = match_credit_num.group(0)[1:-1] if match_credit_num else ''
                        match_credit_types = re.search(credits_re, course_title)
                        # Course Credit Types (I&S, DIV, NW, VLPA, QSR, C)
                        course_credit_types = match_credit_types.group(0).strip(',').strip('/').strip() if match_credit_types else ''
                        # Jointly offered course with the given course
                        if 'jointly with' in course_text:                                                   
                            offered_jointly = course_text.rsplit('jointly with ')[-1].split(';')[-1]                                
                            offered_jointly = ','.join(re.findall(offered_jointly_re, course_text)).replace(' ', '') 
                        else:
                            offered_jointly = ''
                        # Quarters the course is offered (A, W, Sp, S)
                        quarters_offered = get_offered(course_text)
                        # Course Prerequisites
                        prerequisites = get_requisites(course_text, 'Prerequisite:')
                        # Course Co-Requisites
                        corequisites = get_requisites(course_text, 'Co-requisite')
                        course_list.append(
                            [campus, department_name, course_number, course_name,
                            number_credits, course_credit_types, quarters_offered,
                            offered_jointly, prerequisites, corequisites, course_text]
                        )
                        department_full_name = dep_link.get_text().rsplit('(', 1)[0].strip()
                        campus_dict[department_name] = department_full_name
        total_department_dict[campus] = campus_dict
        del parsed_departments
        course_df = pd.DataFrame(course_list, columns=COLUMN_NAMES)
        del course_list
        nonlocal total_course_df
        total_course_df = pd.concat([total_course_df, course_df], axis=0, copy=False)
        del course_df

    # Parse all three campuses in parallel for faster run time
    threads = []
    for campus, link in CAMPUSES.items():
        if campus in campuses: 
            threads.append(Thread(target=read_department_courses, name=campus,
                        args=(BeautifulSoup(requests.get(link).text, features='lxml'), campus)))
            threads[-1].start()
    for thread in threads:
        thread.join()

    del threads

    def compress_file(file_name, compressed):
        with open(os.path.normpath(f'{os.getcwd()}/Course_Catalogs/{file_name}'), mode='r') as f:
            with open(os.path.normpath(f'{os.getcwd()}/Course_Catalogs/{compressed}'), mode='wb') as comp:
                comp.write(compress(f.read().encode()))
        os.remove(os.path.normpath(f'{os.getcwd()}/Course_Catalogs/{file_name}'))

    # Create Departments json file
    with open(os.path.normpath(f'{os.getcwd()}/Course_Catalogs/Departments.json'), mode='w') as file:
        json.dump(total_department_dict, file)
    compress_file('Departments.json', 'Departments')

    # Create file with Course Catalog
    total_course_df['Course ID'] = total_course_df['Department Name'] + total_course_df['Course Number']
    total_course_df.set_index('Course ID', inplace=True)
    # Compress File with Course Catalogs
    total_course_df.to_csv(os.path.normpath(f'{os.getcwd()}/Course_Catalogs/Total_Courses.csv'), sep='\t')
    compress_file('Total_Courses.csv', 'Total_Courses')
    return (total_course_df, total_department_dict)


def gather(campuses=['Seattle', 'Bothell', 'Tacoma'], update=False):
    """Gathers the Course Catalogs for the given UW Campuses
    @params:
        'campuses': The Campuses to get the Time Schedules from
        'update': Whether to update the course catalogs by scraping the course catalog
                  website
    Returns
        A pandas DataFrame representing the Course Catalogs
    """
    if update:
        return parse_catalogs(campuses=campuses)
    else:
        course_catalog = str(decompress(get_data(__package__, 'Course_Catalogs/Total_Courses')).decode())
        df = pd.DataFrame([x.split('\t') for x in course_catalog.split('\n')], columns=['Course_ID'] + COLUMN_NAMES)
        df.set_index('Course_ID', inplace=True)
        total = pd.DataFrame()
        for campus in campuses:
            campus_df = df[df['Campus'] == campus]
            total = pd.concat([total, campus_df], axis=0)
        return total


def get_departments(campuses=['Seattle', 'Tacoma', 'Bothell']):
    """Returns the departments at UW for each campus
    @params:
        'campuses': The Campuses to get the departments from
    Returns
        A dictionary with department name abbreviations to full names.
    """
    chosen = {}
    departments = json.loads(decompress(get_data(__package__, 'Course_Catalogs/Departments')))
    for campus in campuses:
        chosen[campus] = departments[campus]
    return chosen


if __name__ == '__main__':
    total = parse_catalogs()
