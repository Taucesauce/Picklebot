from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import spotipy.util as util
import praw
import configparser as ConfigParser
from configparser import NoSectionError, NoOptionError

#TODO Add webhandler extention for GAE utility
def main():
    bot = Picklebot()
    results = bot.request_playlist()
    bot.post_to_reddit(results)
    
class Picklebot():
    def request_playlist(self):
        config = ConfigParser.RawConfigParser()
        config.read('settings.cfg')
        token = None

        #Gets Spotify API credentials from the settings.cfg
        SPOTIFY_USER = config.get('Spotify OAuth', 'SPOTIFY_USER')
        SPOTIFY_SCOPE = config.get('Spotify OAuth', 'SPOTIFY_SCOPE')
        SPOTIFY_CLIENT_ID = config.get('Spotify OAuth', 'SPOTIFY_CLIENT_ID')
        SPOTIFY_SECRET = config.get('Spotify OAuth', 'SPOTIFY_SECRET')
        SPOTIFY_URL = config.get('Spotify OAuth', 'SPOTIFY_URL')

        #Retrieve token from spotify api and then get an instance of the spotipy class wrapping the api.
        token = util.prompt_for_user_token(SPOTIFY_USER, SPOTIFY_SCOPE, SPOTIFY_CLIENT_ID, SPOTIFY_SECRET, SPOTIFY_URL)
        sp = spotipy.Spotify(auth=token)
        #Share link for thepicklejar playlist, extrapolate the id's to pass when retrieving the object from the api.
        uri = 'spotify:user:1257163432:playlist:0RvjVC3UO1nO75hA5yME9c'
        username = uri.split(':')[2]
        playlist_id = uri.split(':')[4]

        #results is the full object retrieved from the Spotify api, filtered by the "fields" parameter so we only get back information we care about.
        results = sp.user_playlist(username, playlist_id, fields="external_urls, tracks.items(added_at, track(name, artists, popularity))")
        return results

    def post_to_reddit(self, results):
        config = ConfigParser.RawConfigParser()
        config.read('settings.cfg')

        #Gets Reddit API credentials from the settings.cfg
        REDDIT_USERNAME = config.get('Reddit OAuth', 'REDDIT_USERNAME')
        REDDIT_PW = config.get('Reddit OAuth', 'REDDIT_PW')
        REDDIT_USER_AGENT = config.get('Reddit OAuth', 'REDDIT_USER_AGENT')
        REDDIT_CLIENT_ID = config.get('Reddit OAuth', 'REDDIT_CLIENT_ID')
        REDDIT_CLIENT_SECRET = config.get('Reddit OAuth', 'REDDIT_CLIENT_SECRET')

        #Grab an instance of the reddit class from praw
        reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                             client_secret=REDDIT_CLIENT_SECRET,
                             password=REDDIT_PW,
                             user_agent=REDDIT_USER_AGENT,
                             username=REDDIT_USERNAME)
        #Get the /r/spotify subreddit from praw
        pickleInstance = reddit.subreddit('spotify')


        #Trim the response into more digestible data structures, could probably just be done from the results object if I was better at python :)
        tracks = results['tracks']
        trackNames = []
        trackPop = []
        trackDates = []
        trackDict = {}

        #Honestly, this was a lot of guess and check to access the spotify api object, can only assume there's a better way.
        for i, trackHolder in enumerate(tracks.items()):
            for j, track in enumerate(trackHolder[1]):
                trackDates.append(track['added_at'])
                trackNames.append(track['track']['name'])
                trackPop.append(track['track']['popularity'])
                trackDict[track['track']['name']] = track['track']['artists'][0]['name']

        #Sorts the data by most popular song and grabs the top 3 songs in the playlist for the week.
        top3 = sorted(zip(trackPop,trackNames), reverse=True)[:3]
        top3Artists = []

        #Gets the artist responsible for the top 3 songs and adds their name to a dict.
        for i, name in top3:
            top3Artists.append(trackDict[name])

        #Builds the week's title using the most popular artists and submits it to reddit!
        postTitle = "This Week on The Pickle Jar: %s, %s, %s, and more!" %(top3Artists[0], top3Artists[1], top3Artists[2])
        pickleInstance.submit(postTitle, url=results['external_urls']['spotify'])
if __name__ == '__main__':
    main()
