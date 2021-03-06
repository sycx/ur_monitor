from html import unescape
import sqlite3
from time import sleep
import logging
from twython import Twython
from auth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

from settings import (
    DM_RECIPIENT_IDS
)



def send_tweet(message:str):
    twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
    )

    for id in DM_RECIPIENT_IDS:
        event = {
            "type": "message_create",
            "message_create":{
                "target": {
                    "recipient_id": id
                },
                "message_data":{
                    "text": message
                }
            }
        }

        twitter.send_direct_message(event=event)
    
    # twitter.update_status(status=message)
    logging.info("Tweeted: %s" % message)


def main():
    domain = "https://www.ur-net.go.jp"
    db_name = "ur.db"
    con = sqlite3.connect(db_name)
    cur = con.cursor()


    cur.execute(f"SELECT count(*) from room WHERE is_new_room=1")
    new_room_count=cur.fetchone()[0]
    logging.info(f"{new_room_count} new room found")

    if new_room_count > 0:

        cur.execute("select *, count(*) as cnt from room where is_new_room=1 group by bukken_id" )
        group_rows = cur.fetchall()

        
        for row in group_rows:
            bid = row[2]
            bukken_url=row[3]
            bukken_name=row[4]
            bukken_skcs=row[5]

            message=f"""空室速報： 
　物件：{bukken_skcs} 「{bukken_name}」
　　　　{domain}{bukken_url}
  空室："""

            cur.execute(f"SELECT * from room WHERE is_new_room=1 AND bukken_id='{bid}'")
            rows = cur.fetchall()
            for row in rows:
                room_id=row[6]
                room_name=row[7]
                room_rent=row[8]
                room_commonfee=row[9]
                room_type=row[10]
                room_floorspace =unescape(row[11])
                room_floor=row[12]
                room_urlDetail=row[13]
            
                message+=f"""
　「{room_name}」 {room_rent} {room_type} {room_floorspace}
　　　　{domain}{room_urlDetail}
"""
            # print(message)
            send_tweet(message)
            sleep(3)


if __name__ == '__main__':
    main()
