"""Python program to scrape UC San Diego's Schedule of Classes. Created by Aykan Fonseca."""

# Builtins
import itertools
import re
import time

# Pip install packages.
from bs4 import BeautifulSoup
from firebase import firebase
import requests
from tqdm import tqdm

# Constants
from constants import color, SOC_URL, SUBJECTS_URL, timer, timer_main, HEADERS, IS_DEI, CONVERT_RESTRICTIONS, CONVERT_RESTRICTIONS_MINIMAL

# Global Variables.
SESSION = requests.Session()
NUM_PAGES_TO_PARSE = 0
NUM_COURSES = 0
TIMESTAMP = int(time.strftime("%Y%m%d%H%M")) # A timestamp for the scrape in year-month-day-hour-minute.

# Input data besides classes.
POST_DATA = {
    "loggedIn": "false", 
    "instructorType": "begin", 
    "titleType": "contain",
    "schDay": ["M", "T", "W", "R", "F", "S"], 
    "schedOption1": "true",
    "schedOption2": "true"
}

ONLY_RESTRICTIONS = set(["ER", "FR", "GR", "JR", "LD", "MU", "O", "RE", "SI", "SO", "SR", "TH", "UD", "WA"])
NOT_RESTRICTIONS = set(["N", "XFR", "XGR", "XJR", "XLD", "XSO", "XSR", "XUD"])
SPECIAL_RESTRICTIONS = set(["D", "ER", "MU", "O", "RE", "SI", "TH", "WA", "N"])
APPEND_ONLY_RESTRICTIONS = set(["ER", "MU", "RE", "SI", "TH", "WA", "O"])

# Used Custom Sorts. The higher the number, the higher the priority / earlier they appear.
RESTRICTION_RANKS = {"FR": 5, "XFR": 5, "SO": 4, "XSO": 4, "JR": 3, "XJR": 3, "SR": 2, "XSR": 2, "GR": 1, "XGR": 1}
SPECIAL_RANKS = {"D": 2, "O": 2, "N": 1, "ER": 1, "MU": 1, "RE": 1, "SI": 1, "TH": 1, "WA": 1}
DAY_RANKS = {"M": 7, "Tu": 6, "W": 5, "Th": 4, "F": 3, "S": 2, "Su": 1}


def rank_sort(first_restriction_code, second_restriction_code):
    """Orders restrictions by RESTRICTION_RANKS priority."""
    rank_a = RESTRICTION_RANKS.get(first_restriction_code, 0)
    rank_b = RESTRICTION_RANKS.get(second_restriction_code, 0)

    if rank_b > rank_a:
        return 1
    elif rank_a > rank_b:
        return -1
    else:
        return 0


def special_sort(first_restriction_code, second_restriction_code):
    """Orders restrictions by SPECIAL_RANKS priority."""
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
    """Expected format: 2:00a or 4:50p. Converts to military time."""

    is_pm = True if time[-1] == "p" else False
    temp = time[:-1].split(":")

    if is_pm:
        temp[0] = str(int(temp[0]) + 12)

    return ":".join(temp)


def get_quarters():
    """Gets all the quarters listed in drop down menu."""

    quarters = SESSION.get(SOC_URL, headers=HEADERS, stream=True)
    soup = BeautifulSoup(quarters.content, "lxml").findAll("option")

    return [x["value"] for x in soup if len(x["value"]) == 4 and ":" not in x["value"]]


def get_subjects():
    """Gets all the subjects from a seconcary source."""

    subjects = requests.post(SUBJECTS_URL)
    soup = BeautifulSoup(subjects.content, "lxml").findAll("td")

    return {"selectedSubjects": [i.text for i in soup if len(i.text) <= 4]}


