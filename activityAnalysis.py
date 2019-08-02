import nltk
from nltk.corpus import stopwords
from ast import literal_eval
import numpy as np
import re
import csv
import sys
import os
import operator
import reverse_geocoder as rg 
from urllib import request
from urllib import parse
from bs4 import BeautifulSoup

allLocations = {}

'''
    Natural Language Processing Methods
'''
def determineInterest(content):
    wordCounter = sortDicByKey(ngramsCount(content, 1))
    bigramCounter = sortDicByKey(ngramsCount(content, 2))
    trigramCounter = sortDicByKey(ngramsCount(content, 3))
    quadragramCounter = sortDicByKey(ngramsCount(content, 4))
    pentagramCounter = sortDicByKey(ngramsCount(content, 5))

    commonWord = [word[0] for word in wordCounter[:10]]
    commonBigram = [word[0] for word in bigramCounter[:10]]
    commonTrigram = [word[0] for word in trigramCounter[:10]]
    commonQuadraigram = [word[0] for word in quadragramCounter[:10]]
    commonPentagram = [word[0] for word in pentagramCounter[:10]]
    interested = []

    for word in commonWord:
        if word in str(commonBigram):
            for bigram in commonBigram:
                if bigram in str(commonTrigram):
                    for trigram in commonTrigram:
                        if trigram in str(commonQuadraigram):
                            for quadragram in commonQuadraigram:
                                if quadragram in str(commonPentagram):
                                    for pentagram in commonPentagram:
                                        interested.append(pentagram)
                                else:
                                    interested.append(quadragram)
                        else:
                            interested.append(trigram)
                else:
                    interested.append(bigram)
        else:
            interested.append(word)

    return list(set(interested))

def cleanSentence(content):
    content = re.sub(r'https\S+', '', content.lower().replace('amp', ''))
    str = ''

    for word in content:
        if word == '\'':
            pass
        elif word in '!=@#$%^&*()_+;:?-,.—"<>/{}[]|~`\\':
            str += ' '
        else:
            str += word

    stopWords = set(stopwords.words('english'))
    filtered = [w for w in str.split() if not w in stopWords]

    return filtered

def ngramsCount(data, num):
    ngrams = {}
    ngramsList = list(nltk.ngrams(data, num))

    for ngram in ngramsList:
        currentWord = ''

        for word in ngram:
            currentWord += word + ' '

        currentWord = currentWord[:len(currentWord) - 1]

        if currentWord in ngrams:
            ngrams[currentWord] += 1
        else:
            ngrams[currentWord] = 1

    return ngrams

def getNouns(data):
    sent = []
    sents = nltk.pos_tag(data)
    for tag in sents:
        if tag[1] in ['NN', 'NNS']:
            sent.append(tag[0])
    return ngramsCount(sent, 1)

def getVerbs(data):
    sent = []
    sents = nltk.pos_tag(data)
    for tag in sents:
        if tag[1] in ['VB', 'VBD']:
            sent.append(tag[0])
    return ngramsCount(sent, 1)


filename = 'Analyzed Info/' + input("\n\n\nEnter the filename to create: \n") + '.csv'
print(".\n.\n.")
try:
    os.remove(filename)
except:
    pass

def getFileName():
    return open(filename[:-4] + "_Extracted_Data.csv", 'w+', encoding = 'utf8')


'''
    Analyzing Methods
'''
def analyze(dic):
    for title in dic:
        if title.lower() == 'youtube': # Youtube watch history
            analyzeYoutubeWatch(dic[title])
        elif title.lower() == 'search': # Google search history
            analyzeGoogleSearch(dic[title])
        elif title.lower() == 'youtube.com':
            analyzeYoutubeSearch(dic[title]) # Youtube search history
        elif title.lower() == 'gmail':
            analyzeGmail(dic[title])
        elif title.lower() == 'google analytics': # Google analytics
            analyzeGoogleAnalytics(dic[title])
        elif title.lower() == 'google news': # Google news
            analyzeNews(dic[title])
        elif title.lower() == 'ads': # Ads
            analyzeAds(dic[title])
        elif title.lower() == 'maps':
            analyzeMap(dic[title])
        elif title.lower() == 'browser history': # Browser history json
            analyzeBrowswerHistory(dic[title])
        elif title.lower() == 'installs':
            return analyzeInstalls(dic[title])
        elif title.lower() == 'library':
            return analyzeLibrary(dic[title])

