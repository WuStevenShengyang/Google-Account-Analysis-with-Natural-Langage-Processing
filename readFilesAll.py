import os
import codecs
from bs4 import BeautifulSoup
from icalendar import Calendar
import calendar
import json
import csv
import vobject
import datetime
from unidecode import unidecode
from htmlParser import *
from activityAnalysis import *
import webbrowser

def parseDate(dateStr):
    year = dateStr[0:4]
    month = dateStr[4:6]
    day = dateStr[6:8]

    hour = dateStr[9:11]
    minutes = dateStr[11:13]
    sec = dateStr[13:15]

    if hour != '' and minutes != '' and sec != '':
        return calendar.month_abbr[int(month)] + " " + str(int(day)) + ", " + year + " " + str(int(hour)) + ":" + minutes + ":" + sec + " GMT"
    else:
        return calendar.month_abbr[int(month)] + " " + str(int(day)) + ", " + year

def parseDateMillis(dateStr):
    date = str(datetime.datetime.fromtimestamp(dateStr / 1000000))

    return parseDateGoogleFormat(date)

def parseDateGoogleFormat(dateStr):
    year = dateStr[0:4]
    month = dateStr[5:7]
    day = dateStr[8:10]

    hour = dateStr[11:13]
    minutes = dateStr[14:16]
    sec = dateStr[17:19]

    return calendar.month_abbr[int(month)] + " " + str(int(day)) + ", " + year + " " + str(int(hour)) + ":" + minutes + ":" + sec + " GMT"



def getFilePaths(mainFilePath):
    dir = os.listdir(mainFilePath)

    filePaths = []

    for name in dir:
        filename, file_extension = os.path.splitext(name)
        if filename[0] == '.':
            continue
        elif file_extension != '':
            filePaths.append(mainFilePath + '/' + name)
        else:
            filePaths += getFilePaths(mainFilePath + '/' + name)

    return filePaths

def readHtml(path):
    text = codecs.open(path, 'r', encoding='utf8').read()
    return text

def readIcs(path):
    g = open(path,'rb')
    gcal = Calendar.from_ical(g.read())
    events = []
    for component in gcal.walk():
        if component.name == "VEVENT":
            dictionary = {}
            dictionary["Name"] = component.get('summary').to_ical().decode("utf-8")
            dictionary["Start"] = parseDate(component.get('dtstart').to_ical().decode("utf-8"))
            dictionary["End"] = parseDate(component.get('dtend').to_ical().decode("utf-8"))

            location = component.get('location').to_ical().decode('utf-8').replace('\\', '')
            if location != '':
                dictionary["Location"] = location

            description = component.get('description').to_ical().decode('utf-8')

            if description != '':
                dictionary["Description"] = description

            attendee = component.get('attendee')
            try:
                if attendee != None:
                    # if type(attendee) is list:
                    #     emails = []
                    #     for attend in attendee:
                    #         emails.append(attend.to_ical().decode('utf-8').replace('mailto:', ''))
                    #     dictionary["Email"] = emails
                    # else:
                    dictionary["Email"] = attendee.to_ical().decode('utf-8').replace('mailto:', '')
            except:
                pass
            events.append(dictionary)
    g.close()
    return events

def readJson(path):
    with open(path, encoding='utf8') as json_file:
        data = json.load(json_file)
        return data

