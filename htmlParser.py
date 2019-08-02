from bs4 import BeautifulSoup
import csv
from unidecode import unidecode
from activityAnalysis import *
import requests

def write_activity_to_csv(dic):
    for title in dic:
        if title.lower() == 'youtube':
            write_youtube(dic)
        elif title.lower() == 'search':
            write_search(dic)
        elif title.lower() == 'google analytics':
            write_analytics(dic)
        elif title.lower() == 'youtube.com':
            write_video(dic)

def write_video(dic):
    with open('GoogleVideoSearched.csv', 'w', newline = '') as fp:
        writer = csv.writer(fp)
        writer.writerow(dic.keys())
        writer.writerow(['Searched Video', 'Accessed Date'])
        for key in dic:
            for content in dic[key]:
                try:
                    writer.writerow([content['Searched Video'], content['Accessed Date']])
                except:
                    pass

def write_analytics(dic):
    with open('GoogleAnalytics.csv', 'w', newline = '') as fp:
        writer = csv.writer(fp)
        writer.writerow(dic.keys())
        writer.writerow(['Web Accessed', 'Accessed Date'])
        for key in dic:
            for content in dic[key]:
                try:
                    writer.writerow([content['Web Accessed'], content['Accessed Date']])
                except:
                    pass

def write_search(dic):
    with open('GoogleSearched.csv', 'w', newline = '') as fp:
        writer = csv.writer(fp)
        writer.writerow(dic.keys())
        writer.writerow(['Searched Keywords', 'Accessed Date'])
        for key in dic:
            for content in dic[key]:
                try:
                    writer.writerow([content['Searched Keywords'], content['Accessed Date']])
                except:
                    pass

