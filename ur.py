#!/bin/python
from html import unescape
from sqlite3.dbapi2 import Cursor, Date
import requests
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from enum import Enum
import sqlite3
import os.path
import time


#UR api
url = "https://chintai.sumai.ur-net.go.jp/chintai/api/bukken/search/list_bukken/"

## POST params

# rent_low, rent_hight:
# floorspace_low: floorspace_high:

# tdfk: 都道府県
# 01: 北海道 
# 08: 茨城県 ibaraki
# 11: 埼玉県 saitama
# 12: 千葉県 chiba
# 13: 東京都 tokyo
# 14: 神奈川県 kanagawa

class TDFK(Enum):
    ibaraki = "08"
    saitama = "11"
    chiba = "12"
    tokyo = "13"
    kanagawa = "14"

# tokyo area
#
# 01: 都心 (千代田区、中央区、港区、新宿区、文京区、渋谷区)
# 02: 23区東 (台東区、墨田区、江東区、荒川区、足立区、葛飾区、江戸川区)
# 03: 23区南 (品川区、目黒区、大田区、世田谷区)
# 04: 23区西 (中野区、杉並区、練馬区)
# 05: 23区北 (豊島区、北区、板橋区)
# 06: 市部 (八王子市、立川市、武蔵野市、三鷹市、府中市、昭島市、調布市、町田市、小金井市、小平市、日野市、東村山市、国分寺市、国立市、福生市、狛江市、清瀬市、東久留米市、武蔵村山市、多摩市、稲城市、羽村市、西東京市)
tokyo_area_list = ["01","02","03","04","05","06"]
 
 
def get_bukken(tdfk:str, area:str, cur:Cursor, check_date:str):
    headers = {
    'Connection': "keep-alive",
    'Accept': "application/json, text/javascript, */*; q=0.01",
    'Origin': "https://www.ur-net.go.jp",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    'Sec-Fetch-Site': "same-site",
    'Sec-Fetch-Mode': "cors",
    'Referer': "https://www.ur-net.go.jp/chintai/kanto/tokyo/list/",
    'Accept-Encoding': "gzip, deflate, br",
    'Accept-Language': "ja,en-US;q=0.9,en;q=0.8",
    'Cache-Control': "no-cache",
    'Host': "chintai.sumai.ur-net.go.jp",
    'cache-control': "no-cache"
    }
    payload = f"rent_low=&rent_high=&floorspace_low=&floorspace_high=&tdfk={tdfk}&area={area}"
    response = requests.request("POST", url, data=payload, headers=headers)
    print(f"get bukken_list: tdfk={tdfk} area={area}")
    if response.status_code != requests.codes.ok:
        print(f"error response: [{response.status_code}] {response.text}")
        return

    bukken_list = json.loads(response.text, object_hook=lambda d: SimpleNamespace(**d))
    for bukken in bukken_list:
        if bukken.roomCount > 0:
            # get rooms
            rooms = get_rooms(tdfk, bukken.id)
            # room
            # name:  (3号棟719号室)
            # status: combine of (type / fllorspace / floor)
            # type: (1LDK)
            # floorspace: 面積(48&#13217)
            # floor:  (6階)
            # urlDetail:  (/chintai/.../......)
            # madori : image url 間取り図 
            for room in rooms:
                #print(f"{room.name}:{room.rent}({room.commonfee}) {room.status} {room.type} {bukken.roomUrl}{room.id}")
                cur.execute(f"SELECT count(*) from room WHERE last_check_exist='1' AND room_id='{room.id}' AND bukken_id='{bukken.id}'")  
                exist_count = cur.fetchone()[0]
                is_new_room = int(exist_count == 0)

                cur.execute(f"""INSERT OR REPLACE INTO room VALUES(
                    '{tdfk}',
                    '{area}',
                    '{bukken.id}',
                    '{bukken.bukkenUrl}',
                    '{bukken.name}',
                    '{bukken.skcs}',
                    '{room.id}',
                    '{room.name}',
                    '{room.rent}',
                    '{room.commonfee}',
                    '{room.type}',
                    '{room.floorspace}',
                    '{room.floor}',
                    '{room.urlDetail}',
                    '{room.madori}',
                    {is_new_room},
                    1,
                    '{check_date}'
                 )""")
            
            time.sleep(1)

