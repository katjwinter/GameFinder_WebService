#-------------------------------------------------------------------------------
# Name:        Scraper
# Purpose:     Provide RESTful services for getting the locations of various
#               game stores which have a game in stock.
#               Also provides functionality to check how many game titles
#               match the one given, so that possibilities can be narrowed
#               down prior to the location request
#
# Author:      Kat Winter
#
# Created:     24/05/2013
# Copyright:   (c) Kat Winter 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from bottle import route, run, request, response
import bs4
from lxml import etree
import urllib
import urllib2
import re

@route('/locate')
def locate():
    # Get query parameters
    title = request.query.title
    system = request.query.system
    zip = request.query.zip
    store = request.query.store

    root = etree.Element('locations')
    if not store:
        root = locateGS(title, system, zip, root)
        root = locateBBY(title, system, zip, root)
    elif store == "gs":
        root = locateGS(title, system, zip, root)
    elif store == "bby":
        root = locateBBY(title, system, zip, root)
    else:
        root = locateGS(title, system, zip, root)
        root = locateBBY(title, system, zip, root)

    strResult = etree.tostring(root, pretty_print=True)
    response.content_type = 'text/xml' # We are returning XML
    return strResult

def locateBBY(title, system, zip, root):
    # Best Buy requires an API key to use their web service
    bbyApiKey = "crs2yyrur5c9trmtv4uggtd2"
    # Request the Best Buy data
    rawurl = "http://api.remix.bestbuy.com/v1/products(search=%s&categoryPath.name=video games&platform=%s&preowned in(true))+stores(area(%s,10))?apiKey=%s" % (title, system, zip, bbyApiKey)
    url = urllib.quote(rawurl, safe='/,?:=&()')
    response = urllib2.urlopen(url)
    html = response.read()
    # Begin parsing the results
    soup = bs4.BeautifulSoup("".join(html))
    results = list()
    for game in soup.findAll("product"):
        rawName = game.find("name").text
        try:
            titleOpt = re.search(u'(.*)(?= \u2014)', rawName).group()
        except AttributeError:
            titleOpt = ""
        if titleOpt != "":
            titleOpt = re.sub("( 1)", " I", titleOpt)
            titleOpt = re.sub("( 2)", " II", titleOpt)
            titleOpt = re.sub("( 3)", " III", titleOpt)
            titleOpt = re.sub(r'[^\w\s]', "", titleOpt)
            titleOpt = str(titleOpt)
            titleOpt = titleOpt.strip()
            titleOpt = titleOpt.lower()
            price = "Unknown"
            if titleOpt == title:
                # grab onSale. if text is true, grab salePrice else grab regularPrice
                if game.find("onsale").text == "true":
                    price = game.find("saleprice").text
                else:
                    price = game.find("regularprice").text
                # grab every store in stores
                for store in game.findAll("store"):
                    # grab longName, address, city, region, postalCode, lat, lng, phone
                    # and add everything to the tree
                    locElem = etree.Element('location')
                    storeElem = etree.Element('store')
                    storeElem.text = 'BestBuy'
                    locElem.append(storeElem)
                    nameElem = etree.Element('name')
                    nameElem.text = store.find("longname").text
                    locElem.append(nameElem)
                    add1Elem = etree.Element('address1')
                    add1Elem.text = store.find("address").text
                    locElem.append(add1Elem)
                    cityElem = etree.Element('city')
                    cityElem.text = store.find("city").text
                    locElem.append(cityElem)
                    stateElem = etree.Element('state')
                    stateElem.text = store.find("region").text
                    locElem.append(stateElem)
                    zipElem = etree.Element('zip')
                    zipElem.text = store.find("postalcode").text
                    locElem.append(zipElem)
                    phoneElem = etree.Element('phone')
                    phoneElem.text = store.find("phone").text
                    locElem.append(phoneElem)
                    latElem = etree.Element('lat')
                    latElem.text = store.find("lat").text
                    locElem.append(latElem)
                    longElem = etree.Element('long')
                    longElem.text = store.find("lng").text
                    locElem.append(longElem)
                    priceElem = etree.Element('price')
                    priceElem.text = price
                    locElem.append(priceElem)
                    root.append(locElem)
                return root

    return root

