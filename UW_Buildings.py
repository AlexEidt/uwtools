"""Parses UW's Facilities Websites to get all Building Names"""

import re, json, logging, os, requests
from bs4 import BeautifulSoup
from zlib import compress, decompress
from pkgutil import get_data

def seattle():
    """Parses UW's Facilities to get all Building Names for UW Seattle Campus
    Returns
        Dictionary with Building Name Abbreviations to full Building Names"""
    buildings_dict = {}
    # Get UW Seattle Dorm Building Abbreviations and Names
    uw_dorms = BeautifulSoup(requests.get('https://hfs.uw.edu/Live/Undergraduate-Residence-Halls-and-Apartments').text, 
                        features='lxml')
    for img in uw_dorms.find_all('img'):
        dorm_name = str(img).rsplit('alt="', 1)[-1].split('"', 1)[0]
        if 'Hall' in dorm_name:
            dorm_site = BeautifulSoup(requests.get(f'https://www.google.dz/search?q=http://www.washington.edu/maps UW {dorm_name}').text, 
                                    features='lxml').find('html')
            match = re.search(r'\([A-Z]{3,}\)\s?((\</div\>)|(\s?\| Campus Maps))', str(dorm_site))
            if match:
                dorm_abb = re.search(r'\([A-Z]{3,}\)', match.group(0)).group(0)[1:-1]
                if dorm_abb not in buildings_dict:
                    buildings_dict[dorm_abb] = dorm_name

    # Get UW Seattle Classroom Building Abbreviations and Names
    uw_classrooms = BeautifulSoup(requests.get('https://www.washington.edu/classroom/').text, 
                                features='lxml')
    uw_classrooms = uw_classrooms.find("div", {"id": "buildings"})
    for link in uw_classrooms.find_all('a'):
        if link.get('href') not in buildings_dict:
            buildings_dict[link.get('href')] = link.text.rsplit('(', 1)[0].strip()
        
    # Supplement previous UW Building scrape with additional data
    buildings = BeautifulSoup(requests.get('https://www.washington.edu/students/reg/buildings.html').text,
                            features='lxml')
    buildings = str(buildings.html).split('<h2>Code - Building Name (Map Grid)</h2>', 1)[-1]
    buildings = BeautifulSoup(buildings.rsplit('<div class="uw-footer">', 1)[0], features='lxml')
    for building_group in buildings.find_all('p'):
        for building in str(building_group).split('<br/>'):
            if 'a href' in building:
                building = BeautifulSoup(building, features='lxml')
                abbreviation = building.find('code').text
                name = building.find('a').text
                if abbreviation not in buildings_dict:
                    buildings_dict[abbreviation] = name.split('\n', 1)[0].strip()
    return buildings_dict


def bothell():
    """Parses UW's Facilities to get all Building Names for UW Bothell Campus
    Returns
        Dictionary with Building Name Abbreviations to full Building Names"""
    buildings = {}
    bothell_buildings = BeautifulSoup(requests.get('https://www.uwb.edu/safety/hours').text, features='lxml')
    for building in bothell_buildings.find_all('div', {'class': ['col1', 'col2', 'col3']}):
        bld = str(building.find('h3'))
        if bld and '(' in bld:
            abbreviation = bld.rsplit('(', 1)[-1].split(')')[0]
            name = bld.rsplit('(', 1)[0].strip()
            buildings[abbreviation] = name.replace('<h3>', '').replace('&amp;', '&')
    return buildings


def tacoma():
    """Parses UW's Facilities to get all Building Names for UW Seattle Campus
    Returns
        Dictionary with Building Name Abbreviations to full Building Names"""
    buildings = {}
    tacoma_buildings = BeautifulSoup(requests.get('https://www.tacoma.uw.edu/campus-map/buildings').text, 
                                features='lxml')
    for building in tacoma_buildings.find('div', class_='field-items').find('ul').find_all('a'):
        text = building.text
        if '(' in text:
            abbreviation = text.rsplit('(', 1)[-1].split(')')[0]
            name = text.rsplit('(', 1)[0].strip()
            buildings[abbreviation] = name
        else:
            link = BeautifulSoup(requests.get('https://www.tacoma.uw.edu{}'.format(str(building.get('href')))).text,
                                            features='lxml')
            for table in link.find_all('table'):
                for l in table.find_all('a'):
                    if re.search(r'[A-Z]{2,} \d+', l.text):
                        buildings[str(l.text).split(' ', 1)[0].upper()] = text
                        break
    return buildings


def main(campuses=['Seattle', 'Bothell', 'Tacoma']):
    print('Scanning UW Buildings...')
    buildings = {}
    functions = {
        'Seattle': seattle,
        'Bothell': bothell,
        'Tacoma': tacoma
    }
    for campus in campuses:
        buildings[campus] = functions[campus]()
    return buildings


def get_buildings(campuses=['Seattle', 'Bothell', 'Tacoma'], update=False):
    """Returns the Buildings at UW for each campus
    @params:
        'campuses': The Campuses to get the Buildings from
        'update': Whether to update the buildings by scraping the buildings
                  website
    Returns
        A dictionary with building name abbreviations to full names.
    """
    if update:
        return main(campuses=campuses)
    else:
        chosen = {}
        buildings = json.loads(decompress(get_data(__package__, 'Building_Data/UW_Buildings')))
        for campus in campuses:
            chosen[campus] = buildings[campus]
        return chosen


def geocode(buildings=[], campuses=['Seattle', 'Bothell', 'Tacoma']):
    """Geocodes UW Buildings
    @params:
        'buildings': List of buildings to geocode
        'campuses': Campuses to get building coordinates from
    Returns
        A dictionary with data for each building in the buildings list
    """
    coordinates = json.loads(decompress(get_data(__package__, 'Building_Data/Coordinates')))
    all_campuses = {}
    for campus, buildings_ in coordinates.items():
        if campus in campuses:
            for building, coords in buildings_.items():
                if building in buildings or len(buildings) == 0:
                    all_campuses[building] = coords
    return all_campuses


def check_campus(building):
    """Checks which campus a building is on
    @params
        'building': The building to check
    Returns
        The campus the building is on. If no campus is found, returns None.
    """
    coordinates = json.loads(decompress(get_data(__package__, 'Building_Data/Coordinates')))
    for campus, buildings in coordinates.items():
        if building in buildings:
            return campus
    return None

    



if __name__ == '__main__':
    main()

