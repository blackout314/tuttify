import telegram_send, time
import json
import argparse, os
from datetime import date, timedelta

from urllib.request import urlopen
from bs4 import BeautifulSoup

# Parse arguments
parser = argparse.ArgumentParser(
description="This script will watch tutti.ch for new ads and notify you via telegram. Also, it keeps a record of listings with prices in a JSON file."
)
parser.add_argument('-c', '--canton', metavar="Canton", type=str, default="ganze-schweiz",
    help="In which canton to look for.")
parser.add_argument('-q', '--query', metavar="Query", type=str, help='tutti.ch search string')
parser.add_argument('-s', '--silent', action='store_true', default=False,
    help="Don't send notifications.")
parser.add_argument('-m', '--maxprice', metavar="Price", type=int, default=0,
    help="Highest price to still look for.")
args = parser.parse_args()

# Header for requests
headers = {
    'User-Agent': 'Anon',
    'From': 'your.email@here.com'
}

while True:
    # Download page
    try:
        search_url = 'https://www.tutti.ch/de/li/' + args.canton.lower() + '?q=' + args.query.lower().replace(" ", "%20")
        html = urlopen(search_url)
        soup = BeautifulSoup(html, features="lxml")

        list_all = soup.find_all('div', attrs={"class":"_3aiCi"})

        for item in list_all:

            url = item.find_all('a', attrs={"class":"_16dGT"})[0].get("href")
            url = "https://tutti.ch" + url

            title = item.find_all('h4', attrs={"class":"_2SE_L"})[0].get_text()

            price = item.find_all('div', attrs={"class":"_6HJe5"})[0].get_text()
            price_num = price[:-2].replace("'", "")

            try:
                price_num = int(price_num)
                isTooExp = (price_num > args.maxprice) and (args.maxprice > 0)
            except:
                print("Invalid price. Probably empty.")
                isTooExp = False

            location = item.find_all('span', attrs={"class":"_3f6Er"})[0].get_text()

            # Create dict for first advertisement
            new_dict = {"name" : title, "url" : url, "price": price, "location": location}

            # Check if file exists already and create if not
            fname = args.query.lower() + "_dictionary.json"
            if not os.path.isfile(fname):
                mydict = {}
                mydict["inserate"] = []
                listings = mydict["inserate"]
                listings.append(new_dict)

                with open(fname, 'w') as f:
                    json.dump(mydict, f)

                # notify
                print("New listing...")
                if (not args.silent) and (not isTooExp):
                    message = 'Neues Inserat: {} ({}) in {}\n {}'.format(title, price, location, url)
                    telegram_send.send(messages=[message])

            else:
                with open(fname,'r+') as f:
                    dic = json.load(f)

                    if new_dict in dic["inserate"]:
                        print("same..")

                        # If listing is known, skip all afterwards
                        f.close()
                        break
                    else:
                        dic["inserate"].append(new_dict)
                        f.seek(0)
                        json.dump(dic, f)

                        # notify
                        print("New listing...")
                        if (not args.silent) and (not isTooExp):
                            message = 'Neues Inserat: {} ({}) in {}\n {}'.format(title, price, location, url)
                            telegram_send.send(messages=[message])

            # Close file
            f.close()

        # Wait a minute
        time.sleep(60)

    except:
        # Wait half a minute, in case the server isn't reachable
        print("Server not reachable")
        time.sleep(30)