# get_rooms:
# rent_low,rent_high
# floorspace_low,floorspace_high
# tdfk, mode, id
def get_rooms(tdfk:str, bukken_id):
    room_list_url = "https://chintai.sumai.ur-net.go.jp/chintai/api/room/list/"
    headers = {
    'Connection': "keep-alive",
    'Accept': "application/json, text/javascript, */*; q=0.01",
    'Origin': "https://www.ur-net.go.jp",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    'Sec-Fetch-Site': "same-site",
    'Sec-Fetch-Mode': "cors",
    'Referer': "https://www.ur-net.go.jp/",
    'Accept-Encoding': "gzip, deflate, br",
    'Accept-Language': "ja,en-US;q=0.9,en;q=0.8",
    'Cache-Control': "no-cache",
    'Host': "chintai.sumai.ur-net.go.jp",
    'cache-control': "no-cache"}
    payload = f"rent_low=&rent_high=&floorspace_low=&floorspace_high=&tdfk={tdfk}&mode=init&id={bukken_id}"
    print(f"get room_list: tdfk={tdfk} bukken={bukken_id}")
    response = requests.request("POST", room_list_url, data=payload, headers=headers)
    if response.status_code != requests.codes.ok:
        print(f"error response: [{response.status_code}] {response.text}")
        return []
        
    rooms_list = json.loads(response.text, object_hook=lambda d: SimpleNamespace(**d))
    return rooms_list

    

def init_db_scheme(name):
    if os.path.isfile(name):
        return

    try:
        con = sqlite3.connect(name)
        cur = con.cursor()
        cur.execute('''CREATE TABLE room
               (
                tdfk text,
                area text,
                bukken_id text,
                bukken_url text,
                bukken_name text,
                bukken_skcs text,
                room_id text,
                room_name text,
                room_rent text,
                room_commonfee text,
                room_type text,
                room_floorspace text,
                room_floor text,
                room_urlDetail text,
                room_madori text,
                is_new_room integer,
                last_check_exist integer,
                last_check_date datetime,
                PRIMARY KEY (bukken_id, room_id)
                )''')
    except sqlite3.Error as e:
        print(e)
    finally:
        if con:
            con.close()


def main():
    JST = timezone(timedelta(hours=+9), 'JST')
    date = datetime.now(JST)
    check_date = date.strftime("%B %d, %Y %I:%M%p")

    db_name = "ur.db"
    init_db_scheme(db_name)

    con = sqlite3.connect(db_name)
    
    cur = con.cursor()

    # tokyo_area_list = ["03"]
    for area in tokyo_area_list:
        get_bukken(TDFK.tokyo.value, area, cur, check_date)
    
    # check_date='June 06, 2021 03:08PM'
    # check result
    cur.execute(f"SELECT count(*) from room WHERE last_check_date='{check_date}' AND is_new_room=1")
    new_room_count=cur.fetchone()[0]
    print(f"{new_room_count} new room found")

    if new_room_count > 0:
        cur.execute(f"SELECT * from room WHERE last_check_date='{check_date}' AND is_new_room=1")
        rows = cur.fetchall()
        for row in rows:
            space=unescape(row[11])
            print(f"{row[6]}: {row[4]} {row[7]} {row[8]} {row[10]} {space}  {row[13]}")


    # mark not exist.
    cur.execute(f"UPDATE room SET last_check_exist=0  WHERE last_check_date <> '{check_date}'")

    con.commit()

    con.close()

if __name__ == '__main__':
    main()
