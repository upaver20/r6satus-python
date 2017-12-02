import r6sapi
import asyncio
import json
import sys

mail = "your uplay e-mail addres"
password = "your uplay password"

args = sys.argv

@asyncio.coroutine

def run( player_id ):
    file = open('player_data.json','w')

    auth = r6sapi.Auth(mail, password )

    try:
        player = yield from auth.get_player(player_id, r6sapi.Platforms.UPLAY)
    except:
        print ("User not found")
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
            "Win Ratio" : player.matches_won / player.matches_played
            }
        json.dump(player_data,file,indent=4)


asyncio.get_event_loop().run_until_complete(run(args[1]))
