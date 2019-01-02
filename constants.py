'''Python file used to hold common constants and settings. Created by Aykan Fonseca.'''

import time

# Databases
FIREBASE_DB = "https://winter-2019-rd.firebaseio.com/"
FIREBASE_DB2 = "https://winter-test-c46cc.firebaseio.com/"

# URLS
SOC_URL = "https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm?page="
CAPE_URL = "http://cape.ucsd.edu/responses/Results.aspx?"
PLANS_URL = "https://plans.ucsd.edu"
SUBJECTS_URL = "http://blink.ucsd.edu/instructors/courses/schedule-of-classes/subject-codes.html"


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

# Timing


def time_taken_main(func):
    '''A decorator function used specifically to time main()'s execution'''

    def wrapper(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print(color.BOLD + color.PURPLE + "### Total Time taken: " +
              str(end - start) + " seconds" + '\n' + color.END)
        return result

    return wrapper


def time_taken(func):
    '''A decorator function used to time the execution of functions.'''

    def wrapper(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print(color.BOLD + color.GREEN + "- Time taken: " +
              str(end - start) + " seconds" + '\n' + color.END)
        return result

    return wrapper


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'
}

# Convert methods & DEI-checking.

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

CONVERT_MEETING_TYPES = {
    'AC': 'Activity', 'CL': 'Clinical Clerkship', 'CO': 'Conference',
    'DI': 'Discussion', 'FI': 'Final Exam', 'FM': 'Film',
    'FW': 'Fieldwork', 'IN': 'Independent Study', 'IT': 'Internship',
    'LA': 'Laboratory', 'LE': 'Lecture', 'MI': 'Midterm',
    'MU': 'Make-up Session', 'OT': 'Other Additional Meeting',
    'PB': 'Problem Session', 'PR': 'Practicum', 'RE': 'Review Session',
    'SE': 'Seminar', 'ST': 'Studio', 'TU': 'Tutorial'
}
