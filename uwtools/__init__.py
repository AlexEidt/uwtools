

from .parse_courses import parse_catalogs as course_catalogs
from .parse_courses import get_departments as departments

from .parse_schedules import gather as time_schedules
from .parse_schedules import get_academic_year as academic_year

from .parse_buildings import get_buildings as buildings
from .parse_buildings import geocode