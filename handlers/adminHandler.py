import base64
import datetime
from bson import ObjectId
import motor
import tornado.web
import tornado.ioloop
from utils.jwt import decode
import utils.db
import json
from datetime import date
from handlers.auth import BaseHandler

myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = myclient["Tourist_Spot_Booking_System"]

def calculate_revenue(capacity, tickets_available, price):
        return (capacity - tickets_available) * price

class AdminHandler(BaseHandler):
    def initialize(self, db, fs):
        self.db = db
        self.fs = fs

    async def post(self):
        # if not BaseHandler.get_current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return

        try:
            data = tornado.escape.json_decode(self.request.body)
            name = data.get("name")
            city_name = data.get("city")
            state_name = data.get("state")
            country_name = data.get("country")
            category_name = data.get("category")
            is_active = data.get("isActive", True)
            image_url = data.get("image")
            opening_time = data.get("opening_time")
            closing_time = data.get("closing_time")
    
            if not image_url:
                self.set_status(400)
                self.write({"status": False, "message": "Image is required."})
                return

            spot = await utils.db.findSpotByName(name)
    
            if spot is None:
                try:
                    country = await utils.db.findCountry(country_name)
                    if country is None:
                        country_id = ObjectId()
                        countryDetails = {
                            "_id": country_id,
                            "name": country_name,
                        }
                        country_id=await utils.db.addCountry(countryDetails)
                    else:
                        country_id = country['_id']

                    state = await utils.db.findState(state_name)
                    if state is None:
                        country_id = country_id or ObjectId() 
                        state_id = ObjectId()
                        stateDetails = {
                            "_id": state_id,
                            "country_id": country_id,
                            "name": state_name,
                        }
                        state_id = await utils.db.addState(stateDetails)
                    else:
                        state_id = state['_id']

                    city = await utils.db.findCity(city_name)
                    if city is None:
                        country_id = country_id  
                        state_id = state_id 
                        city_id = ObjectId()
                        cityDetails = {
                            "_id": city_id,
                            "country_id": country_id,
                            "state_id": state_id,
                            "name": city_name,
                        }
                        city_id=await utils.db.addCity(cityDetails)
                    else:
                        city_id = city['_id']

                    category = await utils.db.findCategory(category_name)
                    if category is None:
                        category_id = ObjectId()
                        categoryDetails = {
                            "_id": category_id,
                            "name": category_name,
                        }
                        await utils.db.addCategory(categoryDetails)
                    else:
                        category_id = category['_id']
                        
                    address = {
                        "city": city_id,
                        "state": state_id,
                        "country": country_id,
                    }
                    spot = {
                        "name": name,
                        "address": address,
                        "category": category_id,
                        "isActive": is_active,
                        "image": image_url,
                        "opening_time":opening_time,
                        "closing_time":closing_time,
                        "isOpened":True
                    }
                    result=await utils.db.addSpot(spot)
                    spot_id= result.inserted_id
            
                    await utils.db.updateStateWithSpot(state_id, spot_id)

                    await utils.db.updateCityWithSpot(city_id, spot_id)

                    await utils.db.updateCountryWithSpot(country_id, spot_id)

                    await utils.db.updateCategoryWithSpot(category_id, spot_id,city_id,state_id,country_id)

                    self.write({"status": True, "message": "Spot added successfully","spot_id":str(result.inserted_id)})
        
                except Exception as e:
                    self.set_status(500)
                    self.write({"status": False, "message": f"An error occurred: {str(e)}"})
    
            else:
                self.set_status(400)
                self.write({"status": False, "message": "Spot Already Exists"})

        except ValueError as ve:
            self.set_status(400)
            self.write({"status": False, "message": f"Invalid data: {str(ve)}"})
        except Exception as e:
            self.set_status(500)
            self.write({"status": False, "message": f"An error occurred: {str(e)}"})

    async def get(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            usersGender=await utils.db.findMaleFemaleUsers()
            usersAge=await utils.db.findAgeWiseUsers()
            pipeline=[
                {
                    '$lookup': {
                        'from': 'spot_time_slot', 
                        'localField': '_id', 
                        'foreignField': 'spot_id', 
                        'as': 'ticketdetails'
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
                    '$lookup': {
                        'from': 'rating', 
                        'localField': '_id', 
                        'foreignField': 'spot_id', 
                        'as': 'ratings'
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
                        'path': '$ticketdetails', 
                        'preserveNullAndEmptyArrays': True
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
                        'isActive': {
                            '$first': '$isActive'
                        }, 
                        'image_url': {
                            '$first': '$image'
                        }, 
                        'country_name': {
                            '$first': '$country.name'
                        }, 
                        'state_name': {
                            '$first': '$state.name'
                        }, 
                        'city_name': {
                            '$first': '$city.name'
                        }, 
                        'category_name': {
                            '$first': '$category.name'
                        }, 
                        'rating': {
                            '$avg': '$ratings.rating'
                        }, 
                        'ticket_price': {
                            '$first': '$ticketdetails.details.price'
                        }
                    }
                }, {
                    '$project': {
                        'name': 1, 
                        'isActive': 1, 
                        'image_url': 1, 
                        'country_name': 1, 
                        'state_name': 1, 
                        'city_name': 1, 
                        'category_name': 1, 
                        'rating': 1, 
                        'ticket_price': 1
                    }
                }
            ]

            cursor = db.spots.aggregate(pipeline)
            result = await cursor.to_list(length=None)
            for item in result:
                item['_id'] = str(item['_id'])
            self.set_status(200)
            self.write(({"status": "success", "data": result,"usersGender":usersGender,"usersAge":usersAge}))
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))

    async def put(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            spot_id = self.get_query_argument("spot_id")
            data = tornado.escape.json_decode(self.request.body)
            name = data.get("name")
            city_name = data.get("city")
            state_name = data.get("state")
            country_name = data.get("country")
            category_name = data.get("category")
            is_active = data.get("isActive", True)
            image_url = data.get("image")
            opening_time = data.get("opening_time")
            closing_time = data.get("closing_time")
    
    
            if not image_url:
                self.set_status(400)
                self.write({"status": False, "message": "Image is required."})
                return
            spot= await utils.db.findSpotByName(name)
            if spot is not None:
                if not ([spot['_id'], name, city_name, country_name, is_active, state_name, category_name]):
                    self.set_status(400)
                    self.write({"status": "error", "message": "Missing required parameters"})
                    return
            
                spot_id = ObjectId(spot_id)
                await utils.db.updateSpotAll(spot['_id'],spot['address']['country'],spot['address']['state'],spot['address']['city'],spot['category'])
                country = await utils.db.findCountry(country_name)
                if country is None:
                    country_id = ObjectId()
                    countryDetails = {
                        "_id": country_id,
                        "name": country_name,
                    }
                    country_id=await utils.db.addCountry(countryDetails)
                else:
                    country_id = country['_id']

                state = await utils.db.findState(state_name)
                if state is None:
                    country_id = country_id or ObjectId()  # Ensure we have a valid country_id
                    state_id = ObjectId()
                    stateDetails = {
                        "_id": state_id,
                        "country_id": country_id,
                        "name": state_name,
                    }
                    state_id = await utils.db.addState(stateDetails)
                else:
                    state_id = state['_id']

                city = await utils.db.findCity(city_name)
                if city is None:
                    country_id = country_id   # Ensure we have a valid country_id
                    state_id = state_id  # Ensure we have a valid state_id
                    city_id = ObjectId()
                    cityDetails = {
                        "_id": city_id,
                        "country_id": country_id,
                        "state_id": state_id,
                        "name": city_name,
                    }
                    city_id=await utils.db.addCity(cityDetails)
                else:
                    city_id = city['_id']

                category = await utils.db.findCategory(category_name)
                if category is None:
                    category_id = ObjectId()
                    categoryDetails = {
                        "_id": category_id,
                        "name": category_name,
                    }
                    await utils.db.addCategory(categoryDetails)
                else:
                    category_id = category['_id']
                    
                address = {
                    "city": city_id,
                    "state": state_id,
                    "country": country_id,
                }

        
                await utils.db.updateSpot(ObjectId(spot['_id']),name,address,category_name,is_active,image_url,opening_time,closing_time)
                await utils.db.updateStateWithSpot(state_id, spot_id)

                await utils.db.updateCityWithSpot(city_id, spot_id)

                await utils.db.updateCountryWithSpot(country_id, spot_id)

                await utils.db.updateCategoryWithSpot(category_id, spot_id,city_id,state_id,country_id)

                self.write({"status": True, "message": "Spot updated successfully"})
            else:
                self.set_status(400)
                self.write({"status": False, "message": "Spot Not Found"})
            
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": f"An error occurred: {e}"})

    async def delete(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            spot_id = self.get_query_argument("spot_id")
            spot_id = ObjectId(spot_id)
            spot= await utils.db.findSpotById(spot_id)
            country_id=spot['address']['country']
            state_id=spot['address']['state']
            city_id=spot['address']['city']
            category_id = spot['category']
            if spot is not None:
                await utils.db.deleteSpot(ObjectId(spot_id),country_id,state_id,city_id,category_id)

                self.set_status(200)
                self.write({"status": True, "message": "Spot Deleted successfully"})
            else:
                self.set_status(400)
                self.write({"status": False, "message": "Spot Not Found"})
            
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": f"An error occurred: {e}"})
