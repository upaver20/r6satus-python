"""
    r6satus-python
    Extract player data of Rainbow six siege.
"""
import json
import sys
import asyncio
import r6sapi
from pymongo import MongoClient
import datetime

def zchk(target):
    """Check if the input is zero"""
    if target == 0:
        return target + 1
    return target


@asyncio.coroutine
def run(players = None):
    """ main function """
    config = json.load(open('config.json', 'r'))

    client = MongoClient(config["mongodb addres"],config["mongodb port"])

    recentdb = client['r6status']['recent']
    olddb = client['r6status']['old']

    mail = config["e-mail address"]
    pswd = config["password"]

    if players == None:
        players = config["players"]

    auth = r6sapi.Auth(mail, pswd)
    try:
        yield from auth.connect()
    except r6sapi.r6sapi.FailedToConnect:
        print("Email address and password do not match")
        sys.exit(1)

    players_data = []


    for player_id in players:

        try:
            player = yield from auth.get_player(player_id, r6sapi.Platforms.UPLAY)

        except r6sapi.r6sapi.InvalidRequest:
            print(player_id + " is not found")
            continue

        yield from player.check_general()
        yield from player.check_level()
        yield from player.load_queues()
        rank_data = yield from player.get_rank(r6sapi.RankedRegions.ASIA)

        player_data = {
            "date": datetime.datetime.utcnow(),
            "id": player.name,
            "level": player.level,
            "icon": player.icon_url,
            "rank": rank_data.rank,
            "general": {
                "kills": player.kills,
                "deaths": player.deaths,
                "K/D Ratio": round(player.kills / zchk(player.deaths), 2),
                "wons": player.matches_won,
                "loses": player.matches_lost,
                "played": player.matches_played,
                "play time": player.time_played,
                "W/L Ratio": round(player.matches_won / zchk(player.matches_lost), 2)
            }
        }

        for gamemode in [player.casual, player.ranked]:

            player_data[gamemode.name] = {
                "kills": gamemode.kills,
                "deaths": gamemode.deaths,
                "K/D Ratio": round(gamemode.kills / zchk(gamemode.deaths), 2),
                "wons": gamemode.won,
                "loses": gamemode.lost,
                "played": gamemode.played,
                "play time": gamemode.time_played,
                "W/L Ratio": round(gamemode.won / zchk(gamemode.lost), 2)
            }
        recentdb.delete_one({"id": player.name})
        recentdb.insert_one(player_data)
        players_data.append(player_data)

    
    olddb.insert_many(players_data)

args = sys.argv
asyncio.get_event_loop().run_until_complete(run(args))