@timer
def setup():
    """Updates post request with quarter and subjects selected. Also gets NUM_PAGES_TO_PARSE."""
    
    global NUM_PAGES_TO_PARSE

    print(color.BOLD + color.DARKCYAN + "### 1. Setup ###" + color.END)
    print("- Fetching all quarters.")
    current_quarter = get_quarters()[0]
    POST_DATA.update({"selectedTerm": current_quarter})

    print("- Fetching all subjects.")
    POST_DATA.update(get_subjects())

    print("- Updating post.")
    post = str(SESSION.post(SOC_URL, data=POST_DATA, stream=True).content)
    NUM_PAGES_TO_PARSE = int(re.search(r"of&nbsp;([0-9]*)", post).group(1))

    return POST_DATA["selectedTerm"]


@timer
def get_data(urls):
    """Parses the data of all pages in url_page_tuple and returns the raw post data."""

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

        tr_tags = BeautifulSoup(post.content, "lxml").findAll("tr")

        tags.append(tr_tags)

    return tags


@timer
def extract_data(posts):

    # Cache NUM_PAGES_TO_PARSE to avoid calls to global vars.
    total_pages = NUM_PAGES_TO_PARSE

    print(color.BOLD + color.DARKCYAN + "### 3. Extracting Relevant Data ###" + color.END)

    raw_data = [] # Contains the parsed page data for each page. 
    teacher_email_map = {} # Maps teachers to their respective emails.

    for tr_tag_elements in posts:
        parsed_page_data = []

        for tr_tag in tr_tag_elements:
            parsed_text = str(" ".join(tr_tag.text.split()).encode("utf_8"))

            # Changes the current department if tr_tag looks like a department header.
            try:
                current_department = str(re.search(r"\((.*?)\)", tr_tag.td.h2.text).group(1))
            except AttributeError:
                pass

            # The header of each class: units, department, course number, etc..
            if "Units" in parsed_text:
                parsed_page_data.append("NEW_CLASS")

                code = parsed_text.partition(" Prereq")[0]

                parsed_page_data.append(current_department + " " + code)

            # Section and Exam information (and teacher emails).
            else:
                try:
                    tag_class = tr_tag["class"][0]

                    if "nonenrtxt" == tag_class and any(exam_code in parsed_text for exam_code in ("FI", "MI")):
                        parsed_page_data.append("****" + parsed_text)
                    elif "sectxt" == tag_class and "Cancelled" not in parsed_text:
                        parsed_page_data.append("...." + parsed_text)

                        # Check for teacher email to add to mapping.
                        try:
                            for a_tag in tr_tag.findAll("a"):
                                teacher_email_map[a_tag.text.strip()] = a_tag["href"][7:].strip()
                        except TypeError:
                            pass
                except KeyError:
                    pass
        
        raw_data.append(parsed_page_data)

    return teacher_email_map, raw_data


@timer
def format_data(lst):
    """Format the raw data into a particular format."""

    global NUM_COURSES

    print(color.BOLD + color.DARKCYAN + "### 4. Filtering Data (delimiter, cancelled, ID) ###" + color.END)

    print("- Flattening list of lists.")
    flattened_list = (item for sublist in lst for item in sublist)

    print("- Regrouping flattened list by delimiter word.")
    regrouped_list = (list(y) for x, y in itertools.groupby(flattened_list, lambda word: word == "NEW_CLASS") if not x)

    print("- Removing courses that are cancelled.")
    not_cancelled_list = (course for course in regrouped_list if "Cancelled" not in course)

    print("- Removing courses that don't have a 6-digit idenficiation code.")
    cleaned_list = [course for course in not_cancelled_list if re.findall(r"\D(\d{6})\D", str(course))]

    NUM_COURSES = len(list(cleaned_list))

    print("- Number of courses: " + str(NUM_COURSES) + ".")

    return cleaned_list


