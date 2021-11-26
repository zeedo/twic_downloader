import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import zipfile
import time

# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36
twic = requests.Session()
twic.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'})

response = twic.get('https://theweekinchess.com/twic')


tables = pd.read_html(response.text, match='TWIC Downloads')
twic_downloads_table = tables[0]
print(twic_downloads_table.head())
row = list(twic_downloads_table.loc[0])
twic_id = row[0]
twic_date = row[1]

print(f"Last TWIC Update {twic_date} : {twic_id}")

print(f'Total tables: {len(tables)}')

for item in twic_downloads_table.iterrows():
    item = dict(item[1])
    twic_id = item[('TWIC Downloads', 'TWIC')]
    twic_date = item[('TWIC Downloads', 'Date')]
    twic_zip = f"twic{twic_id}g.zip"
    twic_pgn = f"twic{twic_id}.pgn"
    twic_url = f"https://theweekinchess.com/zips/{twic_zip}"
    print(f"{twic_id} {twic_date} {twic_pgn}", end=' ')

    if(not os.path.exists(f"./twic_downloads/{twic_pgn}")):
        print(f"Missing! Downloading... {twic_url}", end=' ')
        response = twic.get(f"https://theweekinchess.com/zips/{twic_zip}")
        with open(f"./twic_downloads/{twic_zip}", "wb") as file:
            file.write(response.content)
        print(f"Unzipping... {twic_zip}")
        with zipfile.ZipFile(f"./twic_downloads/{twic_zip}","r") as zip_ref:
            zip_ref.extractall("./twic_downloads")
        if(os.path.exists(f"./twic_downloads/{twic_pgn}")):
            os.remove(f"./twic_downloads/{twic_zip}")
            
        # time.sleep(2)
    else:
        print("OK!")
