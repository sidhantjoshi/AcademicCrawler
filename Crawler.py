from bs4 import BeautifulSoup
import urllib
from urllib.request import urlopen
from urllib.parse import urlparse
import requests
import traceback    

def getCurrentLocationStack(current_url):    
    """
    Converts a URL into an array where each element is demarcated by a '/'
    current_url: URL to be converted into an array
    Returns: An array representation of the URL
    """
    print('URL: ',current_url)
    protocol_index = current_url.find('://')
    if protocol_index == -1:
        location_stack = current_url.split('/')
    else:
        location_stack = current_url[protocol_index + len('://') : ].split('/')
        location_stack[0] = current_url[:protocol_index] + '://' + location_stack[0]
    
    while location_stack[0] == '':
        del location_stack[0]
    
    while location_stack[-1] == '':
        del location_stack[-1]
        
    print('URL in stack form: ',location_stack)
    return location_stack

def findCommonParent(sitemap, location_stack, query):
    """
    Given the sitemap, the current location and query, this function finds the 
    common parent (if any) to the current location and the query passed.
    sitemap: An instance of the sitemap
    location_stack: current location
    query: The URL whose common parent is to be found
    Returns: A two-tuple containing the parts of the query not in the sitemap 
            and the location in the sitemap where they are to be inserted
    """    
    parts=None
    if '://' in query:
        index = query.find('://') + 3
        parts = query[index:].split('/')
        parts[0] = query[:index] + parts[0]
    else:
        parts = query.split('/')
    
    while parts and parts[0] == '':
        del parts[0]
        if len(location_stack) > 1:
            location_stack = location_stack[:1]
    
    while parts and parts[-1] == '':
        del parts[-1]
        
    if (not parts) or parts[0] not in location_stack:
        index = -1
    else:
        index = location_stack.index(parts[0])
        for part in parts:
            if part in location_stack[index+1:]:
                index = location_stack.index(part)
    
    #print(location_stack[:index+1])
    
    for i in range(index+1):
        sitemap = sitemap[location_stack[i]]
    
    #print(sitemap)
    if index is not -1:
        not_in_sitemap = parts[parts.index(location_stack[index])+1:]
        return (not_in_sitemap, sitemap)
    else:
        #When a relative URL is used.
        if not bool(urlparse(query).netloc):
            for part in location_stack:
                sitemap = sitemap[part]
        
        return (parts, sitemap)    
    
def addToSitemap(sitemap, query):
    """
    Adds the query (in array form) to the sitemap.
    sitemap: An instance of the sitemap pointing to the location where the 
            query URL is to be added.
    query: The query URL in array form
    Returns: None
    """
    for part in query:
        sitemap[part] = sitemap.get(part, {})
        sitemap = sitemap[part]

def driver(sitemap, query, location_stack, absolute_urls):    
    """
    A driver function which adds query URLs to the sitemap.
    sitemap: An instance of the sitemap.
    query: The query URL to be added.
    location_stack: The current location in the sitemap.
    absolute_urls: A list which keeps of all the absolute URLs encountered.
            Absolute URLs are not processed by this function.
    """
    query = urllib.parse.unquote_plus(urllib.parse.unquote_plus(query))
    #Absolute URLs
    #Cannot be dealt with, from within the context of the current page
    #Is processed separately
    if bool(urlparse(query).netloc):
        absolute_urls.append(query)
        return
    #Protocol not specified, ignoring URL
    elif 'www' in query:
        return
    #Link to the same page
    if query.startswith('#'):
        return
    
    if 'mailto' in query:
        query = query[:query.find('mailto')]
        
    '''
    #Ignoring GET arguments
    if '?' in query:
        query = query[:query.find('?')]
    '''
    
    (not_in_sitemap, location_in_sitemap) = findCommonParent(sitemap, location_stack[:], query=query)
    addToSitemap(location_in_sitemap, not_in_sitemap)    
    