def format_restrictions(restrictions):
    """Converts and formats restrictions text. Ex. JR SR => Open to Juniors and Seniors only."""
    restriction_codes = restrictions.strip().split(" ")
    num_restrictions = len(restriction_codes)
    set_restrictions = set(restriction_codes)

    if num_restrictions == 1:
        return CONVERT_RESTRICTIONS[restriction_codes[0]] + "."

    # If we have two, we need to determine if the language is "and" or "or" and whether to include only.
    elif num_restrictions == 2:
        if set_restrictions.issubset(ONLY_RESTRICTIONS):
            return "Open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[0]] + " and " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + " Only."
        elif set_restrictions.issubset(NOT_RESTRICTIONS):
            return "Not open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[0]] + " or " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + "."
        elif "D" in restriction_codes:
            converted_restrictions = sorted([CONVERT_RESTRICTIONS[code] for code in restriction_codes])
            return converted_restrictions[0] + " and " + converted_restrictions[1] + "."
        else:
            print("EXCEPTION: MIXTURE of OPEN AND NOT OPEN.")
            print(restriction_codes)
            return restrictions

    # Three and more, we need commas and determine if "and" or "or" and whether to include only.
    else:
        converted_restrictions = sorted([CONVERT_RESTRICTIONS_MINIMAL[code] for code in restriction_codes])
        formatted_restrictions = ""

        # Check to see if we have any special restrictions in our restriction codes. We want those to be displayed first. 
        if not set_restrictions.isdisjoint(SPECIAL_RESTRICTIONS):
            restriction_codes.sort(rank_sort)
            restriction_codes.sort(special_sort)

            if restriction_codes[0] in SPECIAL_RESTRICTIONS:
                formatted_restrictions += CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[0]] + (" Only" if restriction_codes[0] in APPEND_ONLY_RESTRICTIONS else "") + ", and "
                set_restrictions = set(restriction_codes[1:])

                if num_restrictions == 3:
                    if set_restrictions.issubset(ONLY_RESTRICTIONS):
                        formatted_restrictions += "Open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + " and " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[2]] + " Only."
                    elif set_restrictions.issubset(NOT_RESTRICTIONS):
                        formatted_restrictions += "Not open to " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[1]] + " or " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[2]] + "."
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
                formatted_restrictions += CONVERT_RESTRICTIONS_MINIMAL[code] + ", "
            
            formatted_restrictions += "and " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[-1]] + " Only."

        # Iterate through all except the last, where we apply special formatting to make it semantically-correct.
        elif set_restrictions.issubset(NOT_RESTRICTIONS):
            restriction_codes.sort(rank_sort)

            formatted_restrictions += "Not open to "

            for code in restriction_codes[:-1]:
                formatted_restrictions += CONVERT_RESTRICTIONS_MINIMAL[code] + ", "
            
            formatted_restrictions += "or " + CONVERT_RESTRICTIONS_MINIMAL[restriction_codes[-1]] + "."

        else:
            print("EXCEPTION: MIXTURE of OPEN AND NOT OPEN")
            print(restriction_codes)
            return restrictions
        
        return formatted_restrictions


