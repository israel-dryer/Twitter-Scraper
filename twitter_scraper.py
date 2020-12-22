"""
    TITLE:
        A simple search-based twitter scraper

    LAST MODIFIED:
        2020-12-21

    AUTHOR:
        Israel Dryer
        israel.dryer@gmail.com

    This is not a perfect scraper, so feel free to add improvements if you find any.

    IMPROVEMENTS:
    - Improved error handling so that tweets are not rejected if certain fields are null, etc...
    - Leveraged the `WebDriverAwait` class to enable better detection of desired load states
    - Each record is saved while scraping instead of all at the end; minimizing data loss for a failed session.

    NOTES AND THINGS TO THINK ABOUT:
    - Twitter will block you from logging (temporary) in via the webdriver if you log in too many times in a single day.

    - The `scroll_down_page` function has an argument for `num_seconds_to_load` that represents the num of
    seconds that the program will wait until attempting to scroll again. I'm currently making 5 attempts with
    a pause between. You could also increase the number of max attempts and decrease the `num_seconds_to_load`.
    This could possibly speed up the scraping as you would be more likely to get to a successfull scroll down
    quicker.

    -  The `collect_all_tweets_from_current_view` function has a `lookback_limit` argument that controls how
    many tweets are processed from each scroll. I've written more about this in the function docstring.

    - I've implemented `WebDriverWait` in several sections of this updated code. I think this is a much
    better solution than a hard-coded `sleep` call because it will only timeout after a certain period of
    time if specific conditions are not met. There are many other sections of this code that could be
    improved, I'm sure, by leveraging this class.

    - Feel free to replace the `save_tweet_data_to_csv` function with any other `io` option you want, such
    as a database save via `pyodbc`, `sqlite3`, or whatever you want really.

    - I encourage you to explore the "Advanced Search" functionality. Try adding your criteria and see how the url
     is built. You can then leverage this to make your searches more customized... with date ranges, special keywords,
     etc...  --> https://twitter.com/search-advanced?
"""
import csv
from time import sleep
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions


def create_webdriver_instance():
    options = EdgeOptions()
    options.use_chromium = True
    driver = Edge(options=options)
    return driver


def login_to_twitter(username, password, driver):
    url = 'https://twitter.com/login'
    try:
        driver.get(url)
        xpath_username = '//input[@name="session[username_or_email]"]'
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_username)))
        uid_input = driver.find_element_by_xpath(xpath_username)
        uid_input.send_keys(username)
    except exceptions.TimeoutException:
        print("Timeout while waiting for Login screen")
        return False

    pwd_input = driver.find_element_by_xpath('//input[@name="session[password]"]')
    pwd_input.send_keys(password)
    try:
        pwd_input.send_keys(Keys.RETURN)
        url = "https://twitter.com/home"
        WebDriverWait(driver, 10).until(expected_conditions.url_to_be(url))
    except exceptions.TimeoutException:
        print("Timeout while waiting for home screen")
    return True


def find_search_input_and_enter_criteria(search_term, driver):
    xpath_search = '//input[@aria-label="Search query"]'
    search_input = driver.find_element_by_xpath(xpath_search)
    search_input.send_keys(search_term)
    search_input.send_keys(Keys.RETURN)
    return True


def change_page_sort(tab_name, driver):
    """Options for this program are `Latest` and `Top`"""
    tab = driver.find_element_by_link_text(tab_name)
    tab.click()
    xpath_tab_state = f'//a[contains(text(),\"{tab_name}\") and @aria-selected=\"true\"]'


def generate_tweet_id(tweet):
    return ''.join(tweet)


def scroll_down_page(driver, last_position, num_seconds_to_load=0.5, scroll_attempt=0, max_attempts=5):
    """The function will try to scroll down the page and will check the current
    and last positions as an indicator. If the current and last positions are the same after `max_attempts`
    the assumption is that the end of the scroll region has been reached and the `end_of_scroll_region`
    flag will be returned as `True`"""
    end_of_scroll_region = False
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(num_seconds_to_load)
    curr_position = driver.execute_script("return window.pageYOffset;")
    if curr_position == last_position:
        if scroll_attempt < max_attempts:
            end_of_scroll_region = True
        else:
            scroll_down_page(last_position, curr_position, scroll_attempt + 1)
    last_position = curr_position
    return last_position, end_of_scroll_region


