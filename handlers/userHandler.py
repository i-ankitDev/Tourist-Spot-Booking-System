import base64
from email import utils
from bson import ObjectId
import motor
import tornado.web
import tornado.ioloop
import utils.db

from utils.jwt import decode
from handlers.auth import BaseHandler

myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = myclient["Tourist_Spot_Booking_System"]
    
class UserHandler(BaseHandler):
    def initialize(self, db, fs):
        self.db = db
        self.fs = fs

    async def get(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            pipeline=[
                {
                    '$lookup': {
                        'from': 'spotTicket', 
                        'localField': '_id', 
                        'foreignField': 'spot_id', 
                        'as': 'tickets'
                    }
                }, {
                    '$lookup': {
                        'from': 'rating', 
                        'localField': '_id', 
                        'foreignField': 'spot_id', 
                        'as': 'ratings'
                    }
                }, {
                    '$unwind': {
                        'path': '$ratings', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$group': {
                        '_id': '$_id', 
                        'name': {
                            '$first': '$name'
                        }, 
                        'image': {
                            '$first': '$image'
                        }, 
                        'address': {
                            '$first': '$address'
                        }, 
                        'category': {
                            '$first': '$category'
                        }, 
                        'isActive': {
                            '$first': '$isActive'
                        }, 
                        'rating': {
                            '$avg': '$ratings.rating'
                        }, 
                        'tickets': {
                            '$push': '$$ROOT'
                        }
                    }
                }, {
                    '$unwind': {
                        'path': '$tickets', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$lookup': {
                        'from': 'country', 
                        'localField': 'address.country', 
                        'foreignField': '_id', 
                        'as': 'country'
                    }
                }, {
                    '$lookup': {
                        'from': 'states', 
                        'localField': 'address.state', 
                        'foreignField': '_id', 
                        'as': 'state'
                    }
                }, {
                    '$lookup': {
                        'from': 'city', 
                        'localField': 'address.city', 
                        'foreignField': '_id', 
                        'as': 'city'
                    }
                }, {
                    '$lookup': {
                        'from': 'category', 
                        'localField': 'category', 
                        'foreignField': '_id', 
                        'as': 'category'
                    }
                }, {
                    '$unwind': {
                        'path': '$category', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$unwind': {
                        'path': '$country', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$unwind': {
                        'path': '$state', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$unwind': {
                        'path': '$city', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$unwind': {
                        'path': '$tickets.tickets', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$addFields': {
                        'ticketsArray': {
                            '$objectToArray': '$tickets.tickets'
                        }
                    }
                }, {
                    '$addFields': {
                        'ticketPrices': {
                            '$filter': {
                                'input': '$ticketsArray', 
                                'as': 'ticket', 
                                'cond': {
                                    '$and': [
                                        {
                                            '$ne': [
                                                '$$ticket.k', '_id'
                                            ]
                                        }, {
                                            '$ne': [
                                                '$$ticket.k', 'spot_id'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }, {
                    '$unwind': {
                        'path': '$ticketPrices', 
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$addFields': {
                        'price': '$ticketPrices.v.price'
                    }
                }, {
                    '$project': {
                        '_id': 1, 
                        'name': 1, 
                        'image': 1, 
                        'country': '$country.name', 
                        'state': '$state.name', 
                        'city': '$city.name', 
                        'isActive': 1, 
                        'category': '$category.name', 
                        'rating': 1, 
                        'price': 1
                    }
                }, {
                    '$group': {
                        '_id': '$_id', 
                        'name': {
                            '$first': '$name'
                        }, 
                        'image': {
                            '$first': '$image'
                        }, 
                        'country': {
                            '$first': '$country'
                        }, 
                        'state': {
                            '$first': '$state'
                        }, 
                        'city': {
                            '$first': '$city'
                        }, 
                        'isActive': {
                            '$first': '$isActive'
                        }, 
                        'category': {
                            '$first': '$category'
                        }, 
                        'rating': {
                            '$first': '$rating'
                        }, 
                        'price': {
                            '$first': '$price'
                        }
                    }
                }
            ]
            
            cursor = db.spots.aggregate(pipeline)
            result = await cursor.to_list(length=None)
            for item in result:
                item['_id'] = str(item['_id'])
            self.set_status(200)
            self.write({"status": "success", "data": result})
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": str(e)})