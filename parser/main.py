"""Python program to scrape UC San Diego's Schedule of Classes. Created by Aykan Fonseca."""

# Pip install packages.
from selenium import webdriver
from selenium.webdriver.support.ui import Select
# from selenium.webdriver.common.by import By

# Constants
from constants import SOC_URL, timer, timer_main

driver = webdriver.PhantomJS()
driver.get(SOC_URL)


@timer
def get_departments():
    """
    Description: Gets all the departments listed in the drop down as they are displayed.
    Return Type: List
    """

    departments = driver.find_element_by_id(
        "selectedSubjects").find_elements_by_tag_name("option")

    return [department.text for department in departments]


@timer
def get_department_codes():
    """
    Description: Gets all the department codes listed in drop down. Ex. CSE or ANAR
    Return Type: List
    """

    departments = driver.find_element_by_id(
        "selectedSubjects").find_elements_by_tag_name("option")

    return [department.text.partition(" ")[0] for department in departments]


@timer
def get_quarters():
    """
    Description: Gets all the quarters listed in drop down. Ex. WI19 or FA18
    Return Type: List
    """

    quarters = driver.find_element_by_id(
        "selectedTerm").find_elements_by_tag_name("option")

    return [quarter.get_attribute("value") for quarter in quarters]


def spin():
    button = driver.find_element_by_id("socFacSubmit")
    button.click()

    time.sleep(2)

    html = driver.page_source


@timer_main
def main():
    # print get_departments()
    # print get_quarters()

    dropdown = driver.find_element_by_id("selectedSubjects")

    for option in dropdown.find_elements_by_tag_name("option"):
        Select(dropdown).select_by_visible_text(option.text)

    driver.find_element_by_id("socFacSubmit").submit()

    tr_elements = driver.find_elements_by_tag_name('tr')

    for elem in tr_elements:
        print elem.text
        print '\n'

    for thing in driver.find_elements_by_tag_name("a"):
        print thing.get_attribute("href")


if __name__ == "__main__":
    main()
