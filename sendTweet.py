from html import unescape
import sqlite3
from time import sleep
from twython import Twython
from auth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)



def send_tweet(message:str):
    twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
    )

    twitter.update_status(status=message)
    print("Tweeted: %s" % message)


def main():
    domain = "https://www.ur-net.go.jp"
    db_name = "ur.db"
    con = sqlite3.connect(db_name)
    cur = con.cursor()


    cur.execute(f"SELECT count(*) from room WHERE is_new_room=1")
    new_room_count=cur.fetchone()[0]
    print(f"{new_room_count} new room found")

    if new_room_count > 0:
        cur.execute(f"SELECT * from room WHERE is_new_room=1")
        rows = cur.fetchall()
        for row in rows:
            bukken_url=row[3]
            bukken_name=row[4]
            room_id=row[6]
            room_name=row[7]
            room_rent=row[8]
            room_commonfee=row[9]
            room_type=row[10]
            room_floorspace =unescape(row[11])
            room_floor=row[12]
            room_urlDetail=row[13]
            

            # print(f"{room_id}: {bukken_name} {room_name} {room_rent} {room_type} {room_floorspace}  {room_urlDetail}")

            message=f"""空室速報： 
　物件：「{bukken_name}」
　　　　{domain}{bukken_url}
　空室： 「{room_name}」
　　　　{room_rent} {room_type} {room_floorspace}
　　　　{domain}{room_urlDetail}
"""
            print(message)

        # sleep(10)


if __name__ == '__main__':
    main()
