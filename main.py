# Whatsapp web-scrapper 2021.
import os
import time
import json
import logging
import traceback
import configparser
import pandas as pd
from typing import List
from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
# noinspection PyPep8Naming
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException

# predefined loading times (seconds)
SHORT_TIME_TO_LOAD = 2
MEDIUM_TIME_TO_LOAD = 5
LONG_TIME_TO_LOAD = 10


class Whatsapp_WebScrapper:
    # noinspection PyShadowingNames
    def __init__(self):
        self.__base_url = 'https://web.whatsapp.com/'

    # noinspection PyAttributeOutsideInit,PyShadowingNames
    def load_driver(self, browser: str, binary: str, profile: str):
        """Load the browser driver and open the main page.

        Parameters
        ----------
        browser : str
            Web browser type: firefox/chrome.
        binary : str
            Path where the browser executable is located.
        profile : str
            Path where the browser user profile is located.

        Returns
        -------
        None

        """
        # firefox
        if browser == 'firefox':
            firefox_profile = webdriver.FirefoxProfile(profile)
            self.__driver = webdriver.Firefox(executable_path='drivers/geckodriver.exe', firefox_binary=binary,
                                              firefox_profile=firefox_profile)
        # use chrome by default
        else:
            chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument('start-maximized')
            chrome_options.add_argument(f'user-data-dir={profile}')
            chrome_options.binary_location = binary
            self.__driver = webdriver.Chrome(executable_path='drivers/chromedriver.exe', options=chrome_options)
        # open the main whatsapp page
        # self.__driver.maximize_window()
        self.__driver.get(self.__base_url)

    # noinspection PyShadowingNames
    def search_contact(self, contact_name: str):
        """Search for a user/group in whatsapp.

        Parameters
        ----------
        contact_name : str
            Name of the user or group to search for. It must be identical to how it is saved.

        Returns
        -------
        None

        """
        logging.info(f'Searching in [{contact_name}] to extract messages.')
        # noinspection PyAttributeOutsideInit
        self.__contact_name = contact_name  # make it visible to class
        while True:
            # noinspection PyBroadException
            try:
                # Wait until the search panel is fully loaded in the DOM
                try:
                    WebDriverWait(self.__driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@id='side']/div")))
                except (StaleElementReferenceException, TimeoutException):
                    logging.warning("There wasn't enough time to load the items, trying again.")
                    WebDriverWait(self.__driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@id='side']/div")))

                # find the search bar
                search_panel = self.__driver.find_element_by_xpath("//div[@id='side']/div")
                search_bar = search_panel.find_element_by_xpath(".//div[contains(@class, 'copyable-text') and contains(@class, 'selectable-text')]")
                search_bar.click()
                search_bar.clear()
                search_bar.send_keys(contact_name)

                # Wait until the results are fully loaded in the DOM
                try:
                    WebDriverWait(self.__driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class,'_2Z4DV') and not(contains(@class, '_3mMG5'))]")
                        )
                    )
                except (StaleElementReferenceException, TimeoutException):
                    logging.warning("There wasn't enough time to load the items, trying again.")
                    WebDriverWait(self.__driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class,'_2Z4DV') and not(contains(@class, '_3mMG5'))]")
                        )
                    )

                # get the elements that contains only main classes
                search_pane = self.__driver.find_element_by_id('pane-side')
                contacts_found = search_pane.find_elements_by_xpath(".//div[contains(@class,'_2Z4DV') and not(contains(@class, '_3mMG5'))]")
                # loop the found contacts
                for contact in contacts_found:
                    try:
                        c_attr = contact.find_element_by_xpath(f".//span[@title='{contact_name}']")
                        if c_attr.text == contact_name:
                            c_attr.click()
                            return True
                    except (NoSuchElementException, StaleElementReferenceException):
                        pass
            except Exception:
                logging.error('Something went wrong, check logs for more information.')
                logging.error(traceback.format_exc())

    # noinspection PyBroadException
    def get_messages(self, limit: int = None, last_message: str = None, include_my_user: bool = False) -> pd.DataFrame:
        """Searches for messages from a user/group and returns them in an ordered DataFrame.

        Parameters
        ----------
        limit : int
            Limit the message extraction (always gets the most recent).
            If no value is specified, all messages are returned.
        last_message : str
            Last saved message (scrapping stop point). Messages will only be extracted after this parameter.
            The program will automatically search for this message in the WhatsApp conversation.
        include_my_user : bool
            Indicates if it is required to also extract the own user messages.
            Note that the "last_message" will not care who the message is from and will stop automatically
            until is found.

        Returns
        -------
        pd.DataFrame
            Result DataFrame.

        """
        logging.info(f'Extracting messages for <{self.__contact_name}>')
        # list to save all the messages
        exports = []
        # list to save messages only (used for when there is a starting point)
        _actual_msgs_ = set()
        # loop control
        _found_ = False
        _first_time_click_ = True
        try:
            # Wait until the main panel of messages is loaded
            try:
                WebDriverWait(self.__driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='main']/div[3]")))
            except (StaleElementReferenceException, TimeoutException):
                logging.warning("There wasn't enough time to load the items, trying again.")
                WebDriverWait(self.__driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='main']/div[3]")))
            # loop until text is found
            while not _found_:
                # message board
                message_panel = self.__driver.find_element_by_xpath("//div[@id='main']/div[3]/div/div/div[@class='_11liR']")
                # check if own messages are also required
                if include_my_user:
                    msgs_xpath = ".//div[contains(@class,'GDTQm') and contains(@class,'focusable-list-item') and not(contains(@class, '_397qe'))]"
                # only the inputs (of users, not of the current user)
                else:
                    msgs_xpath = ".//div[contains(@class,'GDTQm') and contains(@class,'message-in') and contains(@class,'focusable-list-item')]"
                    # msgs_xpath = ".//div[contains(@class,'message-in')]" # another valid xpath

                # get messages
                input_msgs = message_panel.find_elements_by_xpath(msgs_xpath)
                # loop only once if there is no starting parameter of the messages
                if last_message is None:
                    _found_ = True
                # loop all messages found
                for container in input_msgs:
                    # initialize variable to save emojis
                    plain_emojis = None
                    # initialize variable to check if message is a reply
                    quoted = None
                    # try to extract the text. If this raise an exception, it means that input is an image or only emojis.
                    try:
                        # ========================================== for text ==========================================
                        msg_meta = container.find_element_by_xpath(".//div[contains(@class, 'copyable-text')]")
                        # metadata of the person who sent the message, example: [07:23, 10/18/2019] John:
                        sender = msg_meta.get_attribute('data-pre-plain-text')
                        # extract the current text you sent
                        text = msg_meta.find_element_by_xpath(".//span[contains(@class, 'selectable-text')]").text
                        # check if the text has emojis, if it has, extract them
                        try:
                            emojis = msg_meta.find_elements_by_xpath(".//img")
                            # noinspection PyShadowingNames
                            plain_emojis = ''.join(emoji.get_attribute('data-plain-text') for emoji in emojis)
                        except Exception:
                            pass
                        # check if the text is a reply of a message
                        try:
                            quoted = msg_meta.find_element_by_xpath(".//span[contains(@class, 'quoted-mention')]").text
                        except Exception:
                            pass
                    # image and emoji verification
                    except NoSuchElementException:
                        # ================================ only emojis (without texts) =================================
                        try:
                            msg_meta = container.find_element_by_xpath(".//div[contains(@class, 'copyable-text')]")
                            sender = msg_meta.get_attribute('data-pre-plain-text')
                            emojis = msg_meta.find_elements_by_xpath(".//img")
                            # noinspection PyShadowingNames
                            text = ''.join(emoji.get_attribute('data-plain-text') for emoji in emojis)
                            # populate emojis with text's value
                            plain_emojis = text
                            # check if the text is a reply of a message
                            try:
                                quoted = msg_meta.find_element_by_xpath(".//span[contains(@class, 'quoted-mention')]").text
                            except Exception:
                                pass
                        # ================================ only images (without text) ==================================
                        except NoSuchElementException:
                            # ===== for images =====
                            try:
                                img_src = container.find_element_by_xpath(".//img").get_attribute('src')
                                if img_src.startswith('data:') or img_src.startswith('blob:'):
                                    continue
                                continue
                            except NoSuchElementException:
                                continue

                    # check if last_message is passed
                    if last_message is not None:
                        if text == last_message:
                            _found_ = True

                    # put all messages and emojis that have not yet been added
                    if text not in _actual_msgs_:
                        _actual_msgs_.add(text)
                        # save to array to export
                        # logging.info(f'|{text}|  ==>  |{last_message}|')
                        exports.append(self.__clean_meta(sender) + [text, plain_emojis, quoted])

                # click on any element to activate window (as long as the target text was not found)
                if _first_time_click_ and not _found_:
                    self.__driver.find_element_by_xpath("//body").click()
                    _first_time_click_ = False
                # scroll (as long as the target text was not found)
                if not _found_:
                    self.__scroll(direction='up')
                    # self.__scroll(direction='up')
                    # time to load all new messages
                    time.sleep(SHORT_TIME_TO_LOAD)
            # sort df
            exports = self.__order_data(data=exports)
            if last_message is not None:
                # check if the last record is equal to the message.
                # if this is true, it means that there are no new messages to extract.
                if exports.iloc[-1]['Message'] == last_message:
                    logging.info('No new messages to extract were found.')
                    return pd.DataFrame()
                else:
                    # get the position where our last saved record is located
                    partitioner = exports[exports['Message'] == last_message].index.values.astype(int)[0]
                    # partition
                    exports = exports[partitioner + 1:]
            logging.info('All messages have been extracted successfully.')
            # check if you need to limit the size of messages
            return exports[-limit:] if limit is not None else exports
        except Exception:
            logging.error(
                f'An error occurred while extracting messages from group/user <{self.__contact_name}>, please check logs.')
            logging.error(traceback.format_exc())


    @staticmethod
    def __order_data(data: List) -> pd.DataFrame:
        """Converts a list to DataFrame and sorts it.

        Parameters
        ----------
        data : List
            List of extracted data.

        Returns
        -------
        pd.DataFrame
            Sorted pandas list.

        """
        df = pd.DataFrame(data, columns=['Date', 'Hour', 'User', 'Message', 'Emojis', 'Quoted_Message'])
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df.sort_values(by=['Date', 'Hour'], ascending=[True, True], inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    # noinspection PyShadowingNames
    @staticmethod
    def __clean_meta(sender: str) -> List:
        """Clean and extract metadata from a message.

        Parameters
        ----------
        sender : str
            Metadata of the user who sends the message (time, date and username).
            Input example: [07:23, 10/18/2019] John:

        Returns
        -------
        List
            List with clean metadata.

        """
        # remove special characters
        sender = sender.translate({ord(c): '' for c in "[],"})
        # split
        sender = sender.split()
        hour = sender[0].lstrip().rstrip()
        date = sender[1].lstrip().rstrip()
        user = sender[2].lstrip().rstrip()[:-1]
        # return spliced data
        return [date, hour, user]


    def __scroll(self, direction: str):
        """Scroll up or down.

        Parameters
        ----------
        direction : str
            Indicates where to scroll. 'up' or 'down'.

        Returns
        -------
        None

        """
        if direction == 'up':
            scroll_direction = Keys.PAGE_UP
        else:
            scroll_direction = Keys.PAGE_DOWN
        # execute scroll
        self.__driver.find_element_by_tag_name('html').send_keys(scroll_direction)


def initialize_logger(level: logging = logging.INFO, stream_handler: bool = False):
    """Initialize a new logger.

    Parameters
    ----------
    level : logging.Types
        Type of logging (INFO, WARNING, ERROR, CRITICAL). Default: INFO.
    stream_handler : bool
        Indicates if a stream handler is required for logging.

    Returns
    -------
    None

    """
    if not os.path.exists('logs'):
        os.mkdir('logs')
    # initialize new logger
    new_logger = logging.getLogger()
    # New file handler for physical files
    fileHandler = logging.FileHandler(f'logs/wa_webscrapper {str(date.today())}.log', mode='a')
    # logs formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(formatter)
    # Configure the logger
    new_logger.setLevel(level)
    new_logger.addHandler(fileHandler)
    # check if the user requires a streamHandler
    if stream_handler:
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        new_logger.addHandler(streamHandler)
    new_logger.info('=' * 100)
    new_logger.info('Initialized log.')


def export_df(df: pd.DataFrame, base_name: str):
    """Export a DataFrame to csv.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to export.
    base_name : str
        Document's base name. It is recommended to use the name of the whatsapp group or user.

    Returns
    -------
    None

    """
    try:
        if not df.empty:
            if not os.path.exists('data'):
                os.mkdir('data')
            df.to_csv(f"data/{base_name} {datetime.now().strftime('%Y-%m-%d %H.%M.%S')}.csv", index=False)
    except AttributeError:
        logging.error('The information could not be exported, check the logs.')
        logging.error(traceback.format_exc())


if __name__ == '__main__':
    # initialize logger
    initialize_logger(stream_handler=True)
    # load settings
    config = configparser.ConfigParser()
    config.read('settings.conf')
    browser = config['BROWSER']['browser']
    browser_binary = config['BROWSER']['binary']
    browser_profile = config['BROWSER']['profile_path']
    # load contacts to search
    contacts = json.load(open('contacts.json', encoding='utf-8'))

    # start scrapper
    logging.info('Starting WhatsApp Web..')
    whatsapp = Whatsapp_WebScrapper()
    whatsapp.load_driver(browser=browser, binary=browser_binary, profile=browser_profile)
    # mini pause
    time.sleep(3)

    # loop all contacts
    for contact, attributes in contacts.items():
        # search contact
        whatsapp.search_contact(contact_name=contact)
        # get all messages
        messages = whatsapp.get_messages(last_message=attributes['last_message'])
        # export
        export_df(df=messages, base_name=contact)
        # update the configuration json
        if not messages.empty:
            contacts[contact]['last_message'] = messages.iloc[-1]['Message']
        # search time
        time.sleep(MEDIUM_TIME_TO_LOAD)

# .