def processPage(sitemap, url, location_stack, absolute_urls):        
    """
    Function which is used to process all the links (<a>) on a given page.
    sitemap: An instance of the sitemap.
    url: The URL of the page to be processed.
    location_stack: The current location in the sitemap.
    absolute_urls: A list which keeps of all the absolute URLs encountered. 
    """
    try:
        r=urlopen(url).read()
        soup=BeautifulSoup(r, 'html.parser')    
        li=soup.find_all("a")
        
        for item in li:
            try:
                link = item["href"]
                driver(sitemap, link, location_stack, absolute_urls)
            except KeyError as k:
                print('Key Error: ', k, item)
                
    except urllib.error.HTTPError as e:
        print(e)
    except urllib.error.URLError as e:
        print(e)
    except Exception as e:
        print('General exception: ', traceback.print_exc())

def returnText(url):
    """
    Function which is used to return all the text in a given page.
    Will be replaced by a more sophisticated function later
    url: The URL of the page to be processed.
    Returns: the text in the page.    
    """
    try:
        r=urlopen(url).read()
        soup=BeautifulSoup(r, 'html.parser')
        return soup.text
    
    except urllib.error.HTTPError as e:
        print(e)
    except urllib.error.URLError as e:
        print(e)
    except Exception as e:
        print('General exception: ', traceback.print_exc())
    
def process(sitemap, base_url):
    """
    Function which is used to construct a sitemap based on a given page.
    sitemap: An instance of the sitemap already constructed. Can be empty.
    base_url: The URL of the page to be processed.    
    """
    #To deal with redirects
    response = requests.get(base_url)
    base_url = response.url    
         
    #Gets the current location ie the base_url in array form
    location_stack = getCurrentLocationStack(base_url)

    absolute_urls = []
    #Adds the current URL to the sitemap
    addToSitemap(sitemap, location_stack)
    #Processes all the links (other than absolute URLs) in the page
    processPage(sitemap, base_url, location_stack, absolute_urls)    
    
    #Processes the absolute URLs
    for url in absolute_urls:
        temp_stack = getCurrentLocationStack(url)        
        addToSitemap(sitemap, temp_stack)
        
#The code below was used only for testing purposes.
def formURL(arr):
    """
    Function used for testing purposes only.
    """
    url = arr[0]
    for part in arr[1:]:
        url+='/'+part
    return url

def processWebsite(sitemap, arr, level):
    """
    Function used for testing purposes only.
    """
    if not sitemap:
        print(formURL(arr[:level]))
        return
    for key in sitemap.keys():
        arr[level] = key
        processWebsite(sitemap[key], arr, level+1) 

def constructURL(sitemap, query):
    """
    Function used for testing purposes only.
    """
    if query in sitemap.keys():        
        return query
    for key in sitemap.keys():
        if constructURL(sitemap[key], query):            
            return key+'/'+constructURL(sitemap[key], query)
    return False

def getTree(sitemap, query):
    """
    Function used for testing purposes only.
    """
    if query in sitemap.keys():
        return sitemap
    for key in sitemap.keys():
        val =  getTree(sitemap[key], query)
        if val:
            return val
    return False

def getTreeDriver(sitemap, query):
    """
    Function used for testing purposes only.
    """
    #To deal with absolute URLs
    parts=None
    if '://' in query:
        index = query.find('://') + 3
        parts = query[index:].split('/')
        parts[0] = query[:index] + parts[0]
    else:
        parts = query.split('/')
            
    for part in parts[:-1]:        
        sitemap = getTree(sitemap, part)        
        if not sitemap:
            return False
        sitemap = sitemap[part]
    
    if parts[-1] in sitemap.keys():
        return sitemap
    else:
        return False
    
def getLevelInTree(sitemap, query, level):
    """
    Function used for testing purposes only.
    """
    if query in sitemap.keys():
        return level
    for key in sitemap.keys():
        val =  getLevelInTree(sitemap[key], query, level+1)
        if val:
            return val
    return False

def getLevelInTreeDriver(sitemap, query, level):
    """
    Function used for testing purposes only.
    """
    #To deal with absolute URLs
    parts=None
    if '://' in query:
        index = query.find('://') + 3
        parts = query[index:].split('/')
        parts[0] = query[:index] + parts[0]
    else:
        parts = query.split('/')
    
    for part in parts:              
        level = getLevelInTree(sitemap, part, level)        
        level+=1        
        sitemap = getTree(sitemap, part)  
        if not sitemap:
            return False
        sitemap = sitemap[part]
    
    return level-1  
