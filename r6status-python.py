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

    auth = r6sapi.Auth( mail, pswd )

    try:
        yield from auth.connect()
    except:
        print("Email address and password do not match")
        sys.exit(1)

    players_data=[]

    for player_id in players:

        try:
            player = yield from auth.get_player(player_id, r6sapi.Platforms.UPLAY)

        except:
            print (player_id + " is not found")
            continue

        yield from player.check_general()
        yield from player.check_level()
        yield from player.load_queues()
        rank_data = yield from player.get_rank(r6sapi.RankedRegions.ASIA,7)

        player_data = {
            "id" : player.name,
            "level" : player.level,
            "icon"  : player.icon_url,
            "rank"  : rank_data.rank,
            "general" : {
                "kills" : player.kills,
                "deaths" : player.deaths,
                "K/D Ratio" : round( player.kills / player.deaths,2 ) ,
                "wons" : player.matches_won,
                "loses" : player.matches_lost,
                "played": player.matches_played,
                "play time" : player.time_played,
                "W/L Ratio" : round( player.matches_won / player.matches_lost, 2)
            }
        }

        for gamemode in [ player.casual, player.ranked ]:
            player_data[ gamemode.name ] = {
                "kills" : gamemode.kills,
                "deaths" : gamemode.deaths,
                "K/D Ratio" : round( gamemode.kills / gamemode.deaths, 2),
                "wons" : gamemode.won,
                "loses" : gamemode.lost,
                "played": gamemode.played,
                "play time" : gamemode.time_played,
                "W/L Ratio" : round(player.matches_won / player.matches_lost, 2)
            }

        players_data.append(player_data)

    json.dump(players_data,file,indent=4,sort_keys=True)

asyncio.get_event_loop().run_until_complete(run())
