#!/usr/bin/env python

import sys
import signal

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup

def sigint(signo, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, sigint)

class Scraper(object):
    def __init__(self):
        self.url = 'http://shop.uofastore.com/courselistbuilder.aspx'
        self.driver = webdriver.PhantomJS()
        self.driver.set_window_size(1120, 550)

    def get_elem(self, xpath):
        elem = self.driver.find_element_by_xpath(xpath)
        return elem

    def get_select(self, xpath):
        select_elem = self.get_elem(xpath)
        select = Select(select_elem)
        return select
        
    def select_dept(self, dept_name):
        '''
        Choose a department from dropdown. Then wait for the
        course list for the chosen dept to load.
        '''
        course_select = self.get_select('//select[@id="clCourseSelectBox"]')
        old_course_id = course_select.options[0].id if len(course_select.options) > 0 else None

        def course_select_updated(driver):
            ''' Once the id has changed, the courses are loaded '''
            new_course_id = course_select.options[0].id if len(course_select.options) > 0 else None
            return old_course_id != new_course_id

        dept_select = self.get_select('//select[@id="clDeptSelectBox"]')
        dept_select.select_by_visible_text(dept_name)
        
        # Now wait for the course list to load
        wait = WebDriverWait(self.driver, 10)
        wait.until(course_select_updated)

    def select_course(self, course_name):
        '''
        Choose a course from dropdown. Then wait for the
        section list for the chosen course to load.
        '''
        section_select = self.get_select('//select[@id="clSectionSelectBox"]')
        old_section_id = section_select.options[0].id if len(section_select.options) > 0 else None

        def section_select_updated(driver):
            ''' Once the id has changed, the sections are loaded '''
            new_section_id = section_select.options[0].id if len(section_select.options) > 0 else None
            return old_section_id != new_section_id

        course_select = self.get_select('//select[@id="clCourseSelectBox"]')
        course_select.select_by_visible_text(course_name)

        # Now wait for the section list to load
        wait = WebDriverWait(self.driver, 10)
        wait.until(section_select_updated)

    def select_section(self, section_name):
        '''
        Choose a section from dropdown. Then wait for the
        Selected Course box to get updated.
        '''
        selected_course_elem = self.get_elem('//div[@id="clSelectedCoursesList"]')
        selected_course_text = selected_course_elem.text

        def selected_courses_updated(driver):
            ''' Once the text has changed, the courses are loaded '''
            return selected_course_text != selected_course_elem.text

        section_select = self.get_select('//select[@id="clSectionSelectBox"]')
        section_select.select_by_visible_text(section_name)

        #
        # Now wait for the course/section to appear in 
        # Selected Courses box
        #
        wait = WebDriverWait(self.driver, 10)
        wait.until(selected_courses_updated)

    def click_choose_books(self):
        xp = '//div[@id="clSelectedCoursesFooter"]/a'
        choose_books_link = self.get_elem(xp)
        choose_books_link.click()

        #
        # See if we've got popup for choosing between new and 
        # used books
        #
        xp = '//iframe[@id="TB_iframeContent"]'
        try:
            iframe = self.get_elem(xp)
        except NoSuchElementException:
            pass
        else:
            # Choose which books may be substituted.
            self.driver.switch_to_frame(iframe)

            radio_button = self.driver.find_element_by_id('ctl00_PageContent_rblSubs_2')
            radio_button.click()

            self.driver.save_screenshot('screenshot-2-modal.png')

            continue_button = self.driver.find_element_by_id('ctl00_PageContent_btnContinue')
            continue_button.click()

            self.driver.switch_to_default_content()

        def iframe_gone(driver):
            try:
                iframe.text
            except StaleElementReferenceException:
                return True
            except:
                pass

            return False

        # Wait for the next page to load
        wait = WebDriverWait(self.driver, 10)
        wait.until(iframe_gone)

    def get_new_books(self):
        '''
        Go through and click 
        '''
        xp = '//tr[@class="product"]'
        books = self.driver.find_elements_by_xpath(xp)

        for book in books:
            css = 'div.booklistvariant > input.new'
            newbook_radio_button = book.find_element_by_css_selector(css)
            newbook_radio_button.click()

            #
            # Select NO for "Allow Substitution"
            # Look for value="1" if you do want a substitution
            #
            css = 'div.subsoptions > fieldset > input[value="0"]'
            no_subs_radio_button = book.find_element_by_css_selector(css)
            no_subs_radio_button.click()

    def click_add_books_to_cart(self):
        add_selected_button = self.driver.find_element_by_id('ctl00_PageContent_btnAddToCart')
        add_selected_button.click()

        # Wait until checkout button appears
        checkout_button_id = 'ctl00_PageContent_ctlCart_btnCheckoutNow'
        wait = WebDriverWait(self.driver, 10)
        wait.until(lambda driver: driver.find_element_by_id(checkout_button_id).is_displayed())

    def scrape(self):
        self.driver.get(self.url)
        
        self.select_dept('ACCT - ACCOUNTING')
        self.select_course('2013')
        self.select_section('1 - Myers')
        self.driver.save_screenshot('screenshot-1-courses-selected.png')
        self.click_choose_books()

        self.get_new_books()
        self.driver.save_screenshot('screenshot-3-books-chosen.png')
        self.click_add_books_to_cart()

        self.driver.save_screenshot('screenshot-4-checkout.png')

if __name__ == '__main__':
    scraper = Scraper()
    scraper.scrape()