# Analyze currently installed apps
def analyzeInstalls(content):
    app = []
    device = []
    date = []
    for item in content:
        app.append(item['App Name'])
        device.append(item.get('Device Installed On'))
        date.append(item.get('Last Install Date'))
    arr = {"Hi" : [app, device, date]}
    return (arr)
    

# Analyze all app library
def analyzeLibrary(content):
    appInstalled = []
    for item in content:
        appInstalled.append(item['App Name'])
    return appInstalled


def writeApp(appInstalled, app, device, date):
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['App Library:'])
        writer.writerow(['App Name:', 'Installed Date:', 'Installed Device:', 'Is currently on the phone?'])
        for i in range(len(device)):
            status = appInstalled[i] in app
            writer.writerow([app[i], date[i], device[i], status])
        
        for i in range(3):
            writer.writerow([])

# Analyze browser history
def analyzeBrowswerHistory(content):
    lastDate = content[-1]['View Date']
    browserHistory = []

    for his in content:
        try:
            browserHistory.append(his['Site Name'])
        except:
            pass

    commonBrowse = commonURL(browserHistory)
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['Most often accessed websites since ' + lastDate + ':'])
        writer.writerow(['Website:', 'Accessed Times:'])
        for interest in commonBrowse[:31]:
            if interest[0] !='newtab':
                writer.writerow([interest[0], interest[1]])
        
        for i in range(3):
            writer.writerow([])

# Given a list of URL, return the access times of each url in a dictionary
def commonURL(URLlist):
    commonWeb = {}

    for web in URLlist:
        try:
            current = web.split('/')[2]
            if current in commonWeb:
                commonWeb[current] += 1
            else:
                commonWeb[current] = 1
        except:
            pass

    return sortDicByKey(commonWeb)

#Gets coordinates and returns address
def analyzeCorrdinates(arr):
    strLocation = str(arr[0])+str(arr[1])
    location = allLocations.get(strLocation)

    if location == None:
        location = rg.search(arr)
        if type(location) is list and len(location) > 0:
            allLocations[strLocation] = location[0]
            return location[0]
        return None
    else :
        return location

# Analyze google ads
def analyzeAds(content):
    adsHistory = ''
    for info in content:
        try:
            adsHistory += ' ' + info['Ads name']
        except:
            pass

    adsHistory = cleanSentence(adsHistory)
    ads = sortDicByKey(getNouns(adsHistory))[3:14]
    
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user is likely to click on the ads with the following keywords:'])
        for item in ads:
            if item[0].lower() != 'ads':
                writer.writerow([item[0][0].upper() + item[0][1:]])
        
        for i in range(3):
            writer.writerow([])

# Analyze Google analytics
def analyzeGoogleAnalytics(content):
    pass

# Analyze gmail History
def analyzeGmail(content):
    gmailHistory = ''
    for info in content:
        try:
            gmailHistory += ' ' + info['Content searched on Gmail']
        except:
            pass

    # Tokenize gmail search history
    gmailHistory = cleanSentence(gmailHistory)

# Analyze Youtube search history
def analyzeYoutubeSearch(content):
    youtubeSearchHistory = ''
    for info in content:
        try:
            youtubeSearchHistory += ' ' + info['Searched Video']
        except:
            pass

    # Tokenize youtube search history
    youtubeSearchHistory = cleanSentence(youtubeSearchHistory)
    commonNouns = sortDicByKey(getNouns(youtubeSearchHistory))
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s most commonly searched phrases on YouTube:'])
        for item in commonNouns[:11]:
            if item[0].lower() != 'youtube':
                writer.writerow([item[0][0].upper() + item[0][1:]])
        
        for i in range(3):
            writer.writerow([])