def write_youtube(dic):
    with open('YouTubeWatched.csv', 'w', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(dic.keys())
        writer.writerow(['Name', 'Channel', 'Accessed Date', 'Link'])
        for key in dic:
            for content in dic[key]:
                try:
                    writer.writerow([content['Name'], content['Channel'], content['Accessed Date'], content['Link']])
                except:
                    pass


# def determineHTML(filename, content):
#     if 'device' in filename.lower():
#         phone_Info = extractPhoneInfoHtml(content)

#     elif 'bookmarks' in filename.lower():
#         bookmarks = extractBookMarksHtml(content)

#     elif 'myactivity' in filename.lower():
#         activity_dic = extractActivityHtml(content, filename.lower())
#         write_activity_to_csv(activity_dic)

#     elif 'youtube' and 'search' in filename.lower():
#         youtube_search_history_dic = extractYoutubeSearchHtml(content)

#     elif 'youtube' and 'comment' in filename.lower():
#         youtube_comment_dic = extractYoutubeCommentHtml(content)


# Returns a list of comments made by the user
def extractYoutubeCommentHtml(content):
    comments = []
    soup = BeautifulSoup(content, 'html.parser')
    content = []
    for tags in soup:
        try:
            content.append(tags.get_text())
        except:
            content.append(tags)
        comments.append(content)
    return comments

# Returns a dictionary with key as activity title and values as a list of dictionaries contains related tags
def extractYoutubeSearchHtml(content):
    search_result = {}
    result_tags = []

    activity_search, activity_title = readActivityHtml(content)

    for result in activity_search:
        search_dic = {}
        content = []

        for tag in result:
            try:
                content.append(tag.get_text())
            except:
                content.append(tag)
        try:
            content.append(result.a.get('href'))
        except:
            pass
        try:
            search_dic = {
                'Youtube Search Keywords': content[1],
                'Accessed Date': content[3]
            }
            result_tags.append(search_dic)
        except:
            pass

    search_result[activity_title] = result_tags
    return search_result

# Extract phone config -> A list of phone config
def extractPhoneInfoHtml(content):
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')

    phone_config = {}

    # Network & Services
    network_Dic = {} # dictionary for network and services
    network = tables[1].get_text().split('\n')[1:-2]
    for i in range(len(network) // 2):
        network_Dic[network[i]] = network[i + 7]

    # Device Config
    fingerprint = [] # Build Fingerprint
    product = [] # Product
    brand = [] # Brand

    config = tables[2].get_text().split('\n')[9:-2]
    for i in range(0, len(config), 8):
        if config[i + 1] != '':
            fingerprint.append(config[i + 1])
            product.append(config[i + 2])
            brand.append(config[i + 3])

    divs = soup.find_all('body')[0].get_text().split('\n')

    androidId = ''
    meid = ''
    imei = ''
    serialNum = ''


    locale = ''
    timezone = ''
    ip = ''
    screenDensity = ''
    screenHeight = ''
    screenWidth = ''
    numberProcessors = ''
    ram = ''
    maxDownload = ''
    updated = ''

    for div in divs:
        if 'Android ID' in div:
            androidId = div[12:]
        elif 'MEID' in div:
            meid = div[9:]
        elif 'IMEI' in div:
            imei = div[9:]
        elif 'Serial Number' in div:
            serialNum = div[18:]
        elif 'Locale:' in div:
            locale = div[7:]
        elif 'Timezone' in div:
            timezone = div[10:]
        elif 'IP address' in div:
            ip = div[38:]
        elif 'Screen Density' in div:
            screenDensity = div[16:]
        elif 'Screen Height' in div:
            screenHeight = div[15:]
        elif 'Screen Width' in div:
            screenWidth = div[14:]
        elif 'Number Of Available Processors' in div:
            numberProcessors = div[32:]
        elif 'Total Memory' in div:
            ram = div[14:]
        elif 'Maximum APK Download Size' in div:
            maxDownload = div[27:]
        elif 'OTA Installed Build' in div:
            updated = div[21:]

    if len(fingerprint) != 0:
        phone_config = {"Network Info" : network_Dic, "Brand" : brand[0], "Product Name" : product[0], "Android ID" : androidId, "MEID" : meid, "IMEI" : imei,
                        "Serial Number" : serialNum, "Locale" : locale, "Timezone" : timezone, "IP Address" : ip, "Screen Density" : screenDensity,
                        "Screen Height" : screenHeight, "Screen Width" : screenWidth, "Cores in Processor" : numberProcessors, "Total RAM" : ram,
                        "Maximum Cellular Download Size" : maxDownload, "Ever Updated" : updated, "Fingerprint" : fingerprint[0]}
        return phone_config
    else:
        phone_config = {"Network Info" : network_Dic, "Android ID" : androidId, "MEID" : meid, "IMEI" : imei, "Serial Number" : serialNum, "Locale" : locale,
                        "Timezone" : timezone, "IP Address" : ip, "Screen Density" : screenDensity, "Screen Height" : screenHeight, "Screen Width" : screenWidth,
                        "Cores in Processor" : numberProcessors, "Total RAM" : ram, "Maximum Cellular Download Size" : maxDownload, "Ever Updated" : updated}
        return phone_config

# Extract bookmarks -> list of bookmarks
def extractBookMarksHtml(content):
    soup = BeautifulSoup(content, 'html.parser')
    bookmarks = []

    bms = soup.find_all('a') # Title of Bookmarks
    for marks in bms:
        bookmarks.append(marks.get_text())

    return bookmarks

# All activity mathods returns a dictionary with key as titile of activity and values as a list of dictionaries with related tags
def extractActivityHtml(contents, filename):
    search_result = {}
    result_tags = []

    dismissedNews = []

    activity_search = []
    activity_title = []
    activity_location = []

    if '/search' or 'maps' in filename:
        activity_search, activity_title, activity_location = readActivityLocationHtml(contents)
    else:
        activity_search, activity_title = readActivityHtml(contents)

    print("READ5")

    for index in range(len(activity_search)):
        result = activity_search[index]
        search_dic = {}
        content = []

        for tag in result:
            try:
                content.append(tag.get_text())
            except:
                content.append(tag)
        try:
            content.append(result.a.get('href'))
        except:
            pass
        if 'video' in filename: # Youtube search history
            try:
                search_dic = {
                    'Searched Video': content[1],
                    'Accessed Date': content[3]
                }
                result_tags.append(search_dic)
            except:
                pass

        elif 'youtube' in filename: # Youtube watch history
            try:
                if len(content) == 7:
                    search_dic = {
                        'Name': content[1],
                        'Channel': content[3],
                        'Accessed Date': content[5],
                        'Link': content[6]
                    }
                result_tags.append(search_dic)
            except:
                pass

        elif 'gmail' in filename: # Gamil search history
            try:
                search_dic = {
                    'Content searched on Gmail': content[1],
                    'Accessed Date': content[3]
                }
                result_tags.append(search_dic)
            except:
                pass

        elif 'analytics' in filename: # Google analytics
            try:
                search_dic = {
                    'Web Accessed': content[1],
                    'Accessed Date': content[3]
                }
                result_tags.append(search_dic)
            except:
                pass

        elif '/search' in filename:
            location = activity_location[index]
            try:
                location = location.a.get('href')
                location = parseLocation(location)
                location[0] = round(float(location[0]), 4)
                location[1] = round(float(location[1]), 4)
                location = analyzeCorrdinates(tuple(location))
                location = location['name'] + ' / ' + location['admin2'] + ', ' + location['admin1'] + ' ' + location['cc']
            except:
                location = None
            try:
                if location != None:
                    search_dic = {
                        'Searched Keywords': content[1],
                        'Accessed Date': content[3],
                        'Location': location
                    }
                else:
                    search_dic = {
                        'Searched Keywords': content[1],
                        'Accessed Date': content[3]
                    }
                result_tags.append(search_dic)
            except:
                pass
        elif '/ads' in filename: # Google ads history
            try:
                if len(content) == 5:
                    search_dic = {
                        'Ads name': content[1],
                        'Accessed Date': content[3]
                    }
                    result_tags.append(search_dic)
            except:
                pass
        elif 'books' in filename: # Google books history
            try:
                search_dic = {
                    'Visited': content[1],
                    'Accessed Date': content[3]
                }
                result_tags.append(search_dic)
            except:
                pass
        elif 'store' in filename: # Google playstore history
            try:
                search_dic = {
                    'App Name': content[1],
                    'Accessed Date': content[3]
                }
                result_tags.append(search_dic)
            except:
                pass
        elif 'news' in filename: # Google news
            #try:
            if 'news' in filename:
                if 'Dismissed' in content[0]:
                    dismissedNews.append(content[1])
                    continue
                elif len(content) > 3 and ('news.google.com' in content[4] or 'www.youtube.com' in content[4]):
                    continue

                if len(content) > 3:
                    website = parseWeb(content[4])
                    search_dic = {
                        'News Title': content[1],
                        'Accessed Date': content[3],
                        'Source' : website,
                        'Important' : (content[1] not in dismissedNews)
                    }
                else:
                    search_dic = {
                        'Action': unidecode(content[0]),
                        'Accessed Date': content[2],
                    }
                result_tags.append(search_dic)
            #except:
            #    pass
        elif 'maps' in filename: # Google maps
            location = activity_location[index]
            try:
                location = location.a.get('href')
                location = parseLocation(location)
                location[0] = round(float(location[0]), 4)
                location[1] = round(float(location[1]), 4)
                location = analyzeCorrdinates(tuple(location))
                location = location['name'] + ' / ' + location['admin2'] + ', ' + location['admin1'] + ' ' + location['cc']
            except:
                location = None
            try:
                if(len(content) > 4):
                    search_dic = {
                        'Search': content[1],
                        'Location': location,
                        'Accessed Date': content[3]
                    }
                    result_tags.append(search_dic)
                elif len(content) == 4:
                    try:
                        location = parseLocationAt(content[-1])
                        location[0] = round(float(location[0]), 4)
                        location[1] = round(float(location[1]), 4)
                        location = analyzeCorrdinates(tuple(location))
                        location = location['name'] + ' / ' + location['admin2'] + ', ' + location['admin1'] + ' ' + location['cc']
                    except:
                        location = None
                    search_dic = {
                        'Search': location,
                        'Accessed Date': content[-2]
                    }
                    result_tags.append(search_dic)

            except:
                pass



        search_result[activity_title] = result_tags
    #print(filename)
    #print(search_result)
    return search_result

def parseLocation(location):
    try:
        return location[location.find('center=') + 7 : location.find('&zoom')].split(',')
    except:
        return None

def parseLocationAt(location):
    try:
        return location[location.find('@') + 7 : location.find(',', location.find(',') + 1)].split(',')
    except:
        return None

def parseWeb(website):
    try:
        if 'q=https://www' in website:
            return website[website.find('q=https:') + 14 : website.find('com', website.find('com') + 1) - 1]
        else:
            return website[website.find('q=https:') + 10 : website.find('com', website.find('com') + 1) - 1]
    except:
        return None

def readActivityHtml(content):
    soup = BeautifulSoup(content, 'lmxl')
    activity_search = soup.find_all('div', {'class': 'content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1'})
    activity_title = soup.find_all('p', {'class': 'mdl-typography--title'})[0].get_text()

    return activity_search, activity_title

def readActivityLocationHtml(content):
    soup = BeautifulSoup(content, 'lmxl')
    activity_search = soup.find_all('div', {'class': 'content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1'})
    activity_title = soup.find_all('p', {'class': 'mdl-typography--title'})[0].get_text()
    activity_location = soup.find_all('div', {'class': 'content-cell mdl-cell mdl-cell--12-col mdl-typography--caption'})

    return activity_search, activity_title, activity_location
