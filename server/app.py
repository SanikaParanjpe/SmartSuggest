from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pymongo
import itertools
import snscrape.modules.twitter as sntwitter
import time
import re
from nltk import word_tokenize
from nltk.corpus import stopwords
from flask import Flask, request
import requests
from datetime import datetime, timedelta
import pandas
from string import punctuation
import nltk
import json
import glob
import api_keys
from pytz import timezone
nltk.download("stopwords")
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')

# initialize app
app = Flask(__name__)

# constants
my_stopwords = ["im", "with", "the", "let's", "a", "an", "", 'i', "i'm", "i've", "i'll", "i'd", 'me', 'my', 'myself', 'we', "we're", "we've", "we'll", "we'd", 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', "he's", "he'll", "he'd", 'him', 'his', 'himself', 'she', "she's", "she'll", "she'd", 'her', 'hers', 'herself', 'it', "it's", "it'll", "it'd", 'its', 'itself', 'they', "they're", "they've", "they'll", "they'd", 'them', 'their', 'theirs', 'themselves', 'what', "what's", 'which', 'who', "who's", "who've", "who'll", "who'd", 'whom', 'when', 'where', 'why', 'how', 'this', 'that', "that's", "that'll", "that'd", 'these', 'those', 'here', 'there', "there's", "there'll", "there'd", 'am', 'is', 'isn', "isn't", 'are', 'aren', "aren't", 'was', 'wasn', "wasn't", 'were', 'weren', "weren't", 'be', 'been', 'being', 'have', 'haven', "haven't", 'has', 'hasn', "hasn't", 'had', 'hadn', "hadn't", 'having', 'ain', "ain't", 'do', 'don', "don't", 'does', 'doesn', "doesn't", 'did', 'didn', "didn't", 'done', 'doing', 'will', 'won', "won't", 'would', 'wouldn', "wouldn't", "would've", 'shall', 'shan', "shan't", 'can', 'cannot', 'could', 'couldn', "couldn't", "could've", 'may', 'mayn', "mayn't", 'might', 'mightn', "mightn't", "might've", 'must', 'mustn', "mustn't", "must've", 'need', 'needn', "needn't", 'should', 'shouldn', "shouldn't", "should've", 'ought', 'oughtn', "oughtn't", 'dare', 'daren', "daren't", 'm', 're', 't', 's', 've', 'll', 'd', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                'so', 'than', 'too', 'very', 'just', 'now', 'o', 'y', 'ma', 'i', 'im', 'ive', 'ill', 'id', 'me', 'my', 'myself', 'we', 'were', 'weve', 'well', 'wed', 'our', 'ours', 'ourselves', 'you', 'youre', 'youve', 'youll', 'youd', 'your', 'yours', 'yourself', 'yourselves', 'he', 'hes', 'hell', 'hed', 'him', 'his', 'himself', 'she', 'shes', 'shell', 'shed', 'her', 'hers', 'herself', 'it', 'its', 'itll', 'itd', 'its', 'itself', 'they', 'theyre', 'theyve', 'theyll', 'theyd', 'them', 'their', 'theirs', 'themselves', 'what', 'whats', 'which', 'who', 'whos', 'whove', 'wholl', 'whod', 'whom', 'when', 'where', 'why', 'how', 'this', 'that', 'thats', 'thatll', 'thatd', 'these', 'those', 'here', 'there', 'theres', 'therell', 'thered', 'am', 'is', 'isn', 'isnt', 'are', 'aren', 'arent', 'was', 'wasn', 'wasnt', 'were', 'weren', 'werent', 'be', 'been', 'being', 'have', 'haven', 'havent', 'has', 'hasn', 'hasnt', 'had', 'hadn', 'hadnt', 'having', 'ain', 'aint', 'do', 'don', 'dont', 'does', 'doesn', 'doesnt', 'did', 'didn', 'didnt', 'done', 'doing', 'will', 'won', 'wont', 'would', 'wouldn', 'wouldnt', 'wouldve', 'shall', 'shan', 'shant', 'can', 'cannot', 'could', 'couldn', 'couldnt', 'couldve', 'may', 'mayn', 'maynt', 'might', 'mightn', 'mightnt', 'mightve', 'must', 'mustn', 'mustnt', 'mustve', 'need', 'needn', 'neednt', 'should', 'shouldn', 'shouldnt', 'shouldve', 'ought', 'oughtn', 'oughtnt', 'dare', 'daren', 'darent', 'm', 're', 't', 's', 've', 'll', 'd', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'o', 'y', 'ma']

more_stopwords = ['word', 'time', 'number', 'way people  water', 'day', 'part', 'sound', 'work', 'place', 'year', 'back', 'thing', 'name', 'sentence', 'man', 'line', 'boy', 'farm', 'end', 'men', 'land', 'home', 'hand', 'picture', 'air', 'animal', 'house', 'page', 'letter', 'point', 'mother', 'answer', 'America', 'world', 'food', 'country', 'plant', 'school', 'father', 'tree', 'city', 'earth', 'eye', 'head', 'story', 'example', 'life', 'paper   group', 'children', 'side', 'feet', 'car mile', 'night', 'sea', 'river', 'state', 'book', 'idea', 'face', 'Indian', 'girl', 'mountain', 'list', 'song', 'family', 'whoever', '’re', 'was', 'sometime', '‘d', 'from', 'such', 'bottom', 'becoming', 'do', 'ever', 'anyone', 'else', 're', 'whereby', 'throughout', 'hereupon', 'third', 'latter', 'your', 'often', 'along', 'my', '’s', 'both', 'am', 'using', 'since', 'first', 'it', 'made', '‘m', 'when', 'below', 'for', 'on', 'yet', 'beforehand', 'out', 'her', 'as', 'how', 'his', 'towards', 'of', 'myself', 'none', 'but', 'formerly', 'eleven', 'so', 'really', 'together', 'should', 'between', 'three', 'whose', 'n’t', 'n‘t', 'anyway', 'just', 'whereupon', 'even', 'being', 'hereafter', 'otherwise', 'top', "'d", 'go', "'s", 'however', 'nevertheless', 'while', 'cannot', 'besides', '‘s', 'herself', '’ve', '‘re', 'must', 'any', 'off', 'back', 'a', 'indeed', 'somewhere', 'two', 'than', 'keep', 'why', 'six', 'their', 'into', 'after', 'give', 'please', 'did', 'some', 'will', 'its', 'against', 'in', 'may', 'whence', 'itself', 'forty', 'empty', 'now', 'ours', 'whither', 'former', 'an', 'him', 'well', 'across', 'become', 'about', 'onto', 'around', 'never', 'anywhere', 'very', 'something', 'with', 'fifteen', 'further', 'seeming', 'or', 'although', 'see', 'those', "yall",
                  'noone', 'still', 'yourselves', 'under', 'almost', 'yourself', 'seems', 'this', 'others', '’ll', 'our', 'side', 'because', 'before', 'always', 'fifty', 'take', 'own', 'via', 'whereas', 'which', 'whole', 'full', 'they', 'beside', 'thereupon', 'whenever', 'most', 'wherever', 'she', 'few', 'another', 'ten', 'does', '‘ll', 'that', 'among', 'namely', 'he', 'anyhow', 'all', 'where', 'through', 'though', 'twelve', 'who', 'doing', 'various', 'therefore', 'either', 'several', 'moreover', 'done', 'hereby', 'whereafter', 'less', 'above', 'rather', 'mine', 'thereby', 'say', 'alone', 'part', 'used', 'front', 'due', 'are', 'seemed', 'more', 'at', 'you', 'amongst', 'and', 'could', 'thereafter', 'over', 'someone', 'hence', 'many', 'what', 'here', 'hundred', 'everyone', 'no', 'unless', 'seem', 'yours', 'nobody', 'if', 'nor', 'ourselves', 'might', 'would', 'were', 'one', 'we', 'became', 'had', "'re", 'four', 'put', '’m', 'twenty', "n't", 'then', 'show', 'the', 'himself', 'whatever', 'be', 'regarding', 'already', 'themselves', 'enough', 'eight', 'until', 'latterly', 'nowhere', 'nine', 'get', 'there', 'name', 'hers', 'within', 'make', 'during', 'least', 'everywhere', 'behind', 'been', 'per', 'these', 'them', 'neither', 'is', 'whether', 'much', 'once', 'serious', 'without', 'too', 'last', 'whom', 'elsewhere', 'perhaps', '’d', 'quite', 'each', 'can', 'mostly', '‘ve', 'only', 'sixty', 'herein', 'therein', 'except', 'ca', 'upon', 'thru', 'also', 'move', 'toward', 'has', 'next', 'nothing', 'thus', 'call', 'have', 'again', 'us', 'i', 'becomes', 'amount', 'same', 'by', "'ve", 'wherein', 'everything', 'five', 'me', 'to', 'beyond', 'afterwards', 'every', "'ll", 'meanwhile', 'up', "'m", 'somehow', 'other', 'not', 'thence', 'anything', 'down', 'sometimes']


myclient = pymongo.MongoClient("mongodb://admin:password@mongodb-test:27017/")

mydb = myclient["mydatabase"]
sentiments = mydb["sentiments"]
# sentiments.drop()
twitter_keywords = mydb["twitter_keywords"]
news_keywords = mydb["news_keywords"]
# news_keywords.drop()


def removeDuplicates(lst):
    return [t for t in (set(tuple(i) for i in lst))]


@app.route('/update_sentiment', methods=["POST"])
def update_sentiment():
    # sentiment_request = {"tweet": "Your tweet", "sentiment": 6, "city": "Bloomington"}
    sentiment_request = request.get_json()
    print(sentiment_request)
    try:
        ispresent = sentiments.find_one({"_id": sentiment_request['city']})
        print(ispresent)
        if ispresent:
            if sentiment_request['sentiment'] > 0:
                print('Update +ve sentiment in db for a city')
                sentiments.update_one({"_id": sentiment_request['city']}, {
                    "$set": {"sentiment": {"positive": (ispresent["sentiment"]['positive'] + 1),
                                           "negative": (ispresent["sentiment"]['negative']),
                                           "neutral": (ispresent["sentiment"]['neutral'])}}})
                
            elif sentiment_request['sentiment'] < 0:
                print('Update -ve sentiment in db for a city')
                sentiments.update_one({"_id": sentiment_request['city']}, {
                    "$set": {"sentiment": {"positive": (ispresent["sentiment"]['positive']),
                                           "negative": (ispresent["sentiment"]['negative'] + 1),
                                           "neutral": (ispresent["sentiment"]['neutral'])}}})

            else:
                print('Update neutral sentiment in db for a city')
                sentiments.update_one({"_id": sentiment_request['city']}, {
                    "$set": {"sentiment": {"positive": (ispresent["sentiment"]['positive']),
                                           "negative": (ispresent["sentiment"]['negative']),
                                           "neutral": (ispresent["sentiment"]['neutral'] + 1)}}})

                
        else:
            if sentiment_request['sentiment'] > 0:
                sentiments.insert_one({'_id': sentiment_request["city"], 'sentiment': {
                                      "positive": 1, "negative": 0, "neutral": 0}})
            elif sentiment_request['sentiment'] < 0:
                sentiments.insert_one({'_id': sentiment_request["city"], 'sentiment': {
                                      "positive": 0, "negative": 1, "neutral": 0}})
            else:
                sentiments.insert_one({'_id': sentiment_request["city"], 'sentiment': {
                                      "positive": 0, "negative": 0, "neutral": 1}})

            print('Insert sentiment in db for a new city')

        sentiment_response = []

        for sentiment in sentiments.find({}):
            sentiment_response.append(sentiment)

        return json.dumps(sentiment_response)
    except Exception as e:
        print(e)
        return "Failed"


@app.route('/news_catcher_api')
def news_data():
    try:
        print("In news_data")
        tz = timezone('EST')
        d_now = datetime.now(tz)
        d_minus_one_minute = d_now - timedelta(hours=0, minutes=5)
        d_now_string = d_now.strftime("%Y/%m/%d %H:%M:%S")
        d_minus_one_minute_string = d_minus_one_minute.strftime(
            "%Y/%m/%d %H:%M:%S")

        API_KEY = api_keys.news_catcher_api_key
        print(API_KEY)
        sports_related_words = "sport OR sports OR game OR competition OR athletics OR soccer OR athletic OR activity OR polo OR skating OR tennis OR hobby OR football OR hockey OR racing OR team OR cycling OR fitness OR referee OR sportsman OR skill OR rugby OR gymnastics OR athlete OR offside OR sports OR coach OR downfield OR skateboard OR performance OR \"association football\" OR show OR archery OR safari OR champion OR supersport OR pack OR exercise OR \"rugby union\" OR hobbies OR active OR players OR fighting OR feature OR \"spectator sport\" OR league OR \"water sport\" OR fun OR judo OR gym OR physical OR recreation OR \"professional sport\" OR health OR limited OR snowboarding OR \"amateur boxing\" OR premium OR company OR basketball OR most-valuable OR rugger OR \"sports league\" OR soccerball OR entertainment OR \"contact sport\" OR funambulism OR art OR athletes OR skiing OR esport OR muscle OR ski OR hunting OR eco OR music OR frolic OR \"water ski\" OR movement OR \"mountain biking\" OR tournaments OR diver OR \"sanctioning body\" OR diversion OR defense OR wakeboarding OR pastimes OR \"roller derby\" OR spectator OR amateur OR dexterity OR equitation OR jocularity OR witticism OR surfboard OR cricket OR sportsaholic OR lusorious OR equestrianism OR competitor OR spar OR lark OR disport OR standard OR action OR \"blood sport\" OR social OR skylark OR gambol OR romp OR dance OR class OR concert OR comfort OR frisk OR rollick OR job OR community OR activities OR cavort OR casual OR suit OR dive OR blazers OR culture OR motorsports OR \"mixed martial arts\" OR discipline OR sport OR schuss OR challenge OR motorcycling OR organization OR combat OR lifestyle OR tradition OR profession OR club OR \"sporting events\" OR utility OR news OR smart OR horseracing OR lead OR esports OR dynamic OR career OR multisport OR chess OR luge OR \"drag racing\" OR fast OR video OR cross OR \"horse racing\" OR \"governing body\" OR \"sports federations\" OR bike OR life OR hunters OR enduro OR events OR skateboarding OR \"sanctioning bodies\" OR teams OR \"thoroughbred racing\" OR motorsport OR compete OR competing OR season OR nascar OR mountaineer OR hike OR disqualified OR soccerplex OR championship OR subbuteo OR peloponnese OR competed OR \"tightrope walking\" OR bucketball OR \"mind sport\" OR snowsport OR \"roller hockey\" OR nongame OR \"sport game\" OR \"water polo\" OR \"extreme sport\" OR metagaming OR subgame OR vacationer OR \"basket ball\" OR gameplayer OR watersport OR \"ping pong\" OR \"violent sport\" OR education OR \"sport card\" OR \"real tennis\" OR \"outdoor game\" OR \"olympic sport\" OR cross-country OR wintersports OR \"snow ski\" OR \"sports betting\" OR \"canadian football\" OR \"combat sport\" OR \"team sport\" OR baseball OR \"athletic game\" OR touring OR super OR event OR sportsmanship OR race OR tactical OR \"professional basketball\" OR target OR call OR \"outdoor sport\" OR olympic OR work OR street OR school OR working OR \"speed skate\" OR run OR riding OR jackknife OR training OR sportswoman OR dress OR normal OR \"ice skate\" OR \"figure skate\" OR kill OR outdoor OR adv OR \"roller skate\" OR adventure OR \"physical activity\" OR workout OR play OR competitive OR martial OR running OR luxury OR \"daisy cutter\" OR games OR pro OR boast OR badminton OR tool OR business OR volleyball OR bouldering OR field OR practice OR \"run around\" OR food OR yoga OR sportive OR \"downhill skiing\" OR jacket OR television OR dirt OR car OR boulder OR form OR instrument OR pastime OR \"intercollegiate athletics\" OR karting OR professional OR \"alpine skiing\" OR triathlons OR \"olympic games\" OR \"figure skating\" OR competitions OR intercollegiate OR \"council of europe\" OR \"beach volleyball\" OR lacrosse OR cut OR federation OR good OR well OR cars OR federations OR coaches OR eventing OR paralympics OR golf OR \"athletic prowess\" OR supercross OR bullfighting OR \"ultimate frisbee\" OR subculture OR sporting OR \"bull riding\" OR weightlifting OR \"anti doping\" OR paralympic OR playing OR watersports OR sportsperson OR sumo OR motocross OR playoffs OR athleticism OR sportsbook OR olympics OR sleigh OR racers OR ironman OR sled OR skate OR manager OR jog OR handler OR defence OR series OR trial OR side OR humour OR tuck OR save OR humor OR possession OR stroke OR foul OR shot OR row OR sledding OR aquatics OR away OR backpack OR pass OR flip OR line OR rappel OR comedy OR home OR tramp OR overhand OR box OR legal OR dribble OR underhanded OR carry OR loose OR drive OR racket OR punt OR submarine OR kick OR bandy OR underhand OR down OR hurdle OR drop OR snorkel OR clowning OR umpire OR surf OR shoot OR start OR seed OR surge OR underarm OR round OR turn OR bout OR onside OR paddle OR defending OR average OR kayak OR wit OR canoe OR timer OR scull OR shooter OR bob OR scout OR leagues OR timekeeper OR biathlon OR goal OR dodgeball OR racer OR floorball OR skin-dive OR jocosity OR one-on-one OR man-to-man OR wittiness OR waggishness OR logrolling OR double-team OR overhanded OR abseil OR overarm OR windsurf OR shadowbox OR birling OR offsides OR outclass OR wrestling OR prizefight OR sporter OR sportful OR gameday OR nonsports OR outsport OR footballer OR sportless OR powerlifting OR acrobatic OR sportlike OR go OR paddlesport OR gamesome OR sportsplex OR postseason OR pickleball OR passtime OR kiteboarding OR slalom OR sportling OR birle OR world OR skateboarder OR racquet OR \"british english\" OR bowling OR diving OR competes OR sportsfield OR dropkick OR skater OR clubs OR formula OR pharaoh OR cheerlead OR minigame OR swimming OR bicycle OR snowboard OR gamely OR motorcycle OR youth OR brand OR iran OR ever OR model OR uci OR f1 OR puck OR racquetball OR riders OR postgame OR trashsport OR popular OR powerboating OR jousting OR friendly OR netball OR models OR softball OR best OR driving OR women OR experience OR association OR venue OR roller OR fia OR pigskin OR standards OR fit OR european OR drivers OR tour OR national OR \"game plan\" OR wogball OR \"press box\" OR \"free agent\" OR \"professional wrestling\" OR \"professional boxing\" OR \"bench warmer\" OR \"horseback riding\" OR \"track and field\" OR \"professional golf\" OR \"out of play\" OR \"ski jump\" OR \"talent scout\" OR \"gymnastic exercise\" OR \"professional tennis\" OR \"field sport\" OR \"line of work\" OR \"defending team\" OR \"follow through\" OR \"at home\" OR \"free agency\" OR \"won-lost record\" OR \"rock climbing\" OR \"warm the bench\" OR \"sit out\" OR \"rope down\" OR \"ride the bench\" OR gambling OR nongamer OR \"regulation of sport\" OR gaymer OR \"table tennis\" OR boxing OR \"broadcasting of sports events\" OR \"field hockey\" OR telegaming OR woodball OR \"blow football\" OR upfield OR \"professional football\" OR \"professional baseball\" OR manual OR mutation OR \"sudden death\" OR tournament OR \"lark about\" OR the OR hiking OR extracurricular OR bmx OR triathlon OR sportaccord OR deficit OR ref OR mma OR variation OR summercater OR toss OR occupation OR curl OR waggery OR championships OR \"american english\" OR \"tie-breaking methods\" OR enthusiasts OR sponsorship OR for OR \"iron man\" OR \"association of ioc recognised international sports federations\" OR tennikoit OR \"individual sport\" OR gamification OR rioting OR hooliganism OR zourkhaneh OR \"sports journalism\" OR gameography OR \"rough sport\" OR skibobbing OR \"sport venue\" OR fanwear OR \"old french\" OR \"bench warm\" OR concussion OR \"devise structure activity\" OR \"four square\" OR rowing OR toboggan OR blazer OR \"personal foul\" OR naked OR recreational OR track OR bobsled OR trad OR rollerblade OR mutant OR \"regulation time\" OR trophy OR wipeout OR ineligible OR position OR leisure OR bewegung OR industry OR fingering OR english OR spread-eagle OR \"contract bridge\" OR transgender"

        url = "https://api.newscatcherapi.com/v2/search"

        querystring = {"q": sports_related_words, "lang": "en", "page": "1",
                       "from": d_minus_one_minute_string, "to": d_now_string, "countries": 'US', "topic": "sport"}

        headers = {
            "x-api-key": API_KEY
        }

        response = requests.request(
            "GET", url, headers=headers, params=querystring)
        response = response.json()
        print("response", response)
        # save data in csv
        # response_df = pandas.DataFrame(response['articles'])
        # filename = 'news_data.csv'
        # response_df.to_csv(filename)

        return response
    except Exception as e:
        print(e)
        return "failed from news data function"


@app.route('/sentiment')
def sentiment():
    try: 
        sentiment_response = []
        print(sentiments.find({}))
        if list(sentiments.find({})) != []:

            for sentiment in sentiments.find({}):
                sentiment_response.append(sentiment)
        else:
            result = pandas.read_csv('all_new_data.csv')
            result = result.dropna(subset=['sentiment', 'locations'])

            # cut out the headers
            result_locations = result[1:]

            # To update sentiment
            location_wise_sentiment = {}

            for index, row in result_locations.iterrows():
                location = json.loads(row['locations'])

                if location:
                    for value in location:
                        if value:
                            if 'city' in value.keys():
                                if value['city']:
                                    sentiment = json.loads(row['sentiment'])
                                    # print(sentiment)
                                    key = max(sentiment, key=sentiment.get)
                                    print(key)
                                    print(type(key))

                                    if value['city'] in location_wise_sentiment.keys():
                                        location_wise_sentiment[value['city']
                                                                ][key] += 1
                                    else:
                                        sentiment_obj = {}

                                        for key in sentiment:
                                            sentiment_obj[key] = 0

                                        sentiment_obj[key] = 1
                                        location_wise_sentiment[value['city']
                                                                ] = sentiment_obj

            print(location_wise_sentiment)

            for key, value in location_wise_sentiment.items():
                if sentiments.count_documents({'_id': key}, limit=1):
                    news_keywords.delete_one({"_id": key})

                sentiments.insert_one({'_id': key, 'sentiment': value})

            for sentiment in sentiments.find({}):
                sentiment_response.append(sentiment)

        return json.dumps(sentiment_response)
    except Exception as e:
        print("Exception",e)
        return "Failed"


@app.route('/news')
def news():
    print("NEWSSSSSS------")
    try:
        # result = pandas.read_csv('all_new_data.csv')
        result = news_data()
        print("Result 1:", result)
        result = pandas.DataFrame(result['articles'])
        print("Result 2:",result)
        # stop words
        stop_words = stopwords.words('english')
        stop_words.extend(my_stopwords)
        stop_words.extend(more_stopwords)
        result['title_new'] = result['title'].apply(lambda x: ' '.join(
            [word.lower() for word in x.split() if (word not in (stop_words) and len(word) > 2)]))

        # remove punctuation
        my_punc = punctuation + "“" + "’" + "”" + "…" + "‘"

        result['title_new'] = result['title_new'].apply(
            lambda x: x.translate(str.maketrans('', '', my_punc)))

        # to get key value pairs
        # these are the POS tags we are filtering (only comman and proper nouns)
        required = ["NN", "NNS", "NNP", "NNPS"]

        temp_storage = {}

        for data in result['title_new']:
            tokens = word_tokenize(data)
            tags = nltk.pos_tag(tokens)
            tags = [x for x in tags if (x[1] in required)]

            tags = removeDuplicates(tags)
            for tag, y in tags:
                if tag in temp_storage.keys():
                    for x, y in tags:
                        if x in temp_storage[tag]:
                            temp_storage[tag][x] += 1
                        else:
                            temp_storage[tag][x] = 1
                else:
                    temp_storage[tag] = {}
                    for x, y in tags:
                        if x == tag:
                            continue
                        if x in temp_storage[tag]:
                            temp_storage[tag][x] += 1
                        else:
                            temp_storage[tag][x] = 1

        print('temp Storage', temp_storage)

        # Store key-value pairs in MongoDB
        for key, value in temp_storage.items():
            if news_keywords.count_documents({'_id': key}, limit=1):
                news_keywords.delete_one({"_id": key})

            news_keywords.insert_one({'_id': key, 'news_keywords': value})

        news_keywords_local = news_keywords.find({})

        for document in news_keywords_local:
            print("doc",document)

        return "works"
    except Exception as e:
        print(e)
        return "failed from news api"


@app.route("/twitter")
def twitter():
    print("Twitter------")
    sports_hashtags = "(sports OR sport OR #sports OR #sport)"
    until_time = datetime.now()
    until_time = int(time.mktime(until_time.timetuple()))
    since_time = datetime.today() - timedelta(hours=0, minutes=5)
    since_time = int(time.mktime(since_time.timetuple()))

    print(until_time)
    print(since_time)
    place_id = '96683cc9126741d1'  # USA
    # min_replies:10
    query = f'{sports_hashtags} place:{place_id} until_time:{str(until_time)} since_time:{str(since_time)} lang:en -filter:replies'

    try:
        df_coord = pandas.DataFrame(itertools.islice(
            sntwitter.TwitterSearchScraper(query, top=True).get_items(), 1000))

        df_coord.dropna(subset=['place'], inplace=True)
        df_coord['user_location'] = df_coord['place'].apply(
            lambda x: x['fullName'])
        print(df_coord.columns)
        df_coord = df_coord.drop(columns=['url', 'id',
                                          'replyCount', 'retweetCount', 'quoteCount',
                                          'conversationId', 'lang', 'source', 'sourceUrl', 'links', 'sourceLabel', 'retweetedTweet', 'quotedTweet', 'inReplyToTweetId',
                                          'inReplyToUser', 'card', 'viewCount', "vibe", "media", "cashtags"])

        print(len(df_coord))
        print(df_coord.head())

        # Remove english stop words from nltk
        stop_words = stopwords.words('english')
        stop_words.append(my_stopwords)
        stop_words.append(more_stopwords)
        df_coord['clean_content'] = df_coord['rawContent'].apply(lambda x: ' '.join(
            [word.lower() for word in x.split() if (word.lower() not in (stop_words) and len(word) > 3)]))

        # Remove links (http://)
        df_coord['clean_content'] = df_coord['clean_content'].apply(
            lambda x: re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', x))

        # Remove punctuations except #
        my_punctuation = punctuation.replace("#", "")
        # my_punctuation = my_punctuation.replace("@", "")
        my_punctuation = my_punctuation + "“" + "’" + "”" + "…" + "‘"
        print(my_punctuation)
        df_coord['clean_content'] = df_coord['clean_content'].apply(
            lambda x: x.translate(str.maketrans('', '', my_punctuation)))

        # to get key value pairs

        # these are the POS tags we are filtering (only comman and proper nouns)
        required = ["NN", "NNS", "NNP", "NNPS"]

        temp_storage = {}

        for data in df_coord["clean_content"]:
            print(data)
            words = data.split(" ")
            for word in words:
                if "#" in word:
                    words.remove(word)
                    words.append(word[1:])
            data = " ".join(words)

            tokens = word_tokenize(data)
            tags = nltk.pos_tag(tokens)
            tags = [x for x in tags if (x[1] in required)]

            tags = removeDuplicates(tags)
            for tag, y in tags:
                if tag in temp_storage.keys():
                    for x, y in tags:
                        if x in temp_storage[tag]:
                            temp_storage[tag][x] += 1
                        else:
                            # temp_storage[tag] = x
                            temp_storage[tag][x] = 1
                else:
                    temp_storage[tag] = {}
                    for x, y in tags:
                        if x == tag:
                            continue
                        if x in temp_storage[tag]:
                            temp_storage[tag][x] += 1
                        else:
                            # temp_storage[tag] = x
                            temp_storage[tag][x] = 1

        # print(tags)
        print(temp_storage)

        # Store key-value pairs in MongoDB
        for key, value in temp_storage.items():
            if twitter_keywords.count_documents({'_id': key}, limit=1):
                twitter_keywords.delete_one({"_id": key})

            twitter_keywords.insert_one(
                {'_id': key, 'twitter_keywords': value})

        twitter_keywords_all = twitter_keywords.find({})

        for document in twitter_keywords_all:
            print(document)
        return "works"
    except Exception as e:
        print(e)
        return "failed"


@app.route('/suggest_hashtags', methods=["POST"])
def suggest_hashtags():
    try:
        # request = {"tweet": "exercise is an art human subway bucket ohio hunter"}
        suggestion_request = request.get_json()

        required = ["NN", "NNS", "NNP", "NNPS"]
        tokens = word_tokenize(suggestion_request['tweet'])
        tags = nltk.pos_tag(tokens)
        tags = [x for x in tags if (x[1] in required)]
        only_tags = [tag.lower() for tag, _ in tags]

        news_hashtags = news_keywords.find({'_id': {"$in": only_tags}})
        twitter_hashtags = twitter_keywords.find({'_id': {"$in": only_tags}})

        final_hashtags_news = {}
        final_hashtags_twitter = {}

        for doc in news_hashtags:
            final_hashtags_news.update(doc['news_keywords'])

        for doc in twitter_hashtags:
            final_hashtags_twitter.update(doc['twitter_keywords'])

        final_hashtags_news = sorted(final_hashtags_news, reverse=True)
        final_hashtags_twitter = sorted(final_hashtags_twitter, reverse=True)

        final_hashtags = {}
        final_hashtags['news_hashtags'] = final_hashtags_news
        final_hashtags['twitter_hashtags'] = final_hashtags_twitter

        return json.dumps(final_hashtags)
    except Exception as e:
        print(e)
        return "failed"

sched = BackgroundScheduler(daemon=True)
sched.add_job(news, 'interval', minutes=1)
# sched.add_job(twitter, 'interval', minutes=1)
sched.start()
