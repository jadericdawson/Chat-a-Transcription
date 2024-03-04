from ytmusicapi import YTMusic
import webbrowser
import youtube_music


def play_music(query):
    yt = YTMusic('oauth.json')
    #playlistId = yt.create_playlist('Jarvis', 'Songs from the AI powered Jarvis')

    playlist = yt.get_library_playlists(limit = 3)
    # Loop through each playlist in the list
    for pl in playlist:
        if pl['title'] == 'Jarvis':
            playlistId = pl['playlistId']
            break  # Exit the loop once the Jarvis playlist is found
    search_results = yt.search(query)    

    yt.add_playlist_items(playlistId, [search_results[1]['videoId']])

    # Get the videoId from the search results
    video_id = search_results[1]['videoId']

    # Construct the YouTube Music URL
    youtube_music_url = f"https://music.youtube.com/watch?v={video_id}"

    # Open the URL in a web browser
    webbrowser.open(youtube_music_url)

#play_music('aerosmith')