def save_tweet_data_to_csv(records, filepath, mode='a+'):
    header = ['User', 'Handle', 'PostDate', 'TweetText', 'ReplyCount', 'RetweetCount', 'LikeCount']
    with open(filepath, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(header)
        if records:
            writer.writerow(records)


def collect_all_tweets_from_current_view(driver, lookback_limit=25):
    """The page is continously loaded, so as you scroll down the number of tweets returned by this function will
     continue to grow. To limit the risk of 're-processing' the same tweet over and over again, you can set the
     `lookback_limit` to only process the last `x` number of tweets extracted from the page in each iteration.
     You may need to play around with this number to get something that works for you. I've set the default
     based on my computer settings and internet speed, etc..."""
    page_cards = driver.find_elements_by_xpath('//div[@data-testid="tweet"]')
    if len(page_cards) <= lookback_limit:
        return page_cards
    else:
        return page_cards[-lookback_limit:]


def extract_data_from_current_tweet_card(card):
    try:
        user = card.find_element_by_xpath('.//span').text
    except exceptions.NoSuchElementException:
        user = ""
    except exceptions.StaleElementReferenceException:
        return
    try:
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    except exceptions.NoSuchElementException:
        handle = ""
    try:
        """
        If there is no post date here, there it is usually sponsored content, or some
        other form of content where post dates do not apply. You can set a default value
        for the postdate on Exception if you which to keep this record. By default I am
        excluding these.
        """
        postdate = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except exceptions.NoSuchElementException:
        return
    try:
        _comment = card.find_element_by_xpath('.//div[2]/div[2]/div[1]').text
    except exceptions.NoSuchElementException:
        _comment = ""
    try:
        _responding = card.find_element_by_xpath('.//div[2]/div[2]/div[2]').text
    except exceptions.NoSuchElementException:
        _responding = ""
    tweet_text = _comment + _responding
    try:
        reply_count = card.find_element_by_xpath('.//div[@data-testid="reply"]').text
    except exceptions.NoSuchElementException:
        reply_count = ""
    try:
        retweet_count = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text
    except exceptions.NoSuchElementException:
        retweet_count = ""
    try:
        like_count = card.find_element_by_xpath('.//div[@data-testid="like"]').text
    except exceptions.NoSuchElementException:
        like_count = ""

    tweet = (user, handle, postdate, tweet_text, reply_count, retweet_count, like_count)
    return tweet


def main(username, password, search_term, filepath, page_sort='Latest'):
    save_tweet_data_to_csv(None, filepath, 'w')  # create file for saving records
    last_position = None
    end_of_scroll_region = False
    unique_tweets = set()

    driver = create_webdriver_instance()
    logged_in = login_to_twitter(username, password, driver)
    if not logged_in:
        return

    search_found = find_search_input_and_enter_criteria(search_term, driver)
    if not search_found:
        return

    change_page_sort(page_sort, driver)

    while not end_of_scroll_region:
        cards = collect_all_tweets_from_current_view(driver)
        for card in cards:
            try:
                tweet = extract_data_from_current_tweet_card(card)
            except exceptions.StaleElementReferenceException:
                continue
            if not tweet:
                continue
            tweet_id = generate_tweet_id(tweet)
            if tweet_id not in unique_tweets:
                unique_tweets.add(tweet_id)
                save_tweet_data_to_csv(tweet, filepath)
        last_position, end_of_scroll_region = scroll_down_page(driver, last_position)
    driver.quit()


if __name__ == '__main__':
    usr = "email@gmail.com"
    pwd = "password"
    path = 'pysimplegui.csv'
    term = 'pysimplegui'

    main(usr, pwd, term, path)
