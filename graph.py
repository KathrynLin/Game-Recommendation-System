import numpy as np
import json

### load cache
with open("api_cache.json") as f:
        cache = json.load(f)

user_friend_graph = cache["user_friend_graph"]
user_game_mapping = cache["user_game_mapping"]
game_detail = cache["game_detail"]
game_name_mapping = {}
game_interests_mapping = {}

for game_id, detail in game_detail.items():
    # print(game_id)
    if not detail:
        continue
    if "name" not in detail:
        game_name_mapping[game_id] = []
    
    game_name_mapping[game_id] = detail['name']


for game_id, detail in game_detail.items():
    # print(game_id)
    if not detail:
        continue
    if "genres" not in detail:
        game_interests_mapping[game_id] = []
        continue
    
    genres = [item["description"] for item in detail["genres"]]
    game_interests_mapping[game_id] = genres



class Node:
    '''
    Represents a node in the graph. This node could represent a user in a social network.

    Attributes:
    ----------
    id : str
        The unique identifier for this node.
    friends : list
        The list of friends(nodes) that are connected to this node.
    interests : list
        The list of interests that this node has.
    '''
    def __init__(self, id):
        self.id = id
        self.friends = []
        self.interests = []

    def add_friend(self, friend):
        self.friends.append(friend)

    def set_node_interests(self, interests):
        self.interests = interests

    def is_game_node(self):
        '''
        Check if current node is a game node.

        Returns:
        --------
        bool
            False for basic Node instances, overridden in derived classes.
        '''
        return False

    

class GameNode(Node):
    '''
    Represents a game node in the graph, derived from Node class.

    Attributes:
    ----------
    num_owned : int
        The number of times this game is owned by users within the network.
    '''
    def __init__(self, id):
        super().__init__(id)
        self.num_owned = 1
    
    def set_node_interests(self, interests, play_time):
        '''
        Set the interests for this game node with an adjustment based on play time.

        Parameters:
        -----------
        interests : list
            The list of interests or genres associated with this game.
        play_time : int
            The amount of time this game has been played by the user.
        '''
        def modified_sigmoid(x):
            return 0.5 * (1 / (1 + np.exp(-0.001*x))) + 0.5
        
        if len(self.interests) == 0:
            for interest in interests:
                self.interests.append((interest, modified_sigmoid(play_time)))
        else:
            score_total = self.interests[0][1] * self.num_owned
            self.num_owned += 1
            for interest in interests:
                self.interests.append((interest, (score_total + modified_sigmoid(play_time))/self.num_owned))
    
    def is_game_node(self):
        '''
        Check if current node is a game node.

        Returns:
        --------
        bool
            True for GameNode instances.
        '''
        return True



def build_graph(user_friend_graph, user_game_mapping):
    '''
    Build a graph based on the user friend relationships and game preferences.

    Parameters:
    -----------
    user_friend_graph : dict
        A dictionary representing the user friend relationships.
    user_game_mapping : dict
        A dictionary mapping users to their preferred games.

    Returns:
    --------
    dict
        A graph represented as a dictionary mapping user IDs to their corresponding Node instances.
    '''
    node_dict = {}
    game_dict = {}

    # Create graph nodes for each user and assign game leaves
    for user in user_friend_graph:
        node_dict[user] = Node(user)

        for g in user_game_mapping[user]:
            if g["appid"] in game_dict:
                game_node = game_dict[g["appid"]]
            else:
                game_node = GameNode(g["appid"])
                game_dict[g["appid"]] = game_node
            game_node.set_node_interests(get_game_interests(str(g["appid"])), g["playtime_forever"])
            node_dict[user].add_friend(game_node)

    # Connect the user nodes based on the friend relationships
    for user, friends in user_friend_graph.items():
        for friend in friends:
            node_dict[user].add_friend(node_dict[friend])

    # Return the root user
    return node_dict



def propagate_interests(node, visited=None):
    '''
    Propagate interests from the given node to its friends.

    Parameters:
    -----------
    node : Node
        The node whose interests will be propagated.
    '''
    if visited is None:
        visited = set()

    # Base case: If the node is a game leaf, return its interests
    if not node.friends:
        return 

    # Recursive case: Propagate interests from friend nodes
    friends_except_visited = []
    visited.add(node)  # Mark the current node as visited

    for friend in node.friends:
        if friend not in visited:  # Skip already visited friends
            propagate_interests(friend, visited)
            friends_except_visited.append(friend)

    # Perform aggregation (e.g., weighted voting or averaging)
    aggregated_interests = perform_aggregation(friends_except_visited)

    # Store the aggregated interests in the node
    node.set_node_interests(aggregated_interests)





def get_game_interests(game_id):
    '''
    Retrieves the interests associated with a given game ID.

    This function looks up the interests (such as genres or features) of a game based on its unique identifier. 
    It utilizes a mapping dictionary that links game IDs to their corresponding interests.

    Parameters:
    -----------
    game_id : str
        The unique identifier of the game.
        
    Returns:
    --------
    list
        A list of interests for the given game ID, or an empty list if not found
    '''
    return game_interests_mapping.get(game_id, [])  