def locateGS(title, system, zip, root):

    # Get the code for the system we're searching
    # Also why doesn't Python have switch statements sadface
    if system == "xbox 360":
        system = "1385"
        sysPrefix = "/xbox-360"
    elif system == "playstation 3":
        system = "138d"
        sysPrefix = "/playstation-3"
    elif system == "nintendo wii u":
        system = "131b0"
        sysPrefix = "/nintendo-wii-u"
    elif system == "nintendo wii":
        system = "138a"
        sysPrefix = "/nintendo-wii"
    elif system == "nintendo 3ds":
        system = "131a2"
        sysPrefix = "/nintendo-3ds"
    elif system == "nintendo ds":
        system = "1386"
        sysPrefix = "/nintendo-ds"
    elif system == "ps vita":
        system = "131af"
        sysPrefix = "/ps-vita"
    else:
        system = ""
        sysPrefix = ""

    condition = "-50" # For now we are only doing Used games

    # Get the code for used/new/both (both will have no code)
    #if condition == "Used":
    #    condition = "-50"
    #elif condition == "New":
    #    condition = "-4f"
    #else:
    #    condition = ""

    # Let it be known that I am in too much of a hurry right now to carefully
    # parse out the PostBack, so I am just setting it manually here. It may
    # become stale if GS changes their site in the future.
    eventtarget = "ctl00$mainContentPlaceHolder$dynamicContent$ctl00$RepeaterResultFoundTemplate$ctl01$ResultFoundPlaceHolder$ctl00$ctl00$ctl03$StandardPlaceHolderTop$ctl00$rptResults$ctl00$res$btnPickupInStore"
    # Get the viewstate, gameID, and price
    url ="http://www.gamestop.com/browse%s?nav=16k-3-%s,28zu0,%s%s" % (sysPrefix, title, system, condition)
    url = urllib.quote(url, safe='/,?:=&()')
    # Request the gamestop page
    response = urllib2.urlopen(url)
    html = response.read()
    # Begin parsing the results
    soup = bs4.BeautifulSoup("".join(html))
    # Get the viewstate
    vsTag = soup.find("input", attrs={"name":"__VIEWSTATE"})
    if not vsTag:
        return root
    viewstate = vsTag['value']
    games = soup.findAll("div", attrs={"class":"product preowned_product"})
    gameID = 0
    price = "Unknown"
    for gameOpt in games:
        titleOpt = gameOpt.find("a", attrs={"id":re.compile("hypTitle")}).text
        titleOpt = re.sub("( 1)", " I", titleOpt)
        titleOpt = re.sub("( 2)", " II", titleOpt)
        titleOpt = re.sub("( 3)", " III", titleOpt)
        titleOpt = re.sub(r'[^\w\s]', "", titleOpt)
        titleOpt = str(titleOpt)
        titleOpt = titleOpt.strip()
        titleOpt = titleOpt.lower()
        if titleOpt == title:
            gameIDTag = gameOpt.find("a", attrs={"onclick":re.compile("(WishListItemAdded)(.*)")})
            gameIDTagValue = gameIDTag['onclick']
            matches = re.findall("(?<=')([0-9]*?)(?=')", gameIDTagValue)
            i = 0
            for gameOptID in matches:
				if i == 1:
					gameID = gameOptID
				i = i + 1
            price = gameOpt.find("p", attrs={"class":"pricing"}).text
            break

    # Now that we have viewstate, do a POST instead of a GET so that we
    # can get the full VIEWSTATE, which does not appear to be title nor
    # request/session specific
    data = urllib.urlencode({"__EVENTTARGET":eventtarget, "__EVENTARGUMENT":"", "__LASTFOCUS":"", "__VIEWSTATE":viewstate, "header":"$ctl00$", "searchtext":""})
    req = urllib2.Request(url)
    req.add_data(data)
    response = urllib2.urlopen(req)
    html = response.read()
    # Begin parsing the results
    soup = bs4.BeautifulSoup("".join(html))
    # Get the viewstate
    vsTag = soup.find("input", attrs={"name":"__VIEWSTATE"})
    if not vsTag:
        return root
    viewstate = vsTag['value']

    # Now that we have the full viewstate, do a POST to the store search
    # Normally we'd need to parse out the other form fields from the response
    # above, but right now I am in too much of a hurry to be so thorough and
    # careful. Instead I am just assigning them manually. They may become stale
    # if GS changes their site in the future.
    eventtarget = "ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$StoreSearchControl$FindZipButton"
    scriptField = "ctl00$ctl00$ScriptManager1" # Or should this be encoded? Does urllib encode the fields as well as the values?
    scriptValue = "ctl00$ctl00$ScriptManager1|ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$StoreSearchControl$FindZipButton"
    searchTextField = "ctl00$ctl00$BaseContentPlaceHolder$cHeader$ctl00$searchtext"
    zipField = "ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$StoreSearchControl$EnterZipTextBox"
    storeSavedField = "ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$StoreSearchControl$StoreSavedModalPopup$PopupTargetControl"
    noStoresField = "ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$StoreSearchControl$NoStoresFoundModalPopup$PopupTargetControl"

    url = "http://www.gamestop.com/Browse/StoreSearch.aspx?sku=%s" % gameID

    data = urllib.urlencode(
    { scriptField:scriptValue, searchTextField:"", zipField:zip, "__EVENTTARGET":eventtarget, "__EVENTARGUMENT":"",
    "__LASTFOCUS":"", "__VIEWSTATE":viewstate, storeSavedField:"", noStoresField:"", "ASYNCPOST":"true&" })

    req = urllib2.Request(url)
    req.add_data(data)
    response = urllib2.urlopen(req)
    html = response.read()

    # Begin parsing the results
    soup = bs4.BeautifulSoup("".join(html))

    stores = dict()

    markers = re.findall(re.compile('setMarker(.*)'), html)
    for marker in markers:
        latlongs = re.findall(re.compile('(-{0,}[0-9]{1,}\.[0-9]{1,})'), marker)
        storeInfos = re.findall(re.compile('\'(.+?)\''), marker)
        stores[storeInfos[1]] = (storeInfos[0], latlongs[0], latlongs[1])

    # Example: 6212 -> ( Willow Lawn , 37.582845 , -77.498765 )

    add1RegEx = re.compile('.*Address1.*')
    cityRegex = re.compile('.*CityLabel')
    stateRegex = re.compile('.*StateLabel')
    zipRegex = re.compile('.*ZipLabel')
    phoneRegex = re.compile('.*PhoneLabel')

    storeTable = soup.find(class_="map_results", id="searchResults")
    for key in stores:
        info = storeTable.find("tr", id=key)
        if info:
            locElem = etree.Element('location')
            storeElem = etree.Element('store')
            storeElem.text = 'GameStop'
            locElem.append(storeElem)
            nameElem = etree.Element('name')
            nameElem.text = stores[key][0]
            locElem.append(nameElem)
            add1Elem = etree.Element('address1')
            add1 = info.find("span", id=add1RegEx)
            add1Elem.text = add1.text
            locElem.append(add1Elem)
            cityElem = etree.Element('city')
            city = info.find("span", id=cityRegex)
            cityElem.text = city.text
            locElem.append(cityElem)
            stateElem = etree.Element('state')
            state = info.find("span", id=stateRegex)
            stateElem.text = state.text
            locElem.append(stateElem)
            zipElem = etree.Element('zip')
            zip = info.find("span", id=zipRegex)
            zipElem.text = zip.text
            locElem.append(zipElem)
            phoneElem = etree.Element('phone')
            phone = info.find("span", id=phoneRegex)
            phoneElem.text = phone.text
            locElem.append(phoneElem)
            latElem = etree.Element('lat')
            latElem.text = stores[key][1]
            locElem.append(latElem)
            longElem = etree.Element('long')
            longElem.text = stores[key][2]
            locElem.append(longElem)
            priceElem = etree.Element('price')
            priceElem.text = price
            locElem.append(priceElem)
            root.append(locElem)
    return root

