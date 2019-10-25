"""Fangraphs Scraping Functions."""

from pathlib import Path, PosixPath
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd


def clear_temp():
    """Remove temporary leaderboard file."""
    # Create the data directory useful for csv output
    if not Path('data').exists():
        Path('data').mkdir()

    csv_path = Path('data/Fangraphs Leaderboard.csv')

    # File is always named the same so remove
    try:
        csv_path.unlink()
    except FileNotFoundError:
        pass


def specify_driver():
    """Set Chrome webdriver options and return a diver object."""
    # Set default download directory
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": str(Path.cwd() / 'data')}
    options.add_experimental_option("prefs", prefs)

    # Define the executable path fro the Chrome call
    chrome_driver = Path.cwd() / 'chromedriver'

    # Set the load strategy so that it does not wait for adds to load
    cap = DesiredCapabilities.CHROME
    cap["pageLoadStrategy"] = "none"

    if type(chrome_driver) is PosixPath:
        driver = webdriver.Chrome(executable_path=chrome_driver,
                                  options=options,
                                  desired_capabilities=cap)
    else:
        driver = webdriver.Chrome(executable_path=chrome_driver.name,
                                  options=options,
                                  desired_capabilities=cap)

    return driver


def clean_file(path=Path('data') / 'Fangraphs Leaderboard.csv',
               level='MLB', league='', season='', position=''):
    """Update names for querying and provide additional context.

    Args:
        level (str): the minor/major leave level selected. Default MLB.
        league (str): optionally add a league column
        season (int): optionally add the year of the data
        position (str): optionally add the position of the data

    Returns:
        a renamed pandas dataframe.

    """
    # Define characters to replace prior to being loaded in a database
    char_rep = {' ': '_',
                '%': 'pct',
                '(': '',
                ')': '',
                '.': '',
                '-': '_',
                '/': 'per',
                '+': 'plus',
                '1B': 'singles',
                '2B': 'doubles',
                '3B': 'triples'}

    # Load file
    leaderboard = pd.read_csv(path)

    # Add additional context from selection not present in the file
    leaderboard['Level'] = level

    if season != '':
        leaderboard['Season'] = season
    else:
        pass

    if league != '':
        leaderboard['League'] = league
    else:
        pass

    if position != '':
        leaderboard['Position'] = position
    else:
        pass

    # Replace invalid header characters
    cols = list(leaderboard)
    for i in enumerate(cols):
        for key in char_rep:
            cols[i[0]] = cols[i[0]].replace(key, char_rep[key])
    leaderboard.columns = cols

    return leaderboard


def download_leaderboard(link):
    """Download the leaderboard and return a bool if successful."""
    # Clear any existing file
    clear_temp()

    # Specify the driver
    driver = specify_driver()

    # Wait a reasonable time that a person would take
    wait = WebDriverWait(driver, 20)

    # Instruct the browser to go to the correct page
    driver.get(link)

    # Wait until the element to download is available and then stop loading
    # Fangraphs has ads that cause the page to appear to continue loading
    wait.until(EC.presence_of_element_located((By.ID, "LeaderBoard1_cmdCSV")))
    driver.execute_script("window.stop();")

    # Click the Export Data button
    # Scrolling down the page helps get to the file more reliably
    driver.execute_script("window.scrollTo(0, 200)")
    driver.find_element_by_id("LeaderBoard1_cmdCSV").click()

    leaderboard = Path('data') / 'Fangraphs Leaderboard.csv'

    # Wait up to one minute for the file to download
    exists = False
    for _ in range(0, 600):
        if leaderboard.is_file():
            exists = True
            break
        else:
            time.sleep(10)

    # Close the selenium window
    driver.close()

    return exists


if __name__ == '__main__':

    # Basic examples
    CHECK_FILE = download_leaderboard("https://www.fangraphs.com/leaders.aspx?"
                                      "pos=all&stats=bat&lg=all&qual=y&type=8&"
                                      "season=2018&month=0&season1=2018&ind=0")

    if CHECK_FILE:
        DATA = clean_file()
        print(DATA)
    else:
        raise ValueError("File does not exist")