def perform_aggregation(nodes):
    '''
    Performs aggregation of interests from a given list of nodes in a graph.

    This function is designed to aggregate interests from a mix of user and game nodes. It differentiates between these two types of nodes,
    compiles their interests, and then calculates an aggregated score for each interest. The aggregation takes into account the type of node 
    (game or user) and weights their interests accordingly.
    
    Parameters:
    -----------
    nodes : list
        A list of Node instances whose interests will be aggregated.
        
    Returns:
    --------
    list
        A list of tupples containing the interest and its aggregated score.
    '''
    aggregated_interests_tuple = []
    # Flatten the list of interests
    user_nodes = []
    game_nodes = []
    for node in nodes:
        if node.is_game_node():
            game_nodes.append(node)
        else:
            user_nodes.append(node)
    
    user_interests_tuple = [user_interest_tuple for user_node in user_nodes for user_interest_tuple in user_node.interests]
    game_interests_tuple = [game_interest_tuple for game_node in game_nodes for game_interest_tuple in game_node.interests]
    
    dic = {}

    for game_interest_tuple in game_interests_tuple:
        if game_interest_tuple[0] not in dic:
            dic[game_interest_tuple[0]] = [game_interest_tuple[1], 1]
            continue
        dic[game_interest_tuple[0]][0] += game_interest_tuple[1]
        dic[game_interest_tuple[0]][1] += 1

    for user_interest_tuple in user_interests_tuple:
        if user_interest_tuple[0] not in dic:
            dic[user_interest_tuple[0]] = [user_interest_tuple[1]*0.8, 1]
            continue
        dic[user_interest_tuple[0]][0] += user_interest_tuple[1]*0.8
        dic[user_interest_tuple[0]][1] += 1
    
    for interest, score in dic.items():
        aggregated_interests_tuple.append((interest, score[0]/score[1]))
    
    return aggregated_interests_tuple



def recommend_users(graph, root_user, num_recommendations=5):
    '''
    Recommend a list of users to the given user based on their interests.

    Parameters:
    -----------
    graph : dict
        A graph represented as a dictionary mapping user IDs to their corresponding Node instances.
    root_user : str
        The ID of the user to whom recommendations will be made.
    num_recommendations : int

    Returns:
    --------
    list
        A list of tupples containing the user ID and similarity score.
    '''
    root_interests = graph[root_user].interests

    # Collect similar users based on interests and scores
    similar_users = []
    for user, node in graph.items():
        if (user != root_user) and (len(user_game_mapping[user]) != 0):
            similarity = calculate_similarity(root_interests, node.interests)
            similar_users.append((user, similarity))

    similar_users = sorted(similar_users, key=lambda x: x[1], reverse=True)
    return similar_users[:num_recommendations]


def calculate_similarity(interests1, interests2):
    '''
    Calculate the cosine similarity between two interest dictionaries.

    Parameters:
    -----------
    interests1 : list
        The list of interests for the first user.
    interests2 : list
        The list of interests for the second user.

    Returns:
    --------
    float
        The cosine similarity between the two users.
    '''
    dot_product = sum(score1 * score2 for game1, score1 in interests1 for game2, score2 in interests2 if game1 == game2)
    magnitude1 = np.sqrt(sum(score ** 2 for _, score in interests1))
    magnitude2 = np.sqrt(sum(score ** 2 for _, score in interests2))
    similarity = dot_product / (magnitude1 * magnitude2) if magnitude1 * magnitude2 != 0 else 0.0

    return similarity


def recommend_games(user, recommend_num=3):
    '''
    Recommends games for a specific user based on playtime.

    This function sorts the games played by a user in descending order of playtime and returns the top games.
    It provides a simple way to identify which games a user spends the most time playing, suggesting these as recommendations.

    Parameters:
    -----------
    user : int
        The user ID for whom recommendations will be made.
    recommend_num : int
        The number of games to recommend.
        
    Returns:
    --------
    list
        A list of tupples containing the game ID and playtime.
    '''
    user_games = user_game_mapping[str(user)]
    user_games = sorted(user_games, key=lambda x: x["playtime_forever"], reverse=True)
    return user_games[:recommend_num]



def recommend_genres(interests, genre_num=3):
    '''
    Recommends genres based on a list of interests with associated relevance scores.

    This function sorts the genres based on their relevance scores in descending order and returns the top genres.
    It is useful for identifying which game genres might be most appealing to a user based on their interests.

    Parameters:
    -----------
    interests : list
        A list of tupples containing the genre and its relevance score.
    genre_num : int
        The number of genres to recommend.
        
    Returns:
    --------
    list
        A list of tupples containing the genre and its relevance score.
    '''
    interests = sorted(interests, key=lambda x: x[1], reverse=True)
    return interests[:genre_num]


