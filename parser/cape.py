"""Python program to UC San Diego's Course and Professor Evaluations (CAPE). Created by Aykan Fonseca."""

# Builtins
import time

# Pip install packages.
from bs4 import BeautifulSoup
from firebase import firebase
import requests

# Constants
from constants import color, timer, timer_main, FIREBASE_DB, FIREBASE_DB2, CAPE_URL, HEADERS

# Global Variables.
SESSION = requests.Session()


@timer
def fetch_data():
    """Fetches course data from Firebase to use for CAPE fetching."""

    print(color.BOLD + color.DARKCYAN + "### 1. Fetching Data ###" + color.END)

    print("- Fetching current quarter.")
    database = firebase.FirebaseApplication(FIREBASE_DB2)

    current_quarter = database.get("/current/", None)

    courses = database.get("/quarter/" + current_quarter + "/", None)

    for course in courses:
        print courses[course]["sections"]


@timer_main
def main():
    write_access = False

    fetch_data()


if __name__ == "__main__":
    main()
