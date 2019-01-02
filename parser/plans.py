'''Python program to scrape UC San Diego's Plan website for 4-year major plans. Created by Aykan Fonseca.'''

# Builtins
import time

# Pip install packages.
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# Constants
from constants import color, time_taken, time_taken_main, PLANS_URL

COLLEGES = set(['Revelle', 'John Muir', 'Thurgood Marshall',
                'Earl Warren', 'Eleanor Roosevelt', 'Sixth'])


driver = webdriver.PhantomJS()
driver.get(PLANS_URL)


def get_options(web_element):
    """Utility: Returns the options from a dropdown."""

    return [option.text for option in web_element.find_elements_by_tag_name(
        'option') if option.text != '--']


def select_option(web_element, option):
    """Utility: Selects an option in a dropdown."""

    dropdown = Select(web_element)

    dropdown.select_by_visible_text(option)


def verify_selected_option(web_element):
    """Utility: Returns the selected option from a dropdown."""

    return Select(web_element).first_selected_option.text


def get_colleges():
    """Returns a list of all colleges from modal."""

    modal = driver.find_element_by_id("college-select-modal")

    dropdown = modal.find_element_by_tag_name('select')

    return get_options(dropdown)


def select_college(selected_college):
    """Selects a college from modal."""

    modal = driver.find_element_by_id("college-select-modal")

    college_dropdown = modal.find_element_by_tag_name('select')

    select_option(college_dropdown, selected_college)

    button = modal.find_element_by_tag_name('button')

    button.click()

    selected_college = verify_selected_option(college_dropdown)

    if selected_college in COLLEGES:
        print("Selected College: " + selected_college + '\n')
    else:
        print(color.RED + "ERROR: Unknown College Selected." + '\n' + color.END)


@time_taken_main
def main():
    colleges = get_colleges()

    select_college(colleges[0])

    former = driver.find_element_by_tag_name("form")

    year_dropdown = former.find_elements_by_xpath(
        "//div[@class='form-group']")[1].find_element_by_tag_name('select')

    years = get_options(year_dropdown)
    select_option(year_dropdown, years[0])
    print verify_selected_option(year_dropdown)

    department_dropdown = former.find_elements_by_xpath(
        "//div[@class='form-group']")[2].find_element_by_tag_name('select')

    departments = get_options(department_dropdown)
    select_option(department_dropdown, departments[0])
    print verify_selected_option(department_dropdown)

    major_dropdown = former.find_elements_by_xpath(
        "//div[@class='form-group']")[3].find_element_by_tag_name('select')

    majors = get_options(major_dropdown)
    select_option(major_dropdown, majors[0])
    print verify_selected_option(major_dropdown)

    # WebDriverWait(driver, 3)

    time.sleep(5)

    print driver.page_source

    # try:
    #     myElem = WebDriverWait(driver, delay).until(
    #         EC.presence_of_element_located((By.ID, 'IdOfMyElement')))
    #     print "Page is ready!"
    # except TimeoutException:
    #     print "Loading took too much time!"


if __name__ == "__main__":
    main()
