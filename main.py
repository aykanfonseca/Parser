'''Python program to scrape UC San Diego's Schedule of Classes. Created by Aykan Fonseca.'''

# Pip install packages.
from selenium import webdriver
# from selenium.webdriver.common.by import By

# Constants
from constants import SOC_URL, time_taken, time_taken_main

driver = webdriver.PhantomJS()
driver.get(SOC_URL)


@time_taken
def get_departments():
    """
    Description: Gets all the departments listed in the drop down as they are displayed.
    Return Type: List
    """

    departments = driver.find_element_by_id(
        "selectedSubjects").find_elements_by_tag_name("option")

    return [department.text for department in departments]


@time_taken
def get_department_codes():
    """
    Description: Gets all the department codes listed in drop down. Ex. CSE or ANAR
    Return Type: List
    """

    departments = driver.find_element_by_id(
        "selectedSubjects").find_elements_by_tag_name("option")

    return [department.text.partition(' ')[0] for department in departments]


@time_taken
def get_quarters():
    """
    Description: Gets all the quarters listed in drop down. Ex. WI19 or FA18
    Return Type: List
    """

    quarters = driver.find_element_by_id(
        "selectedTerm").find_elements_by_tag_name("option")

    return [quarter.get_attribute('value') for quarter in quarters]


def spin():
    button = driver.find_element_by_id("socFacSubmit")
    button.click()

    time.sleep(2)

    html = driver.page_source


@time_taken_main
def main():
    print get_departments()
    print get_quarters()


if __name__ == "__main__":
    main()
