import json
import os
import requests
from collections import deque


class SteamAPI:
    def __init__(self, api_key, cache):
        self.api_key = api_key
        self.cache = cache
    

    def get_all_user_data(self, steamid):
        # Check if data is in cache
        cached_data = self.cache.get(steamid, 'users')

        if cached_data:
            return cached_data
        
        data = {'owned_games': None, 'friends_list': None, 'related_games': None}
        owned_games = self.get_owned_games(steamid)
        print("Get owned games... Done")
        friends_list = self.get_friends_list(steamid)
        print("Get friends list... Done")
        related_games = self.get_related_games(steamid)
        print("Get related games... Done")

        for id in related_games:
            if self.cache.get(id, 'apps'):
                continue
            print(f"Retrieving details for {id}")
            app_detail = self.get_app_detail(id)
            self.cache.set(id, app_detail, 'apps')
        
        data['owned_games'] = owned_games
        data['friends_list'] = friends_list
        data['related_games'] = related_games

        self.cache.set(steamid, data, 'users')
        self.cache.save_cache()

        return self.cache.get(steamid, 'users')



    def get_related_games(self, steamid):
        MAX_DEPTH = 1

        visited = []
        q = deque()
        app_list = []

        q.append((steamid, 0))
        visited.append(steamid)

        while len(q) != 0:
            tp = q.popleft()
            id = tp[0]
            depth = tp[1]
            personal_app_list = self.get_owned_games(id)
            for app in personal_app_list:
                if app['appid'] not in app_list:
                    app_list.append(app['appid'])

            if depth == MAX_DEPTH:
                continue
            friends_list = self.get_friends_list(id)
            for friend in friends_list:
                friend_id = friend['steamid']
                if friend_id in visited:
                    continue 
                visited.append(friend_id)
                q.append((friend_id, depth+1))
        
        return app_list

    
    def get_app_detail(self, appid):
        url = f"http://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data[str(appid)]['success']:
                return data[str(appid)]['data']
            else:
                print(f"No game data available for game {appid}.")
                return None
        else:
            print(response.status_code)
            return None


    def get_owned_games(self, steamid):
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        
        params = {
            'key': self.api_key, 
            'steamid': steamid, 
            'format': 'json', 
            'include_appinfo': True, 
            'include_played_free_games': True
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'games' in data.get('response', {}):  # Check if games data is present
                return data['response']['games']
            else:
                print(f"No game data available for user {steamid}.")
                return []
        else:
            # Handle potential errors or non-200 responses
            print(response.status_code)
            return []
    

    def get_friends_list(self, steamid):
        url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/"
        params = {
            'key': self.api_key,
            'steamid': steamid,
            'relationship': 'friend',
            'format': 'json'
        }
        response = requests.get(url, params=params)
        # print(f"Friends list API response for {steamid}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return data['friendslist']['friends']
        else:
            print(f"Friends list API response for {steamid}: {response.status_code}")
            # Handle potential errors or non-200 responses
            return []
        


class APICache:
    def __init__(self, cache_file='api_cache.json'):
        self.cache_file = cache_file
        self.data = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as file:
                return json.load(file)
        return {'users': {}, 'apps': {}, 'maps': {}, 'videos': {}}
    
    def get(self, key, field):
        if field not in self.data:
            print("Invalid field to get.")
            return None 
        if key in self.data[field]:
            return self.data[field][key]
        else:
            return None

    def set(self, key, value, field):
        if field not in self.data:
            print("Invalid field to set.")
            return None 
        self.data[field][key] = value

    def save_cache(self):
        with open(self.cache_file, 'w') as file:
            json.dump(self.data, file, indent=4)


class TwitchAPI:
    def __init__(self, clientid, secret, cache):
        self.clientid = clientid
        self.secret = secret
        self.cache = cache 
        self.set_token()
        self.headers = {
            'Client-ID': self.clientid,
            'Authorization': f'Bearer {self.token}'
        }

    def set_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        body = {
            'client_id': self.clientid,
            'client_secret': self.secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, data=body)
        
        if response.status_code == 200:
            self.token = response.json()['access_token']
        else:
            print(f"Error obtaining token: {response.status_code}")
            self.token = None

    def get_map(self):
        for steam_id in self.cache.data['apps']:
            if steam_id in self.cache.data['maps']:
                continue 

            if not self.cache.data['apps'][steam_id]:
                self.cache.set(steam_id, None, 'maps')
                continue 

            name = self.cache.data['apps'][steam_id]['name']
            url = f'https://api.twitch.tv/helix/search/categories?query={name}'
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
            else:
                print(f"Error fetching twitch info: {response.status_code}")
                self.cache.set(steam_id, None, 'maps')
                continue 

            twitch_id = None
            for twitch_info in data['data']:
                twitch_id = twitch_info['id']
                break
            
            print((steam_id, twitch_id))
            self.cache.set(steam_id, twitch_id, 'maps')
            self.cache.save_cache()
        
        return self.cache.data['maps']
    
    def get_videos(self):
        for steam_id in self.cache.data['apps']:
            twitch_id = self.cache.get(steam_id, 'maps')

            if twitch_id in self.cache.data['videos']:
                continue 
            
            url = f'https://api.twitch.tv/helix/videos?game_id={twitch_id}'
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
            else:
                print(f"Error fetching streams: {response.status_code}")
                self.cache.set(twitch_id, [], 'videos')
                continue 

            videos = []
            for video_info in data['data']:
                if 'url' in video_info:
                    videos.append(video_info['url'])

            print((twitch_id, videos))
            self.cache.set(twitch_id, videos, 'videos')
            self.cache.save_cache()
        
        return self.cache.data['videos']




            
    
if __name__ == "__main__":
    main()