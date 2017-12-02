import r6sapi
import asyncio
import json
import sys

@asyncio.coroutine

def run():
    config = json.load(open('config.json','r'))
    file = open('player_data.json','w')

    mail = config["e-mail address"]
    pswd = config["password"]
    players = config["players"]

    try:
        auth = r6sapi.Auth( mail, pswd )
    except:
        print("Email address and password do not match")
        sys.exit(1)

    players_data=[]

    for player_id in players:

        try:
            player = yield from auth.get_player(player_id, r6sapi.Platforms.UPLAY)

        except:
            print (player_id + "is not found")
            break

        else:
            yield from player.load_general()
            yield from player.load_level()
            rank_data = yield from player.get_rank(r6sapi.RankedRegions.ASIA,7)

            player_data = {
                "id" : player.name,
                "level" : player.level,
                "icon"  : player.icon_url,
                "rank"  : rank_data.rank,
                "kills" : player.kills,
                "deaths" : player.deaths,
                "K/D Ratio" : player.kills / player.deaths,
                "wons" : player.matches_won,
                "loses" : player.matches_lost,
                "W/L Ratio" : player.matches_won / player.matches_lost
            }
        players_data.append(player_data)

    json.dump(players_data,file,indent=4,sort_keys=True)

asyncio.get_event_loop().run_until_complete(run())
