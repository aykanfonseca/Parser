'''Python program to UC San Diego's Course and Professor Evaluations (CAPE). Created by Aykan Fonseca.'''

# Builtins
import time

# Pip install packages.
from bs4 import BeautifulSoup
from firebase import firebase
import requests

# Global Variables.
SESSION = requests.Session()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT'
}

# CAPE url used to scrape data from.
CAPE_URL = 'http://cape.ucsd.edu/responses/Results.aspx?'

# FIREBASE_DB = "https://winter-2019-rd.firebaseio.com/"
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


@time_taken
def fetch_data():
    """Fetches course data from Firebase to use for CAPE fetching."""

    print(color.BOLD + color.DARKCYAN + "### 1. Fetching Data ###" + color.END)

    print("- Fetching current quarter.")
    database = firebase.FirebaseApplication(FIREBASE_DB2)

    current_quarter = database.get("/current/", None)

    courses = database.get("/quarter/" + current_quarter + "/", None)

    for course in courses:
        print courses[course]['sections']


@time_taken_main
def main():
    write_access = False

    fetch_data()


if __name__ == "__main__":
    main()
