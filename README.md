# Checkpoint report 

*Fangqing Lin*



## Project code

https://github.com/KathrynLin/SI507-FinalProject



## Data source

### Steam data

- **Origin:** Steam data is obtained using the Steam Web API (https://developer.valvesoftware.com/wiki/Steam_Web_API). Specifically, AppDetails is used to get detail description of an app, GetOwnedGames is used to get a list of games a user owns, and GetFriendList is used to get a list of friends of a user.

- **Format:** JSON

- **Cache:** Cache is used to store the owned games, the friends list, and the related games (games that his/her friends and friends of friends own). The cache is organised as a class in memory and a json file on disk:

  ```python
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
  ```

  Caching is important because retrieving information with api is slow (1 second per access). By storing the retrieved information into the cache, no repeated api access is needed.

- **Data summary:** 

  - *# records available:* All games on Steam Store, over 50,000.
  - *# records retrieved:* The `related_games` field includes games of one's friends, friends of friends, friends of friends of friends, etc. Hence, the size of `related_games` depends on the depth one wants to discover. If depth is set to 2, number of related games is roughly 270.
  - *Description:* The `users` field in the cache file contains information specific to a user, including `owned_games`, `friends_list`, and `related_games`. The `apps` field containes detailed information of a game, with `name` the game name, `detailed_description` the description of the game, and `recommend` the number of recommendations.

### Twitch data

- **Origin:** Twitch data is obtained using the Twitch API (https://dev.twitch.tv/docs/api/). Specifically, SearchCategory is used to search games by names, and GetVideos is used to get a list of videos of a given game.
- **Format:** JSON
- **Cache:** Cache is the same as in "Steam data" section.
- **Data summary:** 
  - *# records available:* All games on Twitch, over 10,000.
  - *# records retrieved:* Same order as `related_games`, roughly 270.
  - *Description:* The `maps` field in the cache file contains mappings from steam app ID to Twitch app ID. The `videos` field containes a list of videos of a given game (indicated by the key) on twitch.



## Data structure

I will implement a graph data structure where each game will be represented as a node. The connections between nodes will be established based on similarity measures, such astextual similarity of descriptions, and sentiment analysis of user reviews. With the graph constructed, I will develop a recommendation algorithm that utilizes graph traversal techniques based on breadth-first search (BFS) or depth-first search (DFS), to explore the graph and identify games that are similar to a user's preferences. 

The screenshot below is used to evalued the cosine similarity between two paragraphs.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity_score(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    
    similarity_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

    return similarity_score
```


## Interaction and presentation plans

The game recommendation system will be implemented as a web application implemented with Flask. Users can enter their Steam ID and a graph of recommended games will be shown on the application. On each node, users can gain information such as  title, description, genre, release date, user reviews, Twitch streams and videos. 

The game recommendation system will provide various interaction functionalities to enhance user engagement and improve recommendation accuracy. These interactions will be facilitated through the web application. Users will be able to explore a list of popular live streams on Twitch, based on the games in their Steam library as well as the games recommended to them. The system will generate personalized game recommendations based on a user's profile, playtime history, preferred genres, friends' activities, and popular games within their network. 