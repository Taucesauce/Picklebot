from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import spotipy.util as util
import praw
import ConfigParser as ConfigParser
from ConfigParser import NoSectionError, NoOptionError
from datetime import datetime

#TODO Add utility for other social media platforms
def main():
    bot = Picklebot()
    results = bot.request_playlist()
    bot.post_to_reddit(results)

#A couple of helper methods for parsing the date information returned by Spotify
def check_dates(dates):
    for i, date in enumerate(dates):
        if(days_since_update(date) > 1):
            return False
    return True

def days_since_update(d1):
    d1Date = d1.split('T')[0]
    d1Time = d1.split('T')[1]
    d1Time = d1Time.split('Z')[0]

    d1 = datetime.strptime(d1Date + " " + d1Time, '%Y-%m-%d %H:%M:%S')
    return abs((datetime.now() - d1).days)

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
        client_credentials_manager = SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
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
        pickleInstance = reddit.subreddit('thepicklejar')


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

        #Checks if the newest tracks have been added to the playlist.
        if(check_dates(trackDates)):
            postTitle = "This Week on The Pickle Jar: %s, %s, %s, and more!" %(top3Artists[0], top3Artists[1], top3Artists[2])

            #Checks to make sure a post of the same name has not already been posted to the subreddit (don't want to spam the subreddit!)
            searchResults = pickleInstance.search(postTitle,"relevance","cloudsearch", "month")
            alreadyPosted = False

            #Should only be one
            for submission in searchResults:
                alreadyPosted = True

            #Finally posts to reddit if all the criteria are met.
            if (not alreadyPosted):
                pickleInstance.submit(postTitle, url=results['external_urls']['spotify'])
                print("Posted")
            else:
                print("Already Posted")
        else:
            print("Too old")

if __name__ == '__main__':
    main()
