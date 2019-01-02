'''Python program to scrape UC San Diego's Schedule of Classes. Created by Aykan Fonseca.'''

# Builtins
import itertools
import re
import time

# Pip install packages.
from bs4 import BeautifulSoup
from firebase import firebase
import requests
from tqdm import tqdm

# Pip install packages.
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# Global Variables.
SESSION = requests.Session()
NUM_PAGES_TO_PARSE = 0
NUM_COURSES = 0
TIMESTAMP = int(time.strftime("%Y%m%d%H%M")) # A timestamp for the scrape in year-month-day-hour-minute.

# URL to the entire list of classes.
SOC_URL = 'https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm?page='

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'
}

# URL to get the 3 - 4 letter department codes.
SUBJECTS_URL = 'http://blink.ucsd.edu/instructors/courses/schedule-of-classes/subject-codes.html'

# Input data besides classes.
POST_DATA = {
    'loggedIn': 'false', 
    'instructorType': 'begin', 
    'titleType': 'contain',
    'schDay': ['M', 'T', 'W', 'R', 'F', 'S'], 
    'schedOption1': 'true',
    'schedOption2': 'true'
}

CONVERT_RESTRICTIONS = {
    'D': 'Department Approval Required', 
    'ER': 'Open to Eleanor Roosevelt College Students Only',
    'FR': 'Open to Freshmen Only', 
    'GR': 'Open to Graduate Standing', 
    'JR': 'Open to Juniors Only',
    'LD': 'Open to Lower Division Students Only', 
    'MU': 'Open to Muir College Students Only', 
    'O': 'Open to Majors Only (Non-majors require department approval)', 
    'RE': 'Open to Revelle College Students Only',
    'SI': 'Open to Sixth College Students Only', 
    'SO': 'Open to Sophomores Only', 
    'SR': 'Open to Seniors Only',
    'TH': 'Open to Thurgood Marshall College Students Only', 
    'UD': 'Open to Upper Division Students Only',
    'WA': 'Open to Warren College Students Only', 
    'N': 'Not Open to Majors', 
    'XFR': 'Not Open to Freshmen',
    'XGR': 'Not Open to Graduate Standing', 
    'XJR': 'Not Open to Juniors', 
    'XLD': 'Not Open to Lower Division Students',
    'XSO': 'Not Open to Sophomores', 
    'XSR': 'Not Open to Seniors', 
    'XUD': 'Not Open to Upper Division Students'
}

# These contain the minimal semantically-important words in order to combine restrictions.
CONVERT_RESTRICTIONS_MINIMAL = {
    'D': 'Department Approval Required', 
    'ER': 'Eleanor Roosevelt College Students',
    'FR': 'Freshmen', 
    'GR': 'Graduate Standing', 
    'JR': 'Juniors',
    'LD': 'Lower Division Students', 
    'MU': 'Muir College Students', 
    'O': 'Majors (Non-majors require department approval)', 
    'RE': 'Revelle College Students',
    'SI': 'Sixth College Students',
    'SO': 'Sophomores', 
    'SR': 'Seniors',
    'TH': 'Thurgood Marshall College Students', 
    'UD': 'Upper Division Students',
    'WA': 'Warren College Students', 
    'N': 'Majors', 
    'XFR': 'Freshmen',
    'XGR': 'Graduate Standing', 
    'XJR': 'Juniors', 
    'XLD': 'Lower Division Students',
    'XSO': 'Sophomores', 
    'XSR': 'Seniors', 
    'XUD': 'Upper Division Students'
}

ONLY_RESTRICTIONS = set(['ER', 'FR', 'GR', 'JR', 'LD', 'MU', 'O', 'RE', 'SI', 'SO', 'SR', 'TH', 'UD', 'WA'])
NOT_RESTRICTIONS = set(['N', 'XFR', 'XGR', 'XJR', 'XLD', 'XSO', 'XSR', 'XUD'])
SPECIAL_RESTRICTIONS = set(['D', 'ER', 'MU', 'O', 'RE', 'SI', 'TH', 'WA', 'N'])
APPEND_ONLY_RESTRICTIONS = set(['ER', 'MU', 'RE', 'SI', 'TH', 'WA', 'O'])

