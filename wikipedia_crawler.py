import urllib
import re
from collections import deque
import collections
from urllib import FancyURLopener
from BeautifulSoup import BeautifulSoup

CACHE_DIR = "cache_wikipedia/"

regexEpisodeNum = re.compile('>[\d]+[\W]([\d]+)<')
regexEpisodeTitle = re.compile('"<b><a[^>]+>([^<]+)</a></b>"')
regexEpisodeDesc = re.compile('<td.+?description[^>]+>(.+?)</td>', re.DOTALL)
regexDirectors = re.compile('<tr.+?vevent.+?<td.+?<td.+?<td>(.+?)</td>', re.DOTALL)
regexWriters = re.compile('<tr.+?vevent.+?<td.+?<td.+?<td>.+?<td>(.+?)</td>', re.DOTALL)
regexContributorsSplit = re.compile('&amp;| and|,')

#===============================================================================
# Opener
#===============================================================================
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'

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
    
def get_contributors(str):
    return split(clean(str.replace("<br />", ",")))    
    
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
    return CACHE_DIR + url[29:] + ".html"

def clean(str):
    # remove HTML tags by turning it all into text
    str = ''.join(BeautifulSoup(str).findAll(text=True)).encode('utf-8')
    # remove wikipedia citation boxes
    str = re.sub('\[\d+\]', '', str)
    # remove "Guest star" info (for now)
    str = re.sub('Special Guest', 'Guest', str)
    str = re.sub('[Gg]uest [Ss]tars?:.+', '', str)
    # remove &nbsp; at end
    str = re.sub('&#160;', '', str)
    # replace all whitespace (multiple spaces, newlines, etc) with a single space
    str = re.sub('[\s+]', ' ', str)
    # finally, just strip for fun
    return str.strip()
#    return lxml.html.fromstring(str).text_content()

def split(str):
    return regexContributorsSplit.split(str)

def output(season, episode, title, desc):
    with open("output_wikipedia.txt", 'a') as f:
        f.write(str(season) + "\t" + str(episode) + "\t" + title + "\t" + clean(desc) + "\n")

def output_contributors(season, episode, contributor, type):
    if len(contributor) > 0:
        with open("output_contributors_episodes.txt", 'a') as f:
            f.write(str(season) + "\t" + str(episode) + "\t" + contributor + "\t" + type + "\n")
            
def output_contributor(contributor):
    if len(contributor) > 0:
        with open("output_contributors.txt", 'a') as f:
            f.write(contributor + "\n")
            
#===============================================================================
# Episode List
#===============================================================================

set_contributors = set()
        
season = 1
while (season < 23):
    # reset loop variables
    current = "http://en.wikipedia.org/wiki/The_Simpsons_(season_" + str(season) + ")"
    html = None
    should_cache = True
    
    # try to find a cached version of the current URL
    html = cache_lookup(current)
    
    if html:
        lawg("Cache Hit [" + current + "]")
        should_cache = False
    else:
        # if not find cache, try to request the page
        myopener = MyOpener()
        html = myopener.open(current).read()
        lawg("Cache Miss. Requesting [" + current + "]")
        
    if html:
        # Parse for whatever it is that we want out of this ..........
        ep_titles = regexEpisodeTitle.findall(html)
        ep_descs = regexEpisodeDesc.findall(html)
        ep_directors = regexDirectors.findall(html)
        ep_writers = regexWriters.findall(html)
        
        for i in range(len(ep_titles)):
            episode = i + 1
            
            #output(season, episode, ep_titles[i], ep_descs[i + 1])
            
            directors = get_contributors(ep_directors[i])
            writers = get_contributors(ep_writers[i])
            
            for x in range(len(directors)):
                director = clean(directors[x])
                output_contributors(season, episode, director, 'director')
                set_contributors.add(director)
            for x in range(len(writers)):
                writer = clean(writers[x])
                output_contributors(season, episode, writer, 'writer')
                set_contributors.add(writer)
                            
            #print str(season) + "\t" + str((i+1)) + "\t" + str(len(ep_directors)) + "\t" + str(len(ep_writers))
                
        if should_cache:
            # save this content so we don't have it in our cache
            cache_write(current, html)
    else:
        lawg("No content found")
        
    season += 1

while (len(set_contributors) > 0):
    contributor = set_contributors.pop()
    output_contributor(contributor)