@route('/check')
def check():
    # Get query parameters
    keywords = request.query.keywords
    system = request.query.system
    store = request.query.store

    if not store:
        gsList = scrapeGS(keywords, system)
        bbyList = scrapeBBY(keywords, system)
    elif store == "bby":
        bbyList = scrapeBBY(keywords, system)
        gsList = []
    elif store == "gs":
        gsList = scrapeGS(keywords, system)
        bbyList = []
    else:
        gsList = scrapeGS(keywords, system)
        bbyList = scrapeBBY(keywords, system)

    bbySize = bbyList.count
    gsSize = gsList.count

    # Compare the results and combine so that duplicates
    # are avoided. Combine by saying if a game isn't in
    # the gamestop list (but IS in bestbuy) then add it to
    # the results.
    if bbySize < 1 and gsSize < 1:
        return ""
    elif bbySize > 1:
        for game in bbyList:
            if not game in gsList:
                gsList.append(game)

    # Generate XML
    root = etree.Element('games')
    for title in gsList:
        gameElem = etree.Element('game')
        gameElem.text = title
        root.append(gameElem)

    strResult = etree.tostring(root, pretty_print=True)
    response.content_type = 'text/xml' # We are returning XML
    return strResult

def scrapeBBY(keywords, system):
    # Best Buy requires an API key to use their web service
    bbyApiKey = "crs2yyrur5c9trmtv4uggtd2"
    # Request the Best Buy data
    rawurl = "http://api.remix.bestbuy.com/v1/products(search=%s&categoryPath.name=video games&platform=%s&preowned in(true))?apiKey=%s" % (keywords, system, bbyApiKey)
    url = urllib.quote(rawurl, safe='/,?:=&()')
    response = urllib2.urlopen(url)
    html = response.read()
    # Begin parsing the results
    soup = bs4.BeautifulSoup("".join(html))
    results = list()
    for game in soup.findAll("product"):
        rawName = game.find("name").text
        try:
            title = re.search(u'(.*)(?= \u2014)', rawName).group()
        except AttributeError:
            title = ""
        if title != "":
            title = re.sub("( 1)", " I", title)
            title = re.sub("( 2)", " II", title)
            title = re.sub("( 3)", " III", title)
            title = re.sub(r'[^\w\s]', "", title)
            title.strip
            results.append(title)
    return results