# Used Custom Sorts. The higher the number, the higher the priority / earlier they appear.
RESTRICTION_RANKS = {'FR': 5, 'XFR': 5, 'SO': 4, 'XSO': 4, 'JR': 3, 'XJR': 3, 'SR': 2, 'XSR': 2, 'GR': 1, 'XGR': 1}
SPECIAL_RANKS = {'D': 2, 'O': 2, 'N': 1, 'ER': 1, 'MU': 1, 'RE': 1, 'SI': 1, 'TH': 1, 'WA': 1}
DAY_RANKS = {'M': 7, 'Tu': 6, 'W': 5, 'Th': 4, 'F': 3, 'S': 2, 'Su': 1}
    

# Meeting Type mappings.
CONVERT_MEETING_TYPES = {
    'AC': 'Activity', 'CL': 'Clinical Clerkship', 'CO': 'Conference',
    'DI': 'Discussion', 'FI': 'Final Exam', 'FM': 'Film',
    'FW': 'Fieldwork', 'IN': 'Independent Study', 'IT': 'Internship',
    'LA': 'Laboratory', 'LE': 'Lecture', 'MI': 'Midterm',
    'MU': 'Make-up Session', 'OT': 'Other Additional Meeting',
    'PB': 'Problem Session', 'PR': 'Practicum', 'RE': 'Review Session', 
    'SE': 'Seminar', 'ST': 'Studio', 'TU': 'Tutorial'
}

# Up to date as of November 28th, 2018.
IS_DEI = set([
    'AAS 10', 'ANAR 117', 'ANBI 131', 'ANSC 113', 'ANSC 122', 
    'ANSC 131', 'ANSC 145', 'ANSC 162', 'ANTH 21', 'ANTH 23', 
    'ANTH 43', 'BILD 60', 'COMM 10', 'COMM 102D', 'COMM 102C', 
    'COMM 155', 'CGS 2A', 'CGS 105', 'CGS 112', 'CGS 119', 'DOC 1',
    'DOC 100D', 'ECON 138', 'EDS 25', 'EDS 112', 'EDS 113', 
    'EDS 117', 'EDS 117 GS', 'EDS 125', 'EDS 126', 'EDS 130',
    'EDS 131', 'EDS 136', 'EDS 137', 'EDS 139', 'ETHN 1',
    'ETHN 2', 'ETHN 3', 'ETHN 1A', 'ETHN 1B', 'ETHN 1C', 'ETHN 20',
    'ETHN 110', 'ETHN 112A', 'ETHN 112B', 'ETHN 124', 'ETHN 127',
    'ETHN 130', 'ETHN 131', 'ETHN 136', 'ETHN 154', 'ETHN 163F', 
    'ETHN 163G', 'ETHN 163J', 'ETHN 178', 'ETHN 179', 'ETHN 182', 
    'ETHN 190', 'HDP 135', 'HDP 115', 'HDP 171', 'HDP 175', 'HILD 7A', 
    'HILD 7B', 'HILD 7C', 'HILD 7GS', 'HITO 136', 'HITO 155', 'HITO 156', 
    'HIUS 103', 'HIUS 108A', 'HIUS 108B', 'HIUS 112', 'HIUS 113', 
    'HIUS 125', 'HIUS 128', 'HIUS 136', 'HIUS 158', 'HIUS 159', 
    'HIUS 167', 'HIUS 180', 'LATI 10', 'LIGN 7', 'LIGN 8', 'LTCS 119', 
    'LTCS 130', 'LTEN 27', 'LTEN 28', 'LTEN 29', 'LTEN 169', 'LTEN 171',
    'LTEN 178', 'LTEN 181', 'LTEN 185', 'LTEN 186', 'MUS 8',
    'MUS 8GS', 'MUS 17', 'MUS 126', 'MUS 127', 'MUS 150',
    'PHIL 35', 'PHIL 155', 'PHIL 165', 'PHIL 170', 'POLI 100H',
    'POLI 100I', 'POLI 100O', 'POLI 100Q', 'POLI 105A', 'POLI 108',
    'POLI 150A', 'MGT 18', 'RELI 148', 'RELI 149', 'SIO 114',
    'SOCI 2', 'SOCI 111', 'SOCI 117', 'SOCI 126', 'SOCI 127',
    'SOCI 138', 'SOCI 139', 'SOCI 151', 'SOCI 153', 'TDGE 127',
    'TDGE 131', 'TDHT 103', 'TDHT 107', 'TDHT 109', 'TDHT 120',
    'USP 3', 'USP 129', 'VIS 152D'
])

