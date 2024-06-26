
import datetime
import motor
import tornado.web
import tornado.ioloop

from utils.jwt import decode
from handlers.auth import BaseHandler

myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = myclient["Tourist_Spot_Booking_System"]
    
class FilterHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        try:
            start_date_str = self.get_query_argument("start_date", "")
            end_date_str = self.get_query_argument("end_date", "")
            country_name = self.get_query_argument("country_name", "")
            state_name = self.get_query_argument("state_name", "")
            city_name = self.get_query_argument("city_name", "")
            category_name = self.get_query_argument("category_name", "")
            spot_name = self.get_query_argument("spot_name", "")
            if start_date_str and end_date_str : 
                start_date = datetime.datetime.strptime(start_date_str, "%d-%m-%Y").date()
                end_date = datetime.datetime.strptime(end_date_str, "%d-%m-%Y").date() 
                pipeline=[
                            {
                                '$lookup': {
                                    'from': 'spots', 
                                    'localField': 'spot_id', 
                                    'foreignField': '_id', 
                                    'as': 'spot_details'
                                }
                            }, {
                                '$unwind': '$spot_details'
                            }, {
                                '$project': {
                                    'spot_details': 1, 
                                    'dynamic_fields': {
                                        '$objectToArray': '$$ROOT'
                                    }
                                }
                            }, {
                                '$unwind': '$dynamic_fields'
                            }, {
                                '$match': {
                                    '$and': [
                                        {
                                            'dynamic_fields.k': {
                                                '$gte': str(start_date), 
                                                '$lte': str(end_date)
                                            }
                                        }, {
                                            'spot_details.name': {
                                                '$regex': spot_name, 
                                                '$options': 'ism'
                                            }
                                        }
                                ]
                                    }
                                }, {
                                    '$project': {
                                        '_id': 0, 
                                        'spot name': '$spot_details.name', 
                                        'date': '$dynamic_fields.k', 
                                        'capacity': '$dynamic_fields.v.capacity', 
                                        'tickets_available': '$dynamic_fields.v.tickets_available', 
                                        'price': '$dynamic_fields.v.price', 
                                        'attendence': '$dynamic_fields.v.attendence'
                                    }
                                }
                        ]
                cursor = db.spotTicket.aggregate(pipeline)
                result = await cursor.to_list(length=None)
                self.set_status(200)
                self.write({"status": "success", "data": result})
            else:
                pipeline =  [
                    {
                        '$lookup': {
                            'from': 'category', 
                            'localField': 'category', 
                            'foreignField': '_id', 
                            'as': 'category'
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
                        '$unwind': '$category'
                    }, {
                        '$unwind': '$country'
                    }, {
                        '$unwind': '$state'
                    }, {
                        '$unwind': '$city'
                    }, {
                        '$match': {
                            '$and': [
                                {
                                    'name': {
                                        '$regex': spot_name, 
                                        '$options': 'ism'
                                    }
                                }, {
                                    'category.name': {
                                        '$regex': category_name, 
                                        '$options': 'ism'
                                    }
                                }, {
                                    'country.name': {
                                        '$regex': country_name, 
                                        '$options': 'ism'
                                    }
                                }, {
                                    'state.name': {
                                        '$regex': state_name, 
                                        '$options': 'ism'
                                    }
                                }, {
                                    'city.name': {
                                        '$regex': city_name, 
                                        '$options': 'ism'
                                    }
                                }
                            ]
                        }
                    }, {
                        '$project': {
                            '_id': 0, 
                            'name': 1, 
                            'category': '$category.name', 
                            'country': '$country.name', 
                            'state': '$state.name', 
                            'city': '$city.name', 
                            'isActive': 1
                        }
                    }
                ]
                cursor = db.spots.aggregate(pipeline)
                result = await cursor.to_list(length=None)
                self.set_status(200)
                self.write({"status": "success", "data": result})

        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": f"An error occurred: {e}"})
 