from api import APICache, SteamAPI

c = APICache()
steam_api = SteamAPI("key.conf", c)
steam_api.get_data(2)