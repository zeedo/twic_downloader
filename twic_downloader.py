from datetime import timedelta
import os
import requests_cache
import xml.etree.ElementTree as ET
import pandas as pd
import zipfile


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
print(f"downloading URL: {url}", "(CACHED!)" if response.from_cache else "Downloaded")

# Table is named "TWIC Downloads"
tables = pd.read_html(response.text, match='TWIC Downloads')
twic_downloads_table = tables[0]
print(twic_downloads_table.head())

# Show top table item (We're assuming new is at the top, consideri sorting in future)
row = list(twic_downloads_table.loc[0])
twic_id = row[0]
twic_date = row[1]
print(f"Last TWIC Update {twic_date} : {twic_id}")

# Run through each item inm the table
for item in twic_downloads_table.iterrows():
    item = dict(item[1])
    twic_id = item[('TWIC Downloads', 'TWIC')]
    twic_date = item[('TWIC Downloads', 'Date')]
    twic_zip = f"twic{twic_id}g.zip"
    twic_pgn = f"twic{twic_id}.pgn"
    twic_url = f"https://theweekinchess.com/zips/{twic_zip}"
    print(f"{twic_id} {twic_date} {twic_pgn}", end=' ')
    
    # Have we already got the PGN with this twic_id?
    if(not os.path.exists(f"./twic_downloads/{twic_pgn}")):
        response = twic.get(f"https://theweekinchess.com/zips/{twic_zip}")
        print(f"Missing! Downloading... {twic_url}", "(CACHED!)" if response.from_cache else "Downloaded", end=' ')
        with open(f"./twic_downloads/{twic_zip}", "wb") as file:
            file.write(response.content)

        # Unzip the downloaded file 
        print(f"Unzipping... {twic_zip}")
        with zipfile.ZipFile(f"./twic_downloads/{twic_zip}","r") as zip_ref:
            zip_ref.extractall("./twic_downloads")
        # Delete the zip (we'll have copy in cache) 
        if(os.path.exists(f"./twic_downloads/{twic_pgn}")):
            os.remove(f"./twic_downloads/{twic_zip}")
        
    else:
        # Yes we have the file, just print OK.
        print("OK!")
