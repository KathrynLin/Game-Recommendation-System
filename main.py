from API_loading import SteamAPI
from API_loading import TwitchAPI
from API_loading import APICache
import json

with open('user.conf', 'r') as file:
    config = json.load(file)

api_key = config['api_key']
steamid = config['steamid']
client_id = config['client_id']
client_secret = config['client_secret']

c = APICache()
sapi = SteamAPI(api_key, c)
sapi.get_all_user_data(steamid)
tapi = TwitchAPI(client_id, client_secret, c)
m = tapi.get_map()
v = tapi.get_videos()