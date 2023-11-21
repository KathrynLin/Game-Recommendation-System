from steam import SteamAPI
from steam import TwitchAPI
from steam import APICache


api_key = "xxx"
steamid = 'xxx'
client_id = 'xxx'
client_secret = 'xxx'

c = APICache()
sapi = SteamAPI(api_key, c)
sapi.get_all_user_data(steamid)
tapi = TwitchAPI(client_id, client_secret, c)
m = tapi.get_map()
v = tapi.get_videos()