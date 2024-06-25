import base64
from email import utils
from bson import ObjectId
import tornado.web
import tornado.ioloop
import utils.db

from utils.jwt import decode


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def get_current_user(self):
        auth_cookie = self.get_secure_cookie("auth_token")
        if auth_cookie:
            try:
                token = auth_cookie.decode('utf-8')
                return decode(token)
            except Exception as e:
                print(f"Error decoding token: {e}")
                return None
        return None
    
class UserHandler(BaseHandler):
    def initialize(self, db, fs):
        self.db = db
        self.fs = fs

    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            spots = await utils.db.findAllSpots()  
            spot_list = []
            for spot in spots:
                spot['_id'] = str(spot['_id'])
                spotRating = await utils.db.findRatingBySpotId(ObjectId(spot['_id']))
                if spotRating is not None:
                    avg_rating = await utils.db.get_average_rating(ObjectId(spot['_id']))
                    numOf_rating = await utils.db.get_numberOf_rating(ObjectId(spot['_id']))
                    print(numOf_rating)
                    spot['average_rating'] = avg_rating[0] if avg_rating else None
                    spot['number_of_rating'] = numOf_rating[0] if numOf_rating else None
                city = await utils.db.findCityById(spot['address']['city'])
                states = await utils.db.findStateById(spot['address']['state'])
                country = await utils.db.findCountryById(spot['address']['country'])
                spot['address']['city'] = city['name']
                spot['address']['state'] = states['name']
                spot['address']['country'] = country['name']
                category = await utils.db.findCategoryById(spot['category'])
                spot['category'] = category['name']
                spot['image_id'] = str(spot['image_id'])
                spotImages = await utils.db.findSpotImages(ObjectId(spot['image_id']))
                if spotImages:
                    spotImages['_id'] = str(spotImages['_id'])
                    spotImages['data'] = base64.b64encode(spotImages['data']).decode('utf-8')
                    spot['spot_image'] = spotImages
                # print(spot)
                spot_list.append(spot)

            self.set_status(200)
            self.write({"status": "success", "data": spot_list})
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": str(e)})