@timer
def parse_data(formatted_data):
    """Parses the courses into their readable values to store in database."""

    print(color.BOLD + color.DARKCYAN + "### 5. Parsing Data ###" + color.END)

    result = []
    database = firebase.FirebaseApplication(FIREBASE_DB)
    seen_courses = {}
    seen_restrictions = {}
    seen_times = {}

    for course in tqdm(formatted_data):
        # Components of course.
        header, sections, midterm, final = {}, [], {}, {}

        number_regex = re.compile(r"\d+")
        days_regex = re.compile(r"[A-Z][^A-Z]*")

        for item in course:
            # Finds class information.
            if "Units" in item:
                item = " ".join(item.split())
                number_location = number_regex.search(item).start()
                temp = item.partition("( ")

                department = item.partition(" ")[0]
                code = item[number_location:].partition(" ")[0]
                proper_code = department + " " + code # Ex. CSE 100.

                if proper_code in seen_courses:
                    header.update(seen_courses[proper_code])
                else:
                    title = temp[0][len(code) + 1 + number_location:-1]
                    header["code"] = proper_code
                    header["units"] = temp[2].partition(")")[0][:-6]
                    header["restrictions"] = "None."

                    # Assign values based on catalog information.
                    catalog_course = database.get("/catalog/" + header["code"], None)

                    try:
                        header["description"] = catalog_course["description"]
                        header["prerequisites"] = catalog_course["prerequisites"]
                        header["title"] = catalog_course["title"]
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

            # Section information. We also assign header["is_waitlist"] here.
            elif "...." in item:
                # Assign a default value to all components of a section row.
                section = {"id": "-", "meeting type": "-", "number": "-", "days": "-", "start time": "TBA", "end time": "TBA", "building": "-", "room": "-", "name": "-", "seats taken": "-", "seats available": "-"}

                number_location = number_regex.search(item).start()
                section_line_info = item.split(" ")

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

                # Day. Otherwise, section["days"] is in a list: ["M", "Tu", "W"] etc.
                if section_line_info[0] != "TBA":
                    section["days"] = days_regex.findall(section_line_info[0])
                    section["days"].sort(day_sort)
                    section["days"] = "".join(section["days"])

                    section_line_info = section_line_info[1:]

                # Time. Format is military time, so: 23:50 means 11:50pm. 
                if section_line_info[0] != "TBA":
                    times = section_line_info[0].partition("-")[::2]

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
                if len(section_line_info) > 1 and (section_line_info[0] == section_line_info[1] == "TBA"):
                    section_line_info = section_line_info[1:]

                if section_line_info[0] != "TBA":
                    section["building"] = section_line_info[0]
                    section["room"] = section_line_info[1] 
                    section_line_info = section_line_info[2:]
                
                # Rejoin list so we can extract the name.
                section_line_info = " ".join(section_line_info)

                try:
                    number_location = number_regex.search(section_line_info).start()
                except AttributeError:
                    number_location = 0
                
                # Handles Name, Seats Taken, and Seats Available.
                # Waitlist Full, the seats taken is the amount over plus the seats available.
                if "FULL" in section_line_info:
                    # Get the Name
                    seat_info_location = section_line_info.find("FULL")
                    if seat_info_location != 0:
                        if "Staff" in section_line_info:
                            section["name"] = "Staff"
                        else:
                            section["name"] = section_line_info[:seat_info_location - 1]
                    
                    # Adjust String.
                    section_line_info = section_line_info[seat_info_location:]

                    # Seat information.
                    left_parens_location = section_line_info.find("(")
                    right_parens_location = section_line_info.find(")")

                    taken = int(section_line_info[left_parens_location + 1:right_parens_location])
                    available = int(section_line_info[right_parens_location + 2:])

                    section["seats taken"] = taken + available
                    section["seats available"] = available

                # Unlimited seats.
                elif "Unlim" in section_line_info:
                    # Check if "TBA" is first value. If so, ignore.
                    if "TBA" == section_line_info[0:3]:
                        section_line_info = section_line_info[4:]

                    # Get the Name
                    if "Staff " in section_line_info:
                        section["name"] = "Staff"
                    else:
                        section["name"] = section_line_info[:section_line_info.find("Unlim") - 1]

                    # Seat information. We don't assign to header["is_waitlist"] which already has a default value of false.
                    section["seats taken"] = "Unlimited"
                    section["seats available"] = "Unlimited"

                # Has name and seats. Usual Case.
                elif number_location != 0:
                    # Get the name.
                    section["name"] = section_line_info[:number_location].strip()

                    # Adjust the string.
                    temp2 = section_line_info[number_location:].strip().split(" ")

                    # Seat information.
                    section["seats taken"] = int(temp2[0])
                    section["seats available"] = int(temp2[1])

                # Has name or seats. Unusual Case.
                else:
                    # Name is present. Ex. Gillespie, Gary has a comma. But Staff won't. So we look for either.
                    if "," in section_line_info or section_line_info.strip() == "Staff": 
                        section["name"] = section_line_info.strip()
                    
                    # Seat info but no name. Think discussion sections without teacher name. 
                    # Also, rarely, there's a case where there's no number and everything is just "TBA".
                    # Avoid that case by explicitly checking here.
                    elif number_location == 0 and section_line_info and section_line_info != "TBA":
                        try:
                            temp2 = section_line_info.split(" ")

                            section["seats taken"] = int(temp2[0])
                            section["seats available"] = int(temp2[1])

                        except IndexError:
                            print("ERROR")
                
                # Add section.
                sections.append(section)

            # Finds Final / Midterm Info.
            elif "****" in item:
                # Assign a default value to all components of a exam row.
                exam = {"id": "-", "meeting type": "-", "number": "-", "days": "-", "start time": "TBA", "end time": "TBA", "building": "-", "room": "-", "name": "-", "seats taken": "-", "seats available": "-"}
                exam_line_info = item.split(" ")

                # Section number (ex. A00) and Days (which should only be one day).
                exam["number"] = exam_line_info[1]
                exam["days"] = exam_line_info[2]

                # Building & Room.
                if len(exam_line_info) == 6:
                    exam["building"] = exam_line_info[4]
                    exam["room"] = exam_line_info[5]
                
                # The start and end times.
                if exam_line_info[3] != "TBA":
                    times = exam_line_info[3].partition("-")[::2]

                    # Use a cache.
                    if times[0] in seen_times:
                        exam["start time"] = seen_times[times[0]]
                    else:
                        exam["start time"] = convert_to_military(times[0])
                        
                    if times[1] in seen_times:
                        exam["end time"] = seen_times[times[1]]
                    else:
                        exam["end time"] = convert_to_military(times[1])
                
                if "FI" in item:
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


