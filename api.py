import json
import os
import requests
from collections import deque
import re


class SteamAPI:
    def __init__(self, key_file_name, cache):
        with open(key_file_name) as f:
            conf = json.load(f)
        self.api_key = conf["api_key"]
        self.root_user_id = conf["steam_id"]
        self.cache = cache
    

    def get_data(self, max_depth):  
        if self.cache.get('user_friend_graph'):
            print("Cache already created.")
            return 

        friend_tree = {}
        user_game_map = {}
        game_detail = {}

        visited = []
        q = deque()

        q.append((self.root_user_id, 0))
        visited.append(self.root_user_id)

        while len(q) != 0:
            tp = q.popleft()
            id = tp[0]
            depth = tp[1]
            game_list = self.get_game_list(id)
            game_list_shorten = []
            user_game_map[id] = []
            for game_time in game_list:
                if game_time["playtime_forever"] > 600:
                    user_game_map[id].append(game_time)
                    game_list_shorten.append(game_time)

            for g in game_list_shorten:
                game_id = g["appid"]
                if game_id not in game_detail:
                    detail = self.get_game_detail(game_id)
                    game_detail[game_id] = detail

            friend_list = self.get_friend_list(id)
            if depth == max_depth:
                friend_tree[id] = []
                for friend in friend_list:
                    if friend in friend_tree:
                        friend_tree[id].append(friend)
                continue
            
            friend_tree[id] = friend_list
            for friend in friend_list:
                if friend in visited:
                    continue 
                visited.append(friend)
                q.append((friend, depth+1))

        self.cache.set('user_friend_graph', friend_tree)
        self.cache.set('user_game_mapping', user_game_map)
        self.cache.set('game_detail', game_detail)
        self.cache.save_cache()



    
    def get_game_detail(self, game_id):
        url = f"http://store.steampowered.com/api/appdetails?appids={game_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data[str(game_id)]['success']:
                return data[str(game_id)]['data']
            else:
                print(f"No game data available for game {game_id}.")
                return None
        else:
            print(response.status_code)
            return None


    def get_game_list(self, user_id):
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        
        params = {
            'key': self.api_key, 
            'steamid': user_id, 
            'format': 'json'
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'games' in data.get('response', {}):  # Check if games data is present
                return data['response']['games']
            else:
                print(f"No game data available for user {user_id}.")
                return []
        else:
            # Handle potential errors or non-200 responses
            print(f"Games list API response for {user_id}: {response.status_code}")
            return []
    

    def get_friend_list(self, user_id):
        url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/"
        params = {
            'key': self.api_key,
            'steamid': user_id,
            'relationship': 'friend',
            'format': 'json'
        }
        response = requests.get(url, params=params)
        # print(f"Friends list API response for {steamid}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            friend_list = [obj['steamid'] for obj in data['friendslist']['friends']]
            return friend_list
        else:
            print(f"Friends list API response for {user_id}: {response.status_code}")
            # Handle potential errors or non-200 responses
            return []
        



class TwitchAPI:
    def __init__(self, key_file_name):
        with open(key_file_name) as f:
            conf = json.load(f)
        
        self.client_id = conf["twitch_client_id"]
        self.client_secret = conf["twitch_client_secret"]
        self.set_token()
        self.headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.token}'
        }
    

    def set_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        body = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, data=body)
        
        if response.status_code == 200:
            self.token = response.json()['access_token']
        else:
            print(f"Error obtaining token: {response.status_code}")
            self.token = None

    
    def get_game_id(self, game_name):
        base_url = 'https://api.twitch.tv/helix'
        params = {
            'name': game_name,
            'first': 100
        }
        
        try:
            response = requests.get(f'{base_url}/games', headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data['data']:
                # If there are results for the original game name, return the game ID
                return data['data'][0]['id']

            # Remove number at the end of the game name (if present)
            game_name_no_number = re.sub(r'\s*\d+$', '', game_name)
            
            response = requests.get(f'{base_url}/games', headers=self.headers, params={'name': game_name_no_number, 'first': 100})
            response.raise_for_status()
            data = response.json()

            if data['data']:
                # If there are results after removing the number, return the game ID
                return data['data'][0]['id']

            # Remove sub-name after colon (if present)
            game_name_no_subname = re.sub(r'\s*:.+', '', game_name_no_number)

            response = requests.get(f'{base_url}/games', headers=self.headers, params={'name': game_name_no_subname, 'first': 100})
            response.raise_for_status()
            data = response.json()

            if data['data']:
                # If there are results after removing the sub-name, return the game ID
                return data['data'][0]['id']
            
            # Remove content inside parentheses (if present)
            game_name_no_parentheses = re.sub(r'\s*\([^)]*\)', '', game_name_no_subname)

            response = requests.get(f'{base_url}/games', headers=self.headers, params={'name': game_name_no_parentheses, 'first': 100})
            response.raise_for_status()
            data = response.json()

            if data['data']:
                # If there are results after removing the content inside parentheses, return the game ID
                return data['data'][0]['id']

            # If no results found, return None
            return None

        except requests.exceptions.RequestException as e:
            print(f'Error occurred: {e}')
            return None


    def get_popular_streams(self, game_name, limit=10):
        game_id = self.get_game_id(game_name)
        
        if not game_id:
            print(f'Failed to retrieve game ID for {game_name}')
            return None
        
        base_url = 'https://api.twitch.tv/helix'
        params = {
            'game_id': game_id,
            'first': limit
        }
        
        try:
            response = requests.get(f'{base_url}/streams', headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract information from the response
            return_data = []
            streams = data['data']
            for stream in streams:
                streamer_name = stream['user_name']
                stream_title = stream['title']
                viewer_count = stream['viewer_count']
                return_data.append((streamer_name, stream_title, viewer_count))

            return return_data
                
        except requests.exceptions.RequestException as e:
            print(f'Error occurred: {e}')
            return None
    



class APICache:
    def __init__(self, cache_file='api_cache.json'):
        self.cache_file = cache_file
        self.data = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as file:
                return json.load(file)
        return {}
    
    def get(self, key):
        if key not in self.data:
            return None 
        else:
            return self.data[key]


    def set(self, key, value):
        self.data[key] = value

    def save_cache(self):
        with open(self.cache_file, 'w') as file:
            json.dump(self.data, file, indent=4)


