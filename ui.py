from graph import *
from api import TwitchAPI

def display_similar_users(similar_users):
    print("\nTop 3 similar users in your friend network:")
    print("------------------------------------------------------------")
    num = 1
    for item in similar_users:
        print(f"{num}. User ID: {item[0]}, Similarity Score: {item[1]}")
        num += 1

def display_recommended_games(recommended_games, similar_users):
    similar_user = similar_users[0][0]
    print(f"\nTop 5 most played games of your most similar friend (ID: {similar_user}):")
    print("------------------------------------------------------------")
    num = 1
    for item in recommended_games:
        print(f"{num}. {game_name_mapping[str(item['appid'])]},\tYour friend's playtime: {item['playtime_forever']}")
        num += 1

def display_twitch_info(twitch_api, game_name):
    popular_streams = twitch_api.get_popular_streams(game_name, limit=5)
    if not popular_streams:
        print(f"\nSorry, no streams currently available for game {game_name}\n")
        return 
    
    print(f"\nTop steams for game {game_name}")
    print("------------------------------------------------------------")
    num = 1
    for item in popular_streams:
        print(f"{num}. Streamer Name: {item[0]}, Title: {item[1]}, Views: {item[2]}")
        num += 1

def display_recommended_genres(genres):
    print("\nTop 5 recommended genres based on your friends network:")
    print("------------------------------------------------------------")
    num = 1
    for item in genres:
        print(f"{num}. Genre: {item[0]}, Relevance Score: {item[1]}")
        num += 1



root = list(user_friend_graph.keys())[0]
g = build_graph(user_friend_graph, user_game_mapping)

propagate_interests(g[root])
similar_users = recommend_users(g, root, 3)
similar_user = similar_users[0][0]
recommended_games = recommend_games(similar_user, 5)
recommended_genres = recommend_genres(g[root].interests, 5)
twitch_api = TwitchAPI("key.conf")


# Command-line interface
while True:
    print("\n--- Game Recommendation System ---")
    print("1. Display Similar Users")
    print("2. Display Recommended Games")
    print("3. Display Recommended Games Genres")
    print("4. Exit")

    choice = input("Enter your choice (1-4): ")

    if choice == "1":
        display_similar_users(similar_users)
    elif choice == "2":
        is_first_time = True
        while(True):
            display_recommended_games(recommended_games, similar_users)
            if is_first_time:
                interested_num = input("Which of the above games are you interested in (0 for not interested)? ")
            else:
                interested_num = input("Which else of the above games are you interested in (0 for not interested)? ")
            if interested_num == "0":
                break
            try:
                game_name = game_name_mapping[str(recommended_games[int(interested_num) - 1]['appid'])]
                display_twitch_info(twitch_api, game_name)
                is_first_time = False
            except:
                print("Invalid choice. Please try again.")
    
    elif choice == "3":
        display_recommended_genres(recommended_genres)

    elif choice == "4":
        print("Exiting...")
        break
    else:
        print("Invalid choice. Please try again.")