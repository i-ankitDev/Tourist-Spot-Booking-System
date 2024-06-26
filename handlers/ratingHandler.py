from bson import ObjectId
import tornado.web
import tornado.ioloop
from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler

class RatingHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        try:
            user=self.get_current_user()
            user=await utils.db.findUserById(ObjectId(user['_id']))
            UserRating=await utils.db.findRating(user['_id'])
            if UserRating is None:
                if user is not None:
                    spot_id = self.get_query_argument("spot_id")
                    if spot_id is not None:
                        data = tornado.escape.json_decode(self.request.body)
                        rating = float(data.get("rating"))
                        if rating <= 5:
                            comment = data.get("comment")
                            mydict= {
                                "spot_id" : ObjectId(spot_id),
                                "user_id":user['_id'],
                                "rating":rating,
                                "comment":comment
                            }
                            await utils.db.saveRating(mydict)
                            self.set_status(200)
                            self.write(({"status": True, "message": "Rating saved"}))
                        else:
                            self.set_status(400)
                            self.write(({"status": False, "message": "Rating should be less than 6"}))
                    else:
                        self.set_status(400)
                        self.write(({"status": False, "message": "Spot not found"}))
                else:
                    self.set_status(400)
                    self.write(({"status": False, "message": "User not found"}))
            else:
                self.set_status(400)
                self.write(({"status": False, "message": "User already rated"}))
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))

    async def put(self):
        user=self.get_current_user()
        try:
            user=await utils.db.findUserById(ObjectId(user['_id']))
            UserRating=await utils.db.findRating(user['_id'])
            if user is not None and UserRating is not None:
                spot_id = self.get_query_argument("spot_id")
                if spot_id is not None:
                    data = tornado.escape.json_decode(self.request.body)
                    rating = float(data.get("rating"))
                    if rating <= 5:
                        comment = data.get("comment")
                        await utils.db.updateRating(UserRating['_id'],rating,comment)
                        self.set_status(200)
                        self.write(({"status": True, "message": "Rating updated"}))
                    else:
                        self.set_status(400)
                        self.write(({"status": False, "message": "Rating should be less than 6"}))
                else:
                    self.set_status(400)
                    self.write(({"status": False, "message": "Spot not found"}))
            else:
                self.set_status(400)
                self.write(({"status": False, "message": "User not found or Rating not saved"}))
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))

    