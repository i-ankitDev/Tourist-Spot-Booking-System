import time
from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient

myclient = MongoClient('mongodb://localhost:27017')
mydb = myclient["Tourist_Spot_Booking_System"]

def update_document():
    query = {"isOpened": False}
    update = {"$set": {"isOpened": True}}
    result = mydb.spots.update_many(query, update)
    print(f"Updated {result.modified_count} documents.")

scheduler = BackgroundScheduler(timezone='Asia/Kolkata')


scheduler.add_job(update_document, 'cron', hour='13', minute='57')

scheduler.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
