import pymongo
import certifi

uri = "mongodb+srv://syncduplicate:t5J2uJ3IvHofHi2S@ginsdb.ycefz.mongodb.net/?retryWrites=true&w=majority&appName=ginsDB"
client = pymongo.MongoClient(uri, tlsCAFile=certifi.where())
mydb = client['BotGinTags']
mycol = mydb['IdeaTags']

def db_addData(data):
    if data:
        mycol.insert_one(data)
        print("Inserted new data into the database.")
    else:
        print("No new data to insert.")

def db_readData(query, isFindOne=False):
    if isFindOne:
        data = mycol.find_one(query)
    else:
        data = mycol.find(query)
    return data