FIREBASE_DB = "https://winter-2019-rd.firebaseio.com/"
FIREBASE_DB2 = "https://winter-test-c46cc.firebaseio.com/"

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


def time_taken_main(func):
    '''A decorator function used specifically to time main()'s execution'''

    def wrapper(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print(color.BOLD + color.PURPLE + "### Total Time taken: " + str(end - start) + " seconds" + '\n' + color.END)
        return result

    return wrapper


def time_taken(func):
    '''A decorator function used to time the execution of functions.'''

    def wrapper(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print(color.BOLD + color.GREEN + "- Time taken: " + str(end - start) + " seconds" + '\n' + color.END)
        return result

    return wrapper


def rank_sort(first_restriction_code, second_restriction_code):
    '''Orders restrictions by RESTRICTION_RANKS priority.'''
    rank_a = RESTRICTION_RANKS.get(first_restriction_code, 0)
    rank_b = RESTRICTION_RANKS.get(second_restriction_code, 0)

    if rank_b > rank_a:
        return 1
    elif rank_a > rank_b:
        return -1
    else:
        return 0


def special_sort(first_restriction_code, second_restriction_code):
    '''Orders restrictions by SPECIAL_RANKS priority.'''
    rank_a = SPECIAL_RANKS.get(first_restriction_code, 0)
    rank_b = SPECIAL_RANKS.get(second_restriction_code, 0)

    if rank_b > rank_a:
        return 1
    elif rank_a > rank_b:
        return -1
    else:
        return 0


def day_sort(first_day, second_day):
    day_rank_a = DAY_RANKS.get(first_day, 0)
    day_rank_b = DAY_RANKS.get(second_day, 0)

    if day_rank_b > day_rank_a:
        return 1
    elif day_rank_a > day_rank_b:
        return -1
    else:
        return 0


def convert_to_military(time):
    '''Expected format: 2:00a or 4:50p. Converts to military time.'''

    is_pm = True if time[-1] == 'p' else False
    temp = time[:-1].split(':')

    if is_pm:
        temp[0] = str(int(temp[0]) + 12)

    return ':'.join(temp)


def get_quarters():
    '''Gets all the quarters listed in drop down menu.'''

    quarters = SESSION.get(SOC_URL, headers=HEADERS, stream=True)
    soup = BeautifulSoup(quarters.content, 'lxml').findAll('option')

    return [x['value'] for x in soup if len(x['value']) == 4 and ':' not in x['value']]


def get_subjects():
    '''Gets all the subjects from a seconcary source.'''

    subjects = requests.post(SUBJECTS_URL)
    soup = BeautifulSoup(subjects.content, 'lxml').findAll('td')

    return {'selectedSubjects': [i.text for i in soup if len(i.text) <= 4]}


@time_taken
def setup():
    '''Updates post request with quarter and subjects selected. Also gets NUM_PAGES_TO_PARSE.'''
    
    global NUM_PAGES_TO_PARSE

    print(color.BOLD + color.DARKCYAN + "### 1. Setup ###" + color.END)
    print("- Fetching all quarters.")
    current_quarter = get_quarters()[0]
    POST_DATA.update({'selectedTerm': current_quarter})

    print("- Fetching all subjects.")
    POST_DATA.update(get_subjects())

    print("- Updating post.")
    post = str(SESSION.post(SOC_URL, data=POST_DATA, stream=True).content)
    NUM_PAGES_TO_PARSE = int(re.search(r"of&nbsp;([0-9]*)", post).group(1))

    return POST_DATA['selectedTerm']


@time_taken
def get_data(urls):
    '''Parses the data of all pages in url_page_tuple and returns the raw post data.'''

    # Cache SESSION to avoid calls to global vars.
    s = SESSION
    headers = HEADERS

    print(color.BOLD + color.DARKCYAN + "### 2. Downloading Course Data ###" + color.END)

    tags = []
    for url in tqdm(urls):
        try:
            post = s.get(url, headers=headers)
        except requests.exceptions.HTTPError:
            post = s.get(url, headers=headers)

        tr_tags = BeautifulSoup(post.content, 'lxml').findAll('tr')

        tags.append(tr_tags)

    return tags


@time_taken
def extract_data(posts):

    # Cache NUM_PAGES_TO_PARSE to avoid calls to global vars.
    total_pages = NUM_PAGES_TO_PARSE

    print(color.BOLD + color.DARKCYAN + "### 3. Extracting Relevant Data ###" + color.END)

    raw_data = [] # Contains the parsed page data for each page. 
    teacher_email_map = {} # Maps teachers to their respective emails.

    for tr_tag_elements in posts:
        parsed_page_data = []

        for tr_tag in tr_tag_elements:
            parsed_text = str(" ".join(tr_tag.text.split()).encode('utf_8'))

            # Changes the current department if tr_tag looks like a department header.
            try:
                current_department = str(re.search(r'\((.*?)\)', tr_tag.td.h2.text).group(1))
            except AttributeError:
                pass

            # The header of each class: units, department, course number, etc..
            if 'Units' in parsed_text:
                parsed_page_data.append('NEW_CLASS')

                code = parsed_text.partition(' Prereq')[0]

                parsed_page_data.append(current_department + " " + code)

            # Section and Exam information (and teacher emails).
            else:
                try:
                    tag_class = tr_tag['class'][0]

                    if 'nonenrtxt' == tag_class and any(exam_code in parsed_text for exam_code in ('FI', 'MI')):
                        parsed_page_data.append('****' + parsed_text)
                    elif 'sectxt' == tag_class and 'Cancelled' not in parsed_text:
                        parsed_page_data.append('....' + parsed_text)

                        # Check for teacher email to add to mapping.
                        try:
                            for a_tag in tr_tag.findAll('a'):
                                teacher_email_map[a_tag.text.strip()] = a_tag['href'][7:].strip()
                        except TypeError:
                            pass
                except KeyError:
                    pass
        
        raw_data.append(parsed_page_data)

    return teacher_email_map, raw_data


@time_taken
def format_data(lst):
    '''Format the raw data into a particular format.'''

    global NUM_COURSES

    print(color.BOLD + color.DARKCYAN + "### 4. Filtering Data (delimiter, cancelled, ID) ###" + color.END)

    print("- Flattening list of lists.")
    flattened_list = (item for sublist in lst for item in sublist)

    print("- Regrouping flattened list by delimiter word.")
    regrouped_list = (list(y) for x, y in itertools.groupby(flattened_list, lambda word: word == 'NEW_CLASS') if not x)

    print("- Removing courses that are cancelled.")
    not_cancelled_list = (course for course in regrouped_list if 'Cancelled' not in course)

    print("- Removing courses that don't have a 6-digit idenficiation code.")
    cleaned_list = [course for course in not_cancelled_list if re.findall(r"\D(\d{6})\D", str(course))]

    NUM_COURSES = len(list(cleaned_list))

    print("- Number of courses: " + str(NUM_COURSES) + '.')

    return cleaned_list


def format_restrictions(restrictions):
    '''Converts and formats restrictions text. Ex. JR SR => Open to Juniors and Seniors only.'''
    restriction_codes = restrictions.strip().split(" ")
    num_restrictions = len(restriction_codes)
    set_restrictions = set(restriction_codes)

    if num_restrictions == 1:
        return CONVERT_RESTRICTIONS[restriction_codes[0]] + '.'

    # If we have two, we need to determine if the language is "and" or "or" and whether to include only.
    elif num_restrictions == 2:
        if set_restrictions.issubset(ONLY_RESTRICTIONS):
            return "Open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[0]] + " and " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + ' Only.'
        elif set_restrictions.issubset(NOT_RESTRICTIONS):
            return "Not open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[0]] + " or " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + '.'
        elif 'D' in restriction_codes:
            converted_restrictions = sorted([CONVERT_RESTRICTIONS[code] for code in restriction_codes])
            return converted_restrictions[0] + " and " + converted_restrictions[1] + '.'
        else:
            print("EXCEPTION: MIXTURE of OPEN AND NOT OPEN.")
            print(restriction_codes)
            return restrictions

    # Three and more, we need commas and determine if "and" or "or" and whether to include only.
    else:
        converted_restrictions = sorted([CONVERT_RESTRICTIONS_MINIMAL[code] for code in restriction_codes])
        formatted_restrictions = ''

        # Check to see if we have any special restrictions in our restriction codes. We want those to be displayed first. 
        if not set_restrictions.isdisjoint(SPECIAL_RESTRICTIONS):
            restriction_codes.sort(rank_sort)
            restriction_codes.sort(special_sort)

            if restriction_codes[0] in SPECIAL_RESTRICTIONS:
                formatted_restrictions += CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[0]] + (" Only" if restriction_codes[0] in APPEND_ONLY_RESTRICTIONS else '') + ', and '
                set_restrictions = set(restriction_codes[1:])

                if num_restrictions == 3:
                    if set_restrictions.issubset(ONLY_RESTRICTIONS):
                        formatted_restrictions += "Open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + " and " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[2]] + ' Only.'
                    elif set_restrictions.issubset(NOT_RESTRICTIONS):
                        formatted_restrictions += "Not open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + " or " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[2]] + '.'
                    else:
                        print("EXCEPTION: #1 STRANGE CASE")
                        print(restriction_codes)
                        return restrictions
                else:
                    print("EXCEPTION: #2 STRANGE CASE")
                    print(restriction_codes)
                    return restrictions
            else:
                print("EXCEPTION: #3 STRANGE CASE")
                print(restriction_codes)
                return restrictions

        # Iterate through all except the last, where we apply special formatting to make it semantically-correct.
        elif set_restrictions.issubset(ONLY_RESTRICTIONS):
            restriction_codes.sort(rank_sort)
            
            formatted_restrictions += "Open to "

            for code in restriction_codes[:-1]:
                formatted_restrictions += CONVERT_RESTRICTIONS_MINIMAL[code] + ', '
            
            formatted_restrictions += "and " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[-1]] + ' Only.'

        # Iterate through all except the last, where we apply special formatting to make it semantically-correct.
        elif set_restrictions.issubset(NOT_RESTRICTIONS):
            restriction_codes.sort(rank_sort)

            formatted_restrictions += "Not open to "

            for code in restriction_codes[:-1]:
                formatted_restrictions += CONVERT_RESTRICTIONS_MINIMAL[code] + ', '
            
            formatted_restrictions += "or " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[-1]] + '.'

        else:
            print("EXCEPTION: MIXTURE of OPEN AND NOT OPEN")
            print(restriction_codes)
            return restrictions
        
        return formatted_restrictions


