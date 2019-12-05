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

OperatorTypes = {
    "DOC": "Defense",
    "TWITCH": "Attack",
    "ASH": "Attack",
    "THERMITE": "Attack",
    "BLITZ": "Attack",
    "BUCK": "Attack",
    "HIBANA": "Attack",
    "KAPKAN": "Defense",
    "PULSE": "Defense",
    "CASTLE": "Defense",
    "ROOK": "Defense",
    "BANDIT": "Defense",
    "SMOKE": "Defense",
    "FROST": "Defense",
    "VALKYRIE": "Defense",
    "TACHANKA": "Defense",
    "GLAZ": "Attack",
    "FUZE": "Attack",
    "SLEDGE": "Attack",
    "MONTAGNE": "Attack",
    "MUTE": "Defense",
    "ECHO": "Defense",
    "THATCHER": "Attack",
    "CAPITAO": "Attack",
    "IQ": "Attack",
    "BLACKBEARD": "Attack",
    "JAGER": "Defense",
    "CAVEIRA": "Defense",
    "JACKAL": "Attack",
    "MIRA": "Defense",
    "LESION": "Defense",
    "YING": "Attack",
    "ELA": "Defense",
    "DOKKAEBI": "Attack",
    "VIGIL": "Defense",
    "ZOFIA": "Attack",
    "LION": "Attack",
    "FINKA": "Attack",
    "MAESTRO": "Defense",
    "ALIBI": "Defense",
    "MAVERICK": "Attack",
    "CLASH": "Defense",
    "NOMAD": "Attack",
    "KAID": "Defense",
    "GRIDLOCK": "Attack",
    "MOZZIE": "Defense",
    "WARDEN": "Defense",
    "NAKK": "Attack",
    "AMARU": "Attack",
    "GOYO": "Defense"
}


def zchk(target):
    """Check if the input is zero"""
    if target == 0:
        return target + 1
    return target


@asyncio.coroutine
def get_data(auth, id=None, uid=None):
    player = yield from auth.get_player(id, r6sapi.Platforms.UPLAY, uid)
    yield from player.check_general()
    yield from player.check_level()
    yield from player.load_queues()
    rank_data = yield from player.get_rank(r6sapi.RankedRegions.ASIA)
    operators_data = yield from player.get_all_operators()


async def get_data(auth, id=None, uid=None):
    player = await auth.get_player(id, r6sapi.Platforms.UPLAY, uid)
    await player.check_general()
    await player.check_level()
    await player.load_queues()
    rank_data = await player.get_rank(r6sapi.RankedRegions.ASIA)
    operators_data = await player.get_all_operators()

    return player, rank_data, operators_data


def pack_data(player, rank_data, operators_data, date):
    player_data = {
        "id": player.name,
        "date": date,
        "level": player.level,
        "icon": player.icon_url,
        "rank": rank_data.rank,
        "uid": player.userid,
        "operator": [],
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

    for _, operator in operators_data.items():
        player_data["operator"].append({
            "name":
            operator.name,
            "type":
            OperatorTypes[operator.name.upper()],
            "kills":
            operator.kills,
            "deaths":
            operator.deaths,
            "kdr":
            operator.kills / zchk(operator.deaths),
            "wons":
            operator.wins,
            "loses":
            operator.losses,
            "pick":
            operator.wins + operator.losses
        })
    return player_data


async def dead_method(dead_id, auth):
    players = dead_id.find({}, {'_id': 0, 'id': 1})
    lives = []
    for player_id in players:
        date = datetime.datetime.utcnow()
        try:
            player, rank_data, operators_data = await get_data(
                auth, player_id['id'], None)

        except r6sapi.exceptions.InvalidRequest:
            print(date, file=sys.stderr)
            print(player_id['id'] + " is not found", file=sys.stderr)
            dead_id.update_one({"id": player_id['id']}, {
                '$set': {
                    "date": date
                },
                '$inc': {
                    "deathcount": 1
                }
            },
                               upsert=True)
            if 5 < dead_id.find_one({"id": player_id['id']})['deathcount']:
                # userdb.delete_one({"id": player_id['id']})
                dead_id.delete_one({"id": player_id['id']})
                print(date, file=sys.stderr)
                print(player_id['id'] + " was deleted in database",
                      file=sys.stderr)
            continue
        # print(player.name + " :" + player.userid)
        lives.append({'uid': player.userid, 'id': player.name})
    return lives


async def live_method(live_id, dead_id, auth, lives, userdb, id2uid, recentdb):
    players_raw = live_id.find({}, {'_id': 0, 'uid': 1, 'id': 1})
    players = []
    for item in players_raw:
        players.append({'uid': item['uid'], 'id': item['id']})
    players.extend(lives)

    players_data = []
    for player_sss in players:
        date = datetime.datetime.utcnow()
        try:
            player, rank_data, operators_data = await get_data(
                auth, None, player_sss['uid'])

        except r6sapi.exceptions.InvalidRequest:
            print(date, file=sys.stderr)
            print(player_sss['id'] + " is not found", file=sys.stderr)
            userdb.update({"id": player_sss['id']}, {
                '$set': {
                    "date": date
                },
                '$inc': {
                    "deathcount": 1
                }
            },
                          upsert=True)
            dead_id.update({"id": player_sss['id']},
                           {'$set': {
                               "date": date,
                               "deathcount": 0
                           }},
                           upsert=True)
            live_id.delete_one({"id": player_sss['id']})
            continue

        # print(player.userid)

        player_data = pack_data(player, rank_data, operators_data, date)

        userdb.update_one(
            {"id": player.name},
            {'$set': {
                "date": date,
                "deathcount": 0,
                "uid": player.userid
            }},
            upsert=True)
        dead_id.delete_one({"id": player.name})
        id2uid.update_one({"id": player.name},
                          {'$set': {
                              "date": date,
                              "uid": player.userid
                          }},
                          upsert=True)
        live_id.update_one({"uid": player.userid},
                           {'$set': {
                               "date": date,
                               "id": player.name
                           }},
                           upsert=True)
        recentdb.delete_one({"id": player.name})
        recentdb.insert_one(player_data)
        players_data.append(player_data)
    return players_data


async def run():
    """ main function """
    config_path = open("./config.json", 'r')
    config = json.load(config_path)

    client = MongoClient(config["mongodb addres"], config["mongodb port"])
    recentdb = client['r6status']['recent']
    olddb = client['r6status']['old']
    userdb = client['r6status']['user']
    id2uid = client['r6status']['id2uid']
    live_id = client['r6status']['live_id']
    dead_id = client['r6status']['dead_id']

    mail = config["e-mail address"]
    pswd = config["password"]

    auth = r6sapi.Auth(mail, pswd)

    try:
        await auth.connect()
    except r6sapi.exceptions.FailedToConnect as e:
        print("type:{0}".format(type(e)))
        print("args:{0}".format(e.args))
        print("message:{0}".format(e.message))
        print("{0}".format(e))
        sys.exit(1)

    lives = await dead_method(dead_id, auth)
    players_data = await live_method(live_id, dead_id, auth, lives, userdb,
                                     id2uid, recentdb)

    olddb.insert_many(players_data)
    await auth.close()
    print(datetime.datetime.utcnow())
    print("finised")


asyncio.get_event_loop().run_until_complete(run())