def readCsv(path):
    tweet_list = []
    with open(path, 'r', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            tweet_list.append(list(row))
    return tweet_list

def readVcf(path):
    allContacts = []
    obj = vobject.readComponents(codecs.open(path, encoding='utf-8').read())
    contacts = [contact for contact in obj]
    for contact in contacts:
        dictionary = {}
        dictionary["Name"] = contact.getChildValue("fn")
        if dictionary["Name"] == None:
            dictionary["Name"] = "Unnamed Contact"

        relationship = contact.getChildValue('org')
        if relationship != None:
            dictionary["Relationship"] = relationship

        bday = contact.getChildValue('bday')
        if bday != None:
            dictionary["Birth Day"] = bday

        dictionary["Phone #"] = []
        try:
            for tel in contact.contents["tel"]:
                dictionary["Phone #"].append(tel.value)
        except:
            dictionary.pop('Phone #')

        dictionary["Emails"] = []
        try:
            for email in contact.contents["email"]:
                dictionary["Emails"].append(email.value)
        except:
            dictionary.pop('Emails')

        dictionary["Address"] = []
        try:
            for adr in contact.contents["adr"]:
                dictionary["Address"].append(str(adr.value).replace('\n', " "))
        except:
            dictionary.pop('Address')

        allContacts.append(dictionary)
    return allContacts

def readTxt(path):
    return open(path, 'r', encoding='utf8').read()

def main():
    #path1 = '/Users/labuser/Downloads/Takeout-2/'
    user_path = input('Enter the path to Google Takeout Folder:\n')
    paths = getFilePaths(user_path)
    f = getFileName()
    #Automatically open google takeout website
    #webbrowser.open('https://takeout.google.com/settings/takeout')

    writer = csv.writer(f)

    orderHistory = []
    transactions = []

    appInstalls = []
    appArr = []

    for path in paths:
        filename, file_extension = os.path.splitext(path)
        if file_extension == ".html":
            continue
        print('Path: ', path)
        if file_extension == ".ics": #Calendar
            content  = readIcs(path) #Array of Dictionaries (PARSED IN READ)
            analyzeCalendar(content)
        elif file_extension == ".json":
            content = readJson(path) #List of Dictionaries (if only one dictionary it is a dicitonary not a list)
            content = determineJSON(filename, content, writer)
            if content != None:
                if type(content) == tuple:
                    app = content[1]
                    if type(app) is dict:
                        appArr = app['Hi']
                    else:
                        appInstalls = app
                else:
                    orderHistory = content
        elif file_extension == ".csv":
            content = readCsv(path) #2D Array --- one array for each row with values of elements in row
            content = determineCSV(filename, content, writer)
            if content != None:
                transactions = content
        elif file_extension == ".vcf": #Contacts
            content = readVcf(path) #Array of Dictionaries (PARSED IN READ)
            analyzeContacts(content, filename[filename.rfind('/') + 1:])
        elif file_extension == ".txt":
            readTxt(path) #Plain Text (NO FILES CURRENT USE IT)

    for path in paths:
        filename, file_extension = os.path.splitext(path)
        if file_extension == ".html":
            print('My Path: ', path)
            content = readHtml(path) #Plain text
            ########
            determineHTML(filename, content, writer)

    analyzeOrderTransactionHistory(orderHistory, transactions)

    try:
        writeApp(appInstalls, appArr[0], appArr[1], appArr[2])
    except:
        pass

########
# Determine the type of html files
def determineHTML(filename, content, writer):
 # A list of dictionarys, which contains the key of activity title and value of a list of activities
    if 'device' in filename.lower():
        phoneInfo = extractPhoneInfoHtml(content)
        phoneInfo = removeBlanksFromDictionary(phoneInfo)
        analyzeDevice(phoneInfo)
        writeArrayToCSV("Device Info", phoneInfo, writer)
    elif 'bookmarks' in filename.lower():
        bookmarks = extractBookMarksHtml(content)
        bookmarks = removeBlanksFromArray(bookmarks)
        analyzeBookmarks(bookmarks)
        writeArrayToCSV("Bookmarks", bookmarks, writer)
    elif 'myactivity' in filename.lower():
        activity_dic = extractActivityHtml(content, filename.lower())
        print("READ")
        analyze(activity_dic)
        print("READ2")
        #write_activity_to_csv(activity_dic)
        if type(activity_dic) is list:
            activity_dic = removeBlanksFromArray(activity_dic)
            print("READ3")
            writeArrayToCSV("My Activity", activity_dic, writer)
            print("READ4")
        else:
            activity_dic = removeBlanksFromDictionary(activity_dic)
            writeDictToCSV("My Activity", activity_dic, writer)
    elif 'youtube' and 'search' in filename.lower():
        youtube_search_history_dic = extractYoutubeSearchHtml(content)
        youtube_search_history_dic = removeBlanksFromDictionary(youtube_search_history_dic)
        writeDictToCSV("Youtube Search History", youtube_search_history_dic, writer)
    elif 'youtube' and 'comment' in filename.lower():
        youtube_comment_dic = extractYoutubeCommentHtml(content)
        youtube_comment_dic = removeBlanksFromArray(youtube_comment_dic)
        writeArrayToCSV("Youtube Comments", youtube_comment_dic, writer)

def determineJSON(filename, content, writer):
    if 'autofill' in filename.lower():
        autoFillInfo = extractAutofillJson(content)
        autoFillInfo = removeBlanksFromDictionary(autoFillInfo)
        writeDictToCSV("Autofill Info", autoFillInfo, writer)
    elif 'browserhistory' in filename.lower(): #ONLY ONE {Time : Title} USUALLY OPPOSITE
        browserInfo = extractBowserHistoryJson(content)
        browserInfo = removeBlanksFromArray(browserInfo)

        analyze({'Browser History': browserInfo})

        writeArrayToCSV("Browser History", browserInfo, writer)
    elif 'subscriptions' in filename.lower():
        subscriptionInfo = extractYoutubeSubscriptionJson(content)
        subscriptionInfo = removeBlanksFromArray(subscriptionInfo)
        writeArrayToCSV("Youtube Subscriptions", subscriptionInfo, writer)
    elif 'likes' in filename.lower():
        likeInfo = extractYoutubeLikesJson(content)
        likeInfo = removeBlanksFromArray(likeInfo)
        analyzeLikes(likeInfo)
        writeArrayToCSV("Youtube Likes", likeInfo, writer)
    elif 'playlists' in filename.lower() and 'uploads' not in filename.lower() and 'likes' not in filename.lower():
        watchLaterInfo = [filename[filename.rfind('playlists/') + 10:]] + extractYoutubeWatchLaterJson(content)
        watchLaterInfo = removeBlanksFromArray(watchLaterInfo)
        analyzeWatchLater(watchLaterInfo)
        writeArrayToCSV("Youtube Watch Later Playlist", watchLaterInfo, writer)
    elif 'installs' in filename.lower():
        appInstallsInfo = extractAppInstallsJson(content)
        appInstallsInfo = removeBlanksFromArray(appInstallsInfo)
        appInstall = analyze({'installs': appInstallsInfo})
        writeArrayToCSV("Apps Installed", appInstallsInfo, writer)
        return (0, appInstall)
    elif 'library' in filename.lower():
        appLibraryInfo = extractAppLibraryJson(content)
        appLibraryInfo = removeBlanksFromArray(appLibraryInfo)
        app = analyze({'library': appLibraryInfo})
        writeArrayToCSV("Purchased Apps", appLibraryInfo, writer)
        return (0, app)
    elif 'order history' in filename.lower():
        ordersInfo = extractOrderHistoryJson(content)
        ordersInfo = removeBlanksFromArray(ordersInfo)
        writeArrayToCSV("Orders", ordersInfo, writer)
        return ordersInfo

def determineCSV(filename, content, writer):
    if 'transactions' in filename.lower():
        transactionInfo = extractTransactionCSV(content)
        transactionInfo = removeBlanksFromArray(transactionInfo)
        writeArrayToCSV("Transactions", transactionInfo, writer)
        return transactionInfo

def writeArrayRowCSV(name, content, writer, key = ''):
    first = True
    if name != None:
        writer.writerow([name])
    for el in content:
        if type(el) is list:
            writeArrayToCSV(name, el, writer, key = '')
        elif type(el) is dict:
            if first:
                writer.writerow([key])
            writeDictToCSV(name, el, writer)
        else:
            if first:
                writer.writerow([key, el])
                first = False
            else:
                writer.writerow(['', el])
    if name != None:
        writer.writerow([])

def writeArrayToCSV(name, content, writer, key = ''):
    if name != None:
        writer.writerow([name])
    for el in content:
        if type(el) is dict:
            writeDictToCSV(None, el, writer)
        elif type(el) is list and len(el) > 0:
            if type(el[0]) is list:
                writeArrayToCSV(name, el, writer, key)
            else:
                writeArrayRowCSV(name, el, writer, key)
        elif type(el) is dict:
            writer.writerow([key])
            writeDictToCSV(name, el, writer)
        else:
            writeArrayRowCSV(None, content, writer, key)
            break
    if name != None:
        writer.writerow([])

def writeDictToCSV(name, content, writer):
    if name != None:
        writer.writerow([name])
    for key in content.keys():
        value = content[key]
        if type(value) is list:
            writeArrayToCSV(name, value, writer, key)
        elif type(value) is dict:
            writer.writerow([key])
            writeDictToCSV(name, value, writer)
        else:
            writer.writerow([key, value])
    if name != None:
        writer.writerow([])

########
def extractAutofillJson(content):
    arr = {}
    if type(content) is dict:
        dictionary = content.get('Autofill')
        if type(dictionary) is list and len(dictionary) > 0:
            dictionary = dictionary[0]
        else:
            return arr

        arr["Country"] = dictionary.get('address_home_country')
        arr["State"] = dictionary.get('address_home_state')
        arr["City"] = dictionary.get('address_home_city')
        arr["Name"] = dictionary.get('name_full')
        arr["Email"] = dictionary.get('email_address')
        arr["Zip Code"] = dictionary.get('address_home_zip')
        arr["Street Address"] = dictionary.get('address_home_street_address')
        arr["Phone Number"] = dictionary.get('phone_home_whole_number')

        if type(arr["Name"]) is list and len(arr["Name"]) > 0:
            arr["Name"] = arr["Name"][0]

        if type(arr["Email"]) is list and len(arr["Email"]) > 0:
            arr["Email"] = arr["Email"][0]

        if type(arr["Phone Number"]) is list and len(arr["Phone Number"]) > 0:
            arr["Phone Number"] = arr["Phone Number"][0]

    return arr

def extractBowserHistoryJson(content):
    arr = []
    if type(content) is dict:
        dictionary = content.get('Browser History')
        for site in dictionary:
            if 'time_usec' in site:
                arr.append({'Site Name' : site.get('url'), 'View Date' : parseDateMillis(site.get('time_usec'))})
    return arr

def extractYoutubeSubscriptionJson(content):
    arr = []
    if type(content) is list:
        for dictionary in content:
            if 'snippet' in dictionary:
                newDict = dictionary.get('snippet')
                if 'title' in newDict:
                    if 'contentDetails' in dictionary:
                        arr.append({'Video Name' : newDict.get('title'), 'Publish Date' : parseDateGoogleFormat(newDict.get('publishedAt')), 'Video Description' : newDict.get('description'), 'Unwatched New Videos' : dictionary.get('contentDetails').get('newItemCount')})
                    else:
                        arr.append({'Video Name' : newDict.get('title'), 'Subscribed Date' : parseDateGoogleFormat(newDict.get('publishedAt')), 'Video Description' : newDict.get('description')})
    return arr

def extractYoutubeWatchLaterJson(content):
    arr = []
    if type(content) is list:
        for dictionary in content:
            if 'snippet' in dictionary:
                newDict = dictionary.get('snippet')
                if 'title' in newDict:
                    arr.append({'Video Name' : newDict.get('title'), 'Added Date' : parseDateGoogleFormat(newDict.get('publishedAt')), 'Video Description' : newDict.get('description')})
    return arr

def extractYoutubeLikesJson(content):
    arr = []
    if type(content) is list:
        for dictionary in content:
            if 'snippet' in dictionary:
                newDict = dictionary.get('snippet')
                if 'title' in newDict:
                    arr.append({'Video Name' : newDict.get('title'), 'Liked Date' : parseDateGoogleFormat(newDict.get('publishedAt')), 'Video Description' : newDict.get('description')})
    return arr

def extractAppInstallsJson(content):
    arr = []
    if type(content) is list:
        for dictionary in content:
            if 'install' in dictionary:
                newDict = dictionary.get('install')
                if 'doc' in newDict and 'title' in newDict.get('doc'):
                    docDict = newDict.get('doc')
                    title = docDict.get('title')
                    if title != None and type(title) == str:
                        if title[:3] == 'com':
                            continue
                        if 'deviceAttribute' in newDict:
                            arr.append({'App Name' : title, 'Last Install Date' : parseDateGoogleFormat(newDict.get('firstInstallationTime')), 'Device Installed On' : newDict.get('deviceAttribute').get('deviceDisplayName'), 'Last Update Time' : parseDateGoogleFormat(newDict.get('lastUpdateTime'))})
                        else:
                            arr.append({'App Name' : title, 'Last Install Date' : parseDateGoogleFormat(newDict.get('firstInstallationTime')), 'Last Update Time' : parseDateGoogleFormat(newDict.get('lastUpdateTime'))})
    return arr

def extractAppLibraryJson(content):
    arr = []
    if type(content) is list:
        for dictionary in content:
            if 'libraryDoc' in dictionary:
                newDict = dictionary.get('libraryDoc')
                if 'doc' in newDict and 'title' in newDict.get('doc'):
                    docDict = newDict.get('doc')
                    title = docDict.get('title')
                    if title != None and type(title) == str:
                        if title[:3] == 'com':
                            continue
                        arr.append({'App Name' : title, 'Install Date' : parseDateGoogleFormat(newDict.get('acquisitionTime'))})
    return arr

def extractOrderHistoryJson(content):
    arr = []
    if type(content) is list:
        for dictionary in content:
            if 'orderHistory' in dictionary:
                newDict = dictionary.get('orderHistory')
                if 'orderId' in newDict and 'lineItem' in newDict:
                    lineDict = newDict.get('lineItem')
                    if type(lineDict) is list and len(lineDict) > 0 and 'doc' in lineDict[0]:
                        docDict = lineDict[0].get('doc')
                        orderId = newDict.get('orderId')
                        title = docDict.get('title')
                        docType =  docDict.get('documentType')
                        price = newDict.get('totalPrice')
                        ip = newDict.get('ipAddress')
                        time = parseDateGoogleFormat(newDict.get('creationTime'))
                        billingInfo = {}
                        billContact = {}
                        if 'billingInstrument' in newDict:
                            billingInfo = newDict.get('billingInstrument')
                        if 'billingContact' in newDict:
                            billContact = newDict.get('billingContact')
                        arr.append({'Order Name' : title, 'Order Date' : time, 'Order Type' : docType, 'Price' : price, 'Billing Info' : billingInfo, 'Contact Info' : billContact, 'IP Address' : ip, "Order ID" : orderId})
    return arr

def extractTransactionCSV(content):
    arr = []
    if type(content) is list and len(content) > 1:
        for i in range(1, len(content)):
            row = content[i]
            dictionary = []
            time = unidecode(row[0])
            transactionId = unidecode(row[1])
            description = unidecode(row[2])
            product  = unidecode(row[3])
            credit = unidecode(row[4])
            price = unidecode(row[6])
            dictionary = {'Transaction Description' : description, 'Product' : product, 'Time' : time, 'Credit' : credit, 'Price' : price, 'Transaction ID' : transactionId}
            arr.append(dictionary)
    return arr

def removeBlanksFromDictionary(dictionary):
    forDictionary = dictionary.copy()
    for key in forDictionary.keys():
        value = forDictionary[key]
        if (type(value) is str and value.replace(" ", "") == '') or (type(value) is list and value == []) or (type(value) is dict and value == {}):
            dictionary.pop(key)
        elif type(value) is list:
            removeBlanksFromArray(value)
        elif type(value) is dict:
            removeBlanksFromDictionary(value)
    return dictionary

def removeBlanksFromArray(arr):
    forArray = arr.copy()
    for el in range(len(forArray) - 1, -1, -1):
        value = forArray[el]
        if (type(value) is str and value.replace(" ", "") == '') or (type(value) is list and value == []) or (type(value) is dict and value == {}):
            arr.pop(el)
        elif type(value) is list:
            removeBlanksFromArray(value)
        elif type(value) is dict:
            removeBlanksFromDictionary(value)
    return arr

main()