# Analyze Search History
def analyzeGoogleSearch(content):
    recentLocations = {}
    locations = {}
    searchHistory = ''
    searchLocation = []
    for info in content:
        try:
            searchHistory += ' ' + info['Searched Keywords']
            searchLocation.append(info.get('Location'))
            if len(locations) < 10 and info.get('Location') not in locations:
                recentLocations[info['Location']] = info['Accessed Date']
            if info.get('Location') not in locations:
                locations[info['Location']] = 1
            else:
                locations[info['Location']] += 1
        except:
            pass

    # Tokenize search history
    searchHistory = cleanSentence(searchHistory)
    commonSearch = determineInterest(searchHistory)

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s most commonly searched phrases:'])
        writer.writerow(['Phrase Searched:', "Location Searched At"])
        for index in range(len(commonSearch)):
            item = commonSearch[index]
            location = searchLocation[index]
            if location is None:
                location = ''
            writer.writerow([item[0].upper() + item[1:], location])
        
        for i in range(1):
            writer.writerow([])

        writer.writerow(['The user\'s most common locations when searching:'])
        writer.writerow(['Location:', "Number of times searched there"])
        for item in locations.keys():
            value = locations[item]
            writer.writerow([item, value])
        
        for i in range(1):
            writer.writerow([])

        writer.writerow(['The user\'s most recent locations when searching:'])
        writer.writerow(['Location:', "Date Searched"])
        for item in recentLocations.keys():
            value = recentLocations[item]
            writer.writerow([item, value])
        
        for i in range(3):
            writer.writerow([])

# Analyze YouTube watch history
def analyzeYoutubeWatch(content):
    watchHistory = ''
    channel = {}
    for info in content:
        try:
            watchHistory += ' ' + info['Name']
            if info['Channel'] in channel:
                channel[info['Channel']] += 1
            else:
                channel[info['Channel']] = 1
        except:
            pass

    # Sort channel
    channel = sortDicByKey(channel)

    # Tokenize watch history
    watchHistory = cleanSentence(watchHistory)

    interest = determineInterest(watchHistory)
    # topics = predict(interest)

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s favorite channel'])
        writer.writerow(['Channel:', 'Accessed Times:'])
        for item in channel[:10]:
            writer.writerow([item[0], item[1]])
        
        for i in range(3):
            writer.writerow([])

        writer.writerow(['The user is likely interested in:'])

        for interest in interest:
            writer.writerow([interest[0].upper() + interest[1:]])
        
        for i in range(5):
            writer.writerow([])
        
        # writer.writerow(['The user is likely interested in the following topic(s):'])
        # for top in topics:
        #     writer.writerow([top])
        
#Analyze Ueer Calendar
def analyzeCalendar(content):
    places = {}
    names = {}
    emails = {}

    for event in content:
        location = event.get('Location')

        if location != None:
            if location in places:
                places[location] += 1
            else:
                places[location] = 1

        title = event.get('Name')

        if title != None:
            if title in names:
                names[title] += 1
            else:
                names[title] = 1

        attendees = event.get('Email')

        if attendees != None:
            if attendees in emails:
                emails[attendees] += 1
            else:
                emails[attendees] = 1

    places = sortDicByKey(places)
    names = sortDicByKey(names)
    emails = sortDicByKey(emails)

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s most commonly places in Calendar:'])
        writer.writerow(['Place', "Number of Times"])

        count = 0

        for item in places:
            if count > 10:
                break
            writer.writerow([item[0], item[1]])
        
        for i in range(1):
            writer.writerow([])

        writer.writerow(['The user\'s most commonly names in Calendar:'])
        writer.writerow(['Name', "Number of Times"])

        count = 0

        for item in names:
            if count > 10:
                break
            writer.writerow([item[0], item[1]])
        
        for i in range(1):
            writer.writerow([])

        writer.writerow(['The user\'s most commonly emails in Calendar:'])
        writer.writerow(['Email', "Number of Times"])

        count = 0

        for item in emails:
            if count > 10:
                break
            writer.writerow([item[0], item[1]])
        
        for i in range(3):
            writer.writerow([])



#Analyze Maps
def analyzeMap(content):
    places = {}
    locations = {}

    for event in content:
        location = event.get('Search')

        trueLocation = event.get('Location')

        if location != None:
            if location in places:
                places[location] += 1
            else:
                places[location] = 1

        if trueLocation != None:
            if location in locations:
                locations[trueLocation] += 1
            else:
                locations[trueLocation] = 1

    places = sortDicByKey(places)
    locations = sortDicByKey(locations)

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s most commonly searched places:'])
        writer.writerow(['Placed Searched', "Number of Times"])

        count = 0

        for item in places:
            if count > 10:
                break
            writer.writerow([item[0], item[1]])
        
        for i in range(1):
            writer.writerow([])

        writer.writerow(['The user\'s most common location while searching for places:'])
        writer.writerow(['Location', "Number of Times"])

        count = 0

        for item in locations:
            if count > 10:
                break
            writer.writerow([item[0], item[1]])
        
        for i in range(3):
            writer.writerow([])