@timer
def compute_meta_data(parse_data):
    """Groups courses by code and computes meta data about them like waitlist and seats."""

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
                "dei": "true" if course["code"] in IS_DEI else "false",
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
        waitlist = "false"
        seats_taken = 0
        seats_available = 0

        for (taken, available) in value["seats"]:
            if taken == "Unlimited" or available == "Unlimited":
                seats_taken = "Unlimited"
                seats_available = "Unlimited"
                break
            elif taken != "-" or available != "-":
                seats_taken += taken
                seats_available += available
        
        if seats_taken == "Unlimited" or seats_available == "Unlimited" or seats_taken >= seats_available:
            waitlist = "true"

        # value["seats"] = {TIMESTAMP: (seats_taken, seats_available)}
        value["seats"] = (seats_taken, seats_available)
        value["waitlisted"] = waitlist

    return grouped


@timer
def write_to_db(dictionary, quarter):
    """ Adds data to firebase."""

    print(color.BOLD + color.DARKCYAN + "### 6. Writing information to database ###" + color.END)

    database = firebase.FirebaseApplication(FIREBASE_DB2)

    path = "/quarter/" + quarter + "/"

    for key in tqdm(dictionary):
        database.put(path, key, dictionary[key])

    path = "/"

    database.put(path, "current", quarter)


@timer_main
def main():
    write_access = False
    download_access = True

    quarter = setup()

    page_numbers = range(1, NUM_PAGES_TO_PARSE + 1)
    page_numbers = range(1, 70)

    urls = [SOC_URL + str(num) for num in page_numbers]

    tags = get_data(urls)

    teacher_email_map, raw_data = extract_data(tags)

    formatted_data = format_data(raw_data)

    parsed_data = parse_data(formatted_data)

    final_data = compute_meta_data(parsed_data)

    if download_access:
        with open("check.txt", "w+") as file:
            for k, v in final_data.items():
                file.write(str(k))
                file.write(str(v))
                file.write("\n")
                file.write("\n")

    if write_access:
        write_to_db(final_data, quarter)


if __name__ == "__main__":
    main()