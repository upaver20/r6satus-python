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
def run():
    """ main function """
    config_path = open('/home/upaver20/.ghq/github.com/upaver20/r6satus-python/config.json','r')
    config = json.load(config_path)

    client = MongoClient(config["mongodb addres"],config["mongodb port"])

    recentdb = client['r6status']['recent']
    olddb = client['r6status']['old']
    userdb = client['r6status']['user']

    mail = config["e-mail address"]
    pswd = config["password"]

    players = userdb.find({},{'_id':0,'id':1})

    auth = r6sapi.Auth(mail, pswd)
    try:
        yield from auth.connect()
    except r6sapi.r6sapi.FailedToConnect:
        print("Email address and password do not match")
        sys.exit(1)

    players_data = []


    for player_id in players:
        date = datetime.datetime.utcnow()
        try:
            player = yield from auth.get_player(player_id['id'], r6sapi.Platforms.UPLAY)
        except r6sapi.r6sapi.InvalidRequest:
            userdb.update({"id":player_id['id']},{'$set':{"date":date},'$inc':{"deathcount":1}},upsert=True)
            if 5 > userdb.find_one({"id":player_id['id']})['deathcount']:
                userdb.delete_one({"id": player_id['id']})
            print(player_id['id'] + " is not found")
            continue

        yield from player.check_general()
        yield from player.check_level()
        yield from player.load_queues()
        rank_data = yield from player.get_rank(r6sapi.RankedRegions.ASIA)

        player_data = {
            "date": date,
            "id": player.name,
            "level": player.level,
            "icon": player.icon_url,
            "rank": rank_data.rank,
            "general": {
                "kills": player.kills,
                "deaths": player.deaths,
                "kdr": player.kills / zchk(player.deaths),
                "wons": player.matches_won,
                "loses": player.matches_lost,
                "played": player.matches_played,
                "playtimes": player.time_played,
                "wlr": player.matches_won / zchk(player.matches_lost)
            }
        }

        for gamemode in [player.casual, player.ranked]:

            player_data[gamemode.name] = {
                "kills": gamemode.kills,
                "deaths": gamemode.deaths,
                "kdr": gamemode.kills / zchk(gamemode.deaths),
                "wons": gamemode.won,
                "loses": gamemode.lost,
                "played": gamemode.played,
                "playtimes": gamemode.time_played,
                "wlr": gamemode.won / zchk(gamemode.lost)
            }
        userdb.update({"id":player.name},{'$set':{"date":date,"deathcount":0}},upsert=True)


        recentdb.delete_one({"id": player.name})
        recentdb.insert_one(player_data)
        players_data.append(player_data)


    olddb.insert_many(players_data)


asyncio.get_event_loop().run_until_complete(run())