@time_taken
def parse_data(formatted_data):
    '''Parses the courses into their readable values to store in database.'''

    print(color.BOLD + color.DARKCYAN + "### 5. Parsing Data ###" + color.END)

    result = []
    database = firebase.FirebaseApplication(FIREBASE_DB)
    seen_courses = {}
    seen_restrictions = {}
    seen_times = {}

    for course in tqdm(formatted_data):
        # Components of course.
        header, sections, midterm, final = {}, [], {}, {}

        number_regex = re.compile(r'\d+')
        days_regex = re.compile(r'[A-Z][^A-Z]*')

        for item in course:
            # Finds class information.
            if 'Units' in item:
                item = ' '.join(item.split())
                number_location = number_regex.search(item).start()
                temp = item.partition('( ')

                department = item.partition(' ')[0]
                code = item[number_location:].partition(' ')[0]
                proper_code = department + " " + code # Ex. CSE 100.

                if proper_code in seen_courses:
                    header.update(seen_courses[proper_code])
                else:
                    title = temp[0][len(code) + 1 + number_location:-1]
                    header["code"] = proper_code
                    header["units"] = temp[2].partition(')')[0][:-6]
                    header["restrictions"] = "None."

                    # Assign values based on catalog information.
                    catalog_course = database.get("/catalog/" + header['code'], None)

                    try:
                        header["description"] = catalog_course['description']
                        header["prerequisites"] = catalog_course['prerequisites']
                        header["title"] = catalog_course['title']
                    except TypeError:
                        header["description"] = "None given."
                        header["prerequisites"] = "None."
                        header["title"] = title

                    # Assign formatted restrictions if there are any. Use a cache. 
                    if number_location != len(department) + 1:
                        restrictions = item[len(department) + 1: number_location - 1]

                        if restrictions in seen_restrictions:
                            header["restrictions"] = seen_restrictions[restrictions]
                        else:
                            header["restrictions"] = format_restrictions(restrictions)

                    seen_courses[proper_code] = header

            # Section information. We also assign header['is_waitlist'] here.
            elif '....' in item:
                # Assign a default value to all components of a section row.
                section = {'id': '-', 'meeting type': '-', 'number': '-', 'days': '-', 'start time': 'TBA', 'end time': 'TBA', 'building': '-', 'room': '-', 'name': '-', 'seats taken': '-', 'seats available': '-'}

                number_location = number_regex.search(item).start()
                section_line_info = item.split(' ')

                # IDs are the 6 digi unique identification code. Ex: 945848
                if number_location == 4:
                    section["id"] = item[4:10].strip()
                    section_line_info = section_line_info[1:]
                else:
                    section_line_info[0] = section_line_info[0][4:]

                # Meeting type (ex. LE) and section number (ex. A00).
                section["meeting type"] = section_line_info[0]
                section["number"] = section_line_info[1]
                section_line_info = section_line_info[2:]

                # Day. Otherwise, section['days] is in a list: ['M', 'Tu', 'W'] etc.
                if section_line_info[0] != 'TBA':
                    section["days"] = days_regex.findall(section_line_info[0])
                    section["days"].sort(day_sort)
                    section["days"] = ''.join(section["days"])

                    section_line_info = section_line_info[1:]

                # Time. Format is military time, so: 23:50 means 11:50pm. 
                if section_line_info[0] != 'TBA':
                    times = section_line_info[0].partition('-')[::2]

                    # Use a cache.
                    if times[0] in seen_times:
                        section["start time"] = seen_times[times[0]]
                    else:
                        section["start time"] = convert_to_military(times[0])
                        
                    if times[1] in seen_times:
                        section["end time"] = seen_times[times[1]]
                    else:
                        section["end time"] = convert_to_military(times[1])

                    section_line_info = section_line_info[1:]

                # Adjust list because time was given, but not building or room.
                if len(section_line_info) > 1 and (section_line_info[0] == section_line_info[1] == 'TBA'):
                    section_line_info = section_line_info[1:]

                if section_line_info[0] != 'TBA':
                    section["building"] = section_line_info[0]
                    section["room"] = section_line_info[1] 
                    section_line_info = section_line_info[2:]
                
                # Rejoin list so we can extract the name.
                section_line_info = ' '.join(section_line_info)

                try:
                    number_location = number_regex.search(section_line_info).start()
                except AttributeError:
                    number_location = 0
                
                # Handles Name, Seats Taken, and Seats Available.
                # Waitlist Full, the seats taken is the amount over plus the seats available.
                if 'FULL' in section_line_info:
                    # Get the Name
                    seat_info_location = section_line_info.find('FULL')
                    if seat_info_location != 0:
                        if 'Staff' in section_line_info:
                            section["name"] = 'Staff'
                        else:
                            section["name"] = section_line_info[:seat_info_location - 1]
                    
                    # Adjust String.
                    section_line_info = section_line_info[seat_info_location:]

                    # Seat information.
                    left_parens_location = section_line_info.find('(')
                    right_parens_location = section_line_info.find(')')

                    taken = int(section_line_info[left_parens_location + 1:right_parens_location])
                    available = int(section_line_info[right_parens_location + 2:])

                    section["seats taken"] = taken + available
                    section["seats available"] = available

                # Unlimited seats.
                elif 'Unlim' in section_line_info:
                    # Check if "TBA" is first value. If so, ignore.
                    if 'TBA' == section_line_info[0:3]:
                        section_line_info = section_line_info[4:]

                    # Get the Name
                    if 'Staff ' in section_line_info:
                        section["name"] = 'Staff'
                    else:
                        section["name"] = section_line_info[:section_line_info.find('Unlim') - 1]

                    # Seat information. We don't assign to header['is_waitlist'] which already has a default value of false.
                    section["seats taken"] = "Unlimited"
                    section["seats available"] = "Unlimited"

                # Has name and seats. Usual Case.
                elif number_location != 0:
                    # Get the name.
                    section["name"] = section_line_info[:number_location].strip()

                    # Adjust the string.
                    temp2 = section_line_info[number_location:].strip().split(' ')

                    # Seat information.
                    section["seats taken"] = int(temp2[0])
                    section["seats available"] = int(temp2[1])

                # Has name or seats. Unusual Case.
                else:
                    # Name is present. Ex. Gillespie, Gary has a comma. But Staff won't. So we look for either.
                    if ',' in section_line_info or section_line_info.strip() == 'Staff': 
                        section["name"] = section_line_info.strip()
                    
                    # Seat info but no name. Think discussion sections without teacher name. 
                    # Also, rarely, there's a case where there's no number and everything is just "TBA".
                    # Avoid that case by explicitly checking here.
                    elif number_location == 0 and section_line_info and section_line_info != 'TBA':
                        try:
                            temp2 = section_line_info.split(' ')

                            section["seats taken"] = int(temp2[0])
                            section["seats available"] = int(temp2[1])

                        except IndexError:
                            print("ERROR")
                
                # Add section.
                sections.append(section)

            # Finds Final / Midterm Info.
            elif '****' in item:
                # Assign a default value to all components of a exam row.
                exam = {'id': '-', 'meeting type': '-', 'number': '-', 'days': '-', 'start time': 'TBA', 'end time': 'TBA', 'building': '-', 'room': '-', 'name': '-', 'seats taken': '-', 'seats available': '-'}
                exam_line_info = item.split(' ')

                # Section number (ex. A00) and Days (which should only be one day).
                exam["number"] = exam_line_info[1]
                exam["days"] = exam_line_info[2]

                # Building & Room.
                if len(exam_line_info) == 6:
                    exam["building"] = exam_line_info[4]
                    exam["room"] = exam_line_info[5]
                
                # The start and end times.
                if exam_line_info[3] != 'TBA':
                    times = exam_line_info[3].partition('-')[::2]

                    # Use a cache.
                    if times[0] in seen_times:
                        exam["start time"] = seen_times[times[0]]
                    else:
                        exam["start time"] = convert_to_military(times[0])
                        
                    if times[1] in seen_times:
                        exam["end time"] = seen_times[times[1]]
                    else:
                        exam["end time"] = convert_to_military(times[1])
                
                if 'FI' in item:
                    exam["meeting type"] ="FI"
                    final = exam
                else:
                    exam["meeting type"] ="MI"
                    midterm = exam
        
        parsed_result = {
            "sections": sections, "midterm": midterm, "final": final, 
            "seats": (section["seats taken"], section["seats available"])
        }

        parsed_result.update(header)

        result.append(parsed_result)

    return result