def scrapeGS(keywords, system):

    # Get the code for the system we're searching
    # Also why doesn't Python have switch statements sadface
    if system == "xbox 360":
        system = "1385"
        sysPrefix = "/xbox-360"
    elif system == "playstation 3":
        system = "138d"
        sysPrefix = "/playstation-3"
    elif system == "nintendo wii u":
        system = "131b0"
        sysPrefix = "/nintendo-wii-u"
    elif system == "nintendo wii":
        system = "138a"
        sysPrefix = "/nintendo-wii"
    elif system == "nintendo 3ds":
        system = "131a2"
        sysPrefix = "/nintendo-3ds"
    elif system == "nintendo ds":
        system = "1386"
        sysPrefix = "/nintendo-ds"
    elif system == "ps vita":
        system = "131af"
        sysPrefix = "/ps-vita"
    else:
        system = ""
        sysPrefix = ""

    condition = "-50" # For now we are only doing Used games
    # Get the code for used/new/both (both will have no code)
    #if condition == "Used":
    #    condition = "-50"
    #elif condition == "New":
    #    condition = "-4f"
    #else:
    #    condition = ""

    # Add keywords the the gamestop url
    rawurl = 'http://www.gamestop.com/browse%s?nav=16k-3-%s,28zu0,%s%s' % (sysPrefix, keywords, system, condition)
    # Ensure that we don't encode the commas
    url = urllib.quote(rawurl, safe='/,?:=&')
    # Request the gamestop page
    response = urllib2.urlopen(url)
    html = response.read()
    # Begin parsing the results
    soup = bs4.BeautifulSoup("".join(html))
    # Get the viewstate
    vsTag = soup.find("input", attrs={"name":"__VIEWSTATE"})
    viewstate = vsTag['value']
    # Get the sections containg each game and locate the ID for each
    # which we will need when checking the stores later
    # For each ID, add to a dict mapping the game's title to the ID
    results = list()
    games = soup.findAll("div", attrs={"class":"product preowned_product"}) # This will need to be changed to handle new products when conditions are introduced
    for game in games:
        title = game.find("a", attrs={"id":re.compile("hypTitle")}).text
        title = re.sub("( 1)", " I", title)
        title = re.sub("( 2)", " II", title)
        title = re.sub("( 3)", " III", title)
        title = re.sub(r'[^\w\s]', "", title)
        title = str(title)
        title = title.strip()
        results.append(title)
    return results

run(server='gae')
#run()