#Analyzes User Contacts
def analyzeContacts(content, name):
    length = len(content)

    familyMembers = ['father', 'mother', 'parent', 'son', 'daughter', 'child', 'husband', 'wife', 'spouse', 'brother', 'sister', 'sibling', 'uncle', 
                                'aunt', 'nephew', 'niece', 'cousin', 'partner', 'girlfriend', 'boyfriend']

    emailContacts = 0
    phoneContacts = 0
    bdayContacts = 0
    adrContacts = 0

    specialContacts = []
    relationshipContacts = []

    for contact in content:
        if contact.get("Emails") != None:
            emailContacts += 1

        if contact.get("Phone #") != None:
            phoneContacts += 1

        relationship = contact.get("Relationship")
        if relationship != None:
            relationshipContacts.append(contact)
            for member in familyMembers:
                for relation in relationship:
                    if member in relation.lower():
                        specialContacts.append(content)
                        break

        if contact.get("Birth Day") != None:
            bdayContacts += 1

        if contact.get("Address") != None:
            adrContacts += 1

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s contacts in ' + name + ' with organization names:'])
        writer.writerow(['Contact Name', "Organization"])

        for item in relationshipContacts:
            writer.writerow([item.get("Name"), item.get("Relationship")])
        
        for i in range(1):
            writer.writerow([])

        writer.writerow(['The user\'s contacts ' + filename + ' with familial relations:'])
        writer.writerow(['Contact Name', "Familial Relation"])

        for item in specialContacts:
            writer.writerow([item.get("Name"), item.get("Relationship")])
        
        for i in range(3):
            writer.writerow([])

#Analyzes Users News
def analyzeNews(content):
    importantNews = {}
    generalNews = {}
    actions = {}

    count = 0

    history = ''
    importantHistory = ''

    for story in content:
        action = story.get('Action')

        if action != None:
            if action in actions:
                actions[action] += 1
            else:
                actions[action] = 1
        else:
            history += ' ' + story.get('News Title')
            source = story.get('Source')
            important = story.get('Important')
            if important:
                importantHistory += ' ' + story.get('News Title')
                count += 1
                if source in importantNews:
                    importantNews[source] += 1
                else:
                    importantNews[source] = 1

            if source in generalNews:
                generalNews[source] += 1
            else:
                generalNews[source] = 1

    importantNews = sortDicByKey(importantNews)
    generalNews = sortDicByKey(generalNews)
    actions = sortDicByKey(actions)

    if count > 10:
        importantHistory = cleanSentence(importantHistory)
        interest = determineInterest(importantHistory)

        #newsTopic = predict(interest)

        with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
            writer = csv.writer(fp)
            # writer.writerow(['The user\'s most likely interested in the news with following topic(s):'])
            # for item in newsTopic:
            #     writer.writerow([item])
            
            # for i in range(1):
            #     writer.writerow([])

            writer.writerow(['The user\'s most likely reads most from these sources:'])
            writer.writerow(['Source:', 'Read Times:'])
            for item, value in importantNews:
                writer.writerow([item, value])

            for i in range(3):
                writer.writerow([])
    else:
        history = cleanSentence(history)
        interest = determineInterest(history)

        #newsTopic = predict(interest)

        with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
            writer = csv.writer(fp)
            # writer.writerow(['The user\'s most likely interested in the news with following topic(s):'])
            # for item in newsTopic:
            #     writer.writerow([item])
            
            # for i in range(1):
            #     writer.writerow([])

            writer.writerow(['The user\'s most likely reads most from these sources:'])
            writer.writerow(['Source:', 'Read Times:'])
            for item, value in generalNews:
                writer.writerow([item, value])

            for i in range(3):
                writer.writerow([])


#Analyzes Users Watch Later Playlist
def analyzeWatchLater(content):

    name = content[0]
    videos = {name : []}

    content.pop(0)

    for video in content[-10:]:
        videos[name].append({'Video Name' : video.get('Video Name'), 'Added Date' : video.get('Added Date')})

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s 10 most recent addiitons to ' + name + ' playlist:'])
        writer.writerow(['Video Name', "Addition Date"])

        for item in videos[name]:
            writer.writerow([item.get("Video Name"), item.get("Added Date")])
        
        for i in range(3):
            writer.writerow([])