@time_taken
def compute_meta_data(parse_data):
    '''Groups courses by code and computes meta data about them like waitlist and seats.'''

    print(color.BOLD + color.DARKCYAN + "### 5. Computing Meta data & Grouping ###" + color.END)

    grouped, seen = {}, {}

    for course in parse_data:
        if course["code"] in seen:
            grouped[course["code"]]["seats"].append(course["seats"])
            grouped[course["code"]]["sections"].append(
                {
                    "section": course["sections"],
                    "midterm": course["midterm"],
                    "final": course["final"]
                }
            )

        else:
            grouped[course["code"]] = {
                "title": course["title"],
                "description": course["description"],
                "prerequisites": course["prerequisites"],
                "restrictions": course["restrictions"],
                "units": course["units"],
                "dei": 'true' if course["code"] in IS_DEI else 'false',
                "seats": [course["seats"]],
                "sections": [
                    { 
                        "section": course["sections"],
                        "midterm": course["midterm"],
                        "final": course["final"]
                    }
                ]
            }
    
    for code, value in grouped.items():
        waitlist = 'false'
        seats_taken = 0
        seats_available = 0

        for (taken, available) in value["seats"]:
            if taken == 'Unlimited' or available == 'Unlimited':
                seats_taken = "Unlimited"
                seats_available = "Unlimited"
                break
            elif taken != '-' or available != '-':
                seats_taken += taken
                seats_available += available
        
        if seats_taken == "Unlimited" or seats_available == "Unlimited" or seats_taken >= seats_available:
            waitlist = 'true'

        # value["seats"] = {TIMESTAMP: (seats_taken, seats_available)}
        value["seats"] = (seats_taken, seats_available)
        value["waitlisted"] = waitlist

    return grouped


