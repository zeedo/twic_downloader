from datetime import timedelta
import logging
import os
import requests_cache
import pandas as pd
import zipfile
from sqlitedict import SqliteDict
# Log everything, and send it to stderr.
logging.basicConfig(level=logging.INFO,format='%(levelname)s -:- %(message)s')

if __name__ == "__main__":
    # Set Header and Cachin options
    # The main page only updates weekly, zips should never change so just cache them forever
    # Cache file can always be cleared out manually for space

    url_expiry = {
        'https://theweekinchess.com/twic': timedelta(days=1),
        'https://theweekinchess.com/zips/*': -1, # Never
        
    }
    twic = requests_cache.CachedSession('twic_downloads_cache', urls_expire_after=url_expiry)
    twic.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'})

    # Main Page URL
    url = 'https://theweekinchess.com/twic'


    # Download Main Page
    response = twic.get(url)
    logging.info(f"Downloading URL: {url}")
    logging.info("....... (CACHED!)" if response.from_cache else "....... Downloaded")
    # Table is named "TWIC Downloads"
    tables = pd.read_html(response.text, match='TWIC Downloads',parse_dates=True)
    twic_downloads_table = tables[0]
    # logging.info(twic_downloads_table.head())

    # Show top table item (We're assuming new is at the top, consideri sorting in future)
    row = list(twic_downloads_table.loc[0])
    twic_id = row[0]
    twic_date = row[1]
    logging.info(f"Last TWIC Update:\t {twic_date} : {twic_id}")
    with SqliteDict('./twic_downloader_saveddata.sqlite', autocommit=True) as saved_data:
        if 'last_download_date' in saved_data:
            logging.info(f"Last Download:\t\t {saved_data['last_download_date']} : {saved_data['last_download_id']} ")
            if twic_date in saved_data['last_download_date']:
                logging.info(f"No new games :-(")
                exit()
        # Saving the latest id and date for checking on next run.
        saved_data['last_download_id'] = twic_id
        saved_data['last_download_date'] = twic_date


    # Run through each item in the table
    # We could just download the newest, but we're checking incase me miss a run and there's more than one game
    # to download.
    for item in twic_downloads_table.iterrows():
        item = dict(item[1])
        twic_id = item[('TWIC Downloads', 'TWIC')]
        twic_date = item[('TWIC Downloads', 'Date')]
        twic_zip = f"twic{twic_id}g.zip"
        twic_pgn = f"twic{twic_id}.pgn"
        twic_url = f"https://theweekinchess.com/zips/{twic_zip}"
        logging.info(f"TWIC ID: {twic_id}\tUpload Date: {twic_date}\t  PGN: {twic_pgn}")
        
        # Have we already got the PGN with this twic_id?
        if(not os.path.exists(f"./twic_downloads/{twic_pgn}")):
            response = twic.get(f"https://theweekinchess.com/zips/{twic_zip}")
            logging.warning(f"{twic_pgn} Missing!")
            logging.info(f"Downloading... {twic_url}")
            logging.info("....... (CACHED!)" if response.from_cache else "....... Downloaded")

            with open(f"./twic_downloads/{twic_zip}", "wb") as file:
                file.write(response.content)

            # Unzip the downloaded file 
            logging.info(f"Unzipping... {twic_zip}")
            with zipfile.ZipFile(f"./twic_downloads/{twic_zip}","r") as zip_ref:
                zip_ref.extractall("./twic_downloads")
            # Delete the zip (we'll have copy in cache) 
            if(os.path.exists(f"./twic_downloads/{twic_pgn}")):
                os.remove(f"./twic_downloads/{twic_zip}")
            
        else:
            # Yes we have the file, just print OK.
            logging.info("....... OK!")