#Analyzes Users Likes Playlist
def analyzeLikes(content):
    likes = []
    for like in content[-10:]:
        likes.append({'Video Name' : like.get('Video Name'), 'Liked Date' : like.get('Liked Date')})

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s 10 most recent videos they liked'])
        writer.writerow(['Video Name', "Liked Date"])

        for item in likes:
            writer.writerow([item.get("Video Name"), item.get("Liked Date")])
        
        for i in range(3):
            writer.writerow([])

#Analyzes Users comments on videos
def analyzeComments(content):
    content = {"Comments" : content[-10:]}

#Analyzes Users Device (IF android only)
def analyzeDevice(content):
    if len(content) < 1:
        return None
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s Device Configurations'])
        writer.writerow(['Configuration:', 'Value:'])
        for data in content.keys():
            value = content[data]
            writer.writerow([data, value])

        for i in range(3):
            writer.writerow([])

#Analyzes Users bookmarks
def analyzeBookmarks(content):
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s Bookmarks'])
        for values in content[:25]:
            writer.writerow([values])

        for i in range(3):
            writer.writerow([])

#Analyzes Users autofill from chrome
def analyzeAutofill(content):
    if len(content) < 1:
        return None
    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['The user\'s Autofill from Chrome'])
        writer.writerow(['Autofill Elements', 'Value'])
        for data in content:
            value = content[data]
            writer.writerow([data, value])

        for i in range(3):
            writer.writerow([])


#Analyze payments
def analyzeOrderTransactionHistory(orderContent, transactionContent):
    newList = []
    groupProduct = {}

    orderCopies = orderContent.copy()

    for transaction in transactionContent:
        found = False
        for index in range(len(orderCopies)-1, -1, -1):
            order = orderCopies[index]
            if transaction['Transaction ID'] == order['Order ID']:
                found = True
                newList.append(order)

                orderCopies.pop(index)

                product = order['Order Type']

                if product in groupProduct:
                    groupProduct[product].append(order)
                else:
                    groupProduct[product] = [order]
                break
        if not found:
            newList.append(transaction)

            product = transaction['Product']

            if product in groupProduct:
                groupProduct[product].append(transaction)
            else:
                groupProduct[product] = [transaction]

    newList += orderCopies

    for order in orderCopies:

        product = order['Order Type']

        if product in groupProduct:
            groupProduct[product].append(order)
        else:
            groupProduct[product] = [order]

    names = {}

    for order in newList:
        transactionTitle = order.get("Transaction Description")
        orderTitle = order.get('Order Name')

        if orderTitle != None:
            if orderTitle in names:
                names[orderTitle] += 1
            else:
                names[orderTitle] = 1
        elif transactionTitle != None:
            if transactionTitle in names:
                names[transactionTitle] += 1
            else:
                names[transactionTitle] = 1

    names = sortDicByKey(names)

    with open(filename, 'a', newline = '', encoding = 'utf-8') as fp:
            writer = csv.writer(fp)
            writer.writerow(['The user\'s most common transactions:'])
            writer.writerow(['Transaction Name', 'Number of times'])

            count = 0

            for item in names:
                if count > 10:
                    break
                writer.writerow([item[0], item[1]])
                
            
            for i in range(1):
                writer.writerow([])

            writer.writerow(['The user\'s transactions:'])
            writer.writerow(['Transaction Name', 'Price', 'Transaction Date', 'Billing Name', 'Billing Address', 'Card Used', 'Product Type', 'IP Address'])
            for item in newList:
                title = item.get('Order Name')
                price = item.get('Price')
                if title != None:
                    billing = item.get('Billing Info')
                    billing = billing.get('cardClass') + " " + billing.get('displayName') + " EXP: " + billing.get('expiration')

                    contact = item.get('Contact Info')
                    name = contact.get('Name')

                    contact = contact.get('city') + ", " + contact.get('state') + " " + contact.get('countryCode') + contact.get('postalCode')

                    writer.writerow([title, price, item.get('Order Date'), name, contact, billing, item.get('Order Type'), item.get('IP Address')])
                else:
                    writer.writerow([item.get('Transaction Description'), price, item.get('Time'), '', '', item.get('Credit'), item.get('Product'), ''])
            for i in range(3):
                writer.writerow([])


def sortDicByKey(wordCount):
    return sorted(wordCount.items(), key = operator.itemgetter(1), reverse = True)
