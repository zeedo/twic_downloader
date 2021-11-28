import logging
import os
import zipfile
from datetime import timedelta

import pandas as pd
import requests_cache
from sqlitedict import SqliteDict

# Log everything, and send it to stderr.
# TODO: Imeplement a command line option to download a range and optionally add them to a bulk PGN for chessbase import.
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname)-8s %(name)-12s-:-  %(message)s')


def main():

    twic_session = setup_twic_session()

    response = download_main_page(twic_session)

    twic_downloads_table = parse_downloads_table(response)

    if not check_new_twic_issue(twic_downloads_table):
        exit()
    else:
        # Run through each item in the table
        # We could just download the newest, but we're checking incase me miss a run and there's more than one game
        # to download.

        for _, twic_row in twic_downloads_table.iterrows():  # Throw away the index
            download_twic_pgn(twic_session, twic_row)


def check_new_twic_issue(twic_downloads_table):
    # Show top table item (We're assuming new is at the top, consider sorting in future)
    twic_id = twic_downloads_table.loc[0, 'TWIC_ID']  # row 0 column 0
    twic_date = twic_downloads_table.loc[0, 'Date']  # row 0 column 1
    logging.info(f"Last TWIC Update:\t {twic_date:%Y-%m-%d} : {twic_id}")
    with SqliteDict('./twic_downloader_saveddata.sqlite', autocommit=True) as saved_data:
        if 'last_download_date' in saved_data:
            logging.info(
                f"Last Download:\t\t {saved_data['last_download_date']:%Y-%m-%d} : {saved_data['last_download_id']} ")
            if twic_date == saved_data['last_download_date']:
                logging.info(f"No new games :-(")
                return False
        # Saving the latest id and date for checking on next run.
        saved_data['last_download_id'] = twic_id
        saved_data['last_download_date'] = twic_date
        return True


def parse_downloads_table(response):
    tables = pd.read_html(
        response.text, match='TWIC Downloads')
    twic_downloads_table = tables[0]
    # First line in the DB is a bit messy, so label the column headings we need for clarity.
    twic_downloads_table.columns = ['TWIC_ID', 'Date', 2, 3, 4, 5, 6, 7]
    twic_downloads_table['Date'] = pd.to_datetime(twic_downloads_table['Date'])
    return twic_downloads_table


def setup_twic_session():
    # Set Header and Caching options
    # The main page only updates weekly, zips should never change so just cache them forever
    # Cache file can always be cleared out manually for space
    url_expiry = {
        'https://theweekinchess.com/twic': timedelta(days=1),
        'https://theweekinchess.com/zips/*': -1,  # Never
    }
    twic = requests_cache.CachedSession(
        'twic_downloads_cache', urls_expire_after=url_expiry)
    twic.headers.update(
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'})

    return twic


def download_main_page(twic_session):
    # Main Page URL
    url = 'https://theweekinchess.com/twic'

    # Download Main Page
    response = twic_session.get(url)
    logging.info(f"Downloading URL: {url}")
    check_cached(response)
    # Table is named "TWIC Downloads"
    return response


def download_twic_pgn(twic_session, twic_row):
    twic_id = twic_row['TWIC_ID']
    twic_date = twic_row['Date']
    twic_zip = f"twic{twic_id}g.zip"
    twic_pgn = f"twic{twic_id}.pgn"
    twic_url = f"https://theweekinchess.com/zips/{twic_zip}"
    logging.info(
        f"TWIC ID: {twic_id}\tUpload Date: {twic_date}\t  PGN: {twic_pgn}")

    # Have we already got the PGN with this twic_id?
    if(not os.path.exists(f"./twic_downloads/{twic_pgn}")):
        response = twic_session.get(
            f"https://theweekinchess.com/zips/{twic_zip}")
        logging.warning(f"{twic_pgn} Missing!")
        logging.info(f"Downloading... {twic_url}")
        check_cached(response)

        with open(f"./twic_downloads/{twic_zip}", "wb") as file:
            file.write(response.content)

            # Unzip the downloaded file
        logging.info(f"Unzipping... {twic_zip}")
        with zipfile.ZipFile(f"./twic_downloads/{twic_zip}", "r") as zip_ref:
            zip_ref.extractall("./twic_downloads")
            # Delete the zip (we'll have copy in cache)
        if(os.path.exists(f"./twic_downloads/{twic_pgn}")):
            os.remove(f"./twic_downloads/{twic_zip}")

    else:
        # Yes we have the file, just print OK.
        logging.info("....... OK!")


def check_cached(response):
    if response.from_cache:
        logging.warning(f"....... (CACHED! Expires {response.expires})")
    else:
        logging.info("....... Downloaded")


if __name__ == "__main__":
    main()