@time_taken
def write_to_db(dictionary, quarter):
    """ Adds data to firebase."""

    print(color.BOLD + color.DARKCYAN + "### 6. Writing information to database ###" + color.END)

    database = firebase.FirebaseApplication(FIREBASE_DB2)

    path = "/quarter/" + quarter + "/"

    for key in tqdm(dictionary):
        database.put(path, key, dictionary[key])

    path = "/"

    database.put(path, 'current', quarter)


def spin():
    driver = webdriver.PhantomJS()
    driver.get("https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm")

    dropdown = driver.find_element_by_id("selectedSubjects").
    dropdown_select = Select(dropdown)

    
    options = dropdown.find_elements_by_tag_name("option")

    for option in options:
        dropdown_select.select_by_visible_text(option.text)

    button = driver.find_element_by_id("socFacSubmit")
    button.click()

    time.sleep(4)

    html = driver.page_source

@time_taken_main
def main():
    write_access = False
    download_access = True

    # quarter = setup()

    # page_numbers = range(1, NUM_PAGES_TO_PARSE + 1)
    # page_numbers = range(1, 70)

    # urls = [SOC_URL + str(num) for num in page_numbers]

    NUM_PAGES_TO_PARSE = int(re.search(r"of&nbsp;([0-9]*)", html).group(1))

    # tags = get_data(urls)

    # teacher_email_map, raw_data = extract_data(tags)

    # formatted_data = format_data(raw_data)

    # parsed_data = parse_data(formatted_data)

    # final_data = compute_meta_data(parsed_data)

    # if download_access:
    #     with open("check.txt", "w+") as file:
    #         for k, v in final_data.items():
    #             file.write(str(k))
    #             file.write(str(v))
    #             file.write('\n')
    #             file.write('\n')

    # if write_access:
    #     write_to_db(final_data, quarter)


if __name__ == "__main__":
    main()