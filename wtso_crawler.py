import urllib
import re
from collections import deque
import collections

CACHE_DIR = "cache_wtso/"
EPISODE_CACHE = CACHE_DIR + "episode_set.txt"

regexEpisodeName = re.compile('movie/([^\.]+)\.html')
regexSeasonURLs = re.compile('(http://www.wtso.net/cat/\d+\.html)')
regexEpisodeURLs = re.compile('(http://www.wtso.net/movie/[^\.]+\.html)')

#http://www.wtso.net/movie/505-2222_The_NedLiest_Catch.html

#===============================================================================
# Helpers
#===============================================================================

def lawg(str):
    print str
    
def get_match(regex, str):
    match = regex.search(str)
    if match:
        return match.group(1).strip()
    else:
        return None
    
#===============================================================================
# Caching    
#===============================================================================

def cache_write(url, content):
    with open(filename_for(url), 'w') as f:
        f.write(content)
    
def cache_lookup(url):
    return get_contents_for(filename_for(url))
    
def get_contents_for(filename):
    content = None
    try:
        f = open(filename, 'r')
        content = f.read()
    except IOError:
#        lawg("File doesn't exist!")
        content = None
    except:
        lawg("Other error reading file [" + str(filename) + "]")
        content = None
    return content
    
def filename_for(url):
    episode = get_match(regexEpisodeName, url)
    if episode:
        return CACHE_DIR + episode + ".txt"
    else:
        lawg("Could not find filename for url [" + url + "]")
        return None
    
def write_set_cache(set_cp, filename):
    # copy the set so we don't end up destroying (how do references work in python?)
    s = set_cp.copy()
    with file(filename, 'w') as f:
        while len(s) > 0:
            f.write(s.pop() + "\n")
        f.flush()

def read_set_cache(filename):
    s = set()
    try:
        f = open(filename, 'r')
        for line in f:
            s.add(line)
    except:
        lawg("Cache does not exist")
    return s
            
def get_season_episode_set(season_queue):
    # just for fun, to see how useful the set collection is
    episodes_added = 0
    ep_set = set()  
    
    # Go through each season page in the queue
    while season_queue:
        # Pop a season from the queue
        season_url = season_queue.pop()
        
        # Get the season list page's content
        season_content = urllib.urlopen(season_url).read()
        
        # Go through all episode links on the season list page
        for ep in regexEpisodeURLs.findall(season_content):
            # Add each episode to the set (which will filter out the dupes)
            ep_set.add(ep)
            # Track how many episodes we've added (again, just for fun)
            episodes_added += 1
    
    print "Looked at [" + str(episodes_added) + "] episode links and filtered down to [" + str(len(ep_set)) + "]"
    return ep_set
            
#===============================================================================
# Episode List
#===============================================================================

# Start by reading in all the Season URLs into a queue
start = "http://www.wtso.net/cat/1.html"
season_queue = deque(regexSeasonURLs.findall(urllib.urlopen(start).read()))

# create a set of episode URLs (so we don't repeat any)
episode_set = read_set_cache(EPISODE_CACHE)

if not episode_set or len(episode_set) is 0:
    # could not read in, so go through and create a new one (takes time)
    episode_set = get_season_episode_set(season_queue)
    
# Cache episode set so we don't have to do that again!
write_set_cache(episode_set, EPISODE_CACHE)

#===============================================================================
# Parse Episodes
#===============================================================================
while len(episode_set) > 0:
    # Get an episode URL to look at
    current = episode_set.pop().strip()
    
    # reset loop variables
    html = None
    should_cache = True
    
    # try to find a cached version of the current URL
    html = cache_lookup(current)
    
    if html:
        lawg("Cache Hit [" + current + "]")
        should_cache = False
    else:
        # if not find cache, try to request the page
        html = urllib.urlopen(current).read()
        lawg("Cache Miss. Requesting [" + current + "]")
        
    if html:
        # Parse for whatever it is that we want out of this ..........
        
        if should_cache:
            # save this content so we don't have it in our cache
            cache_write(current, html)
    else:
        lawg("No content found")
