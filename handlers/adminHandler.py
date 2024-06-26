import base64
import datetime
from bson import ObjectId
import tornado.web
import tornado.ioloop
from utils.jwt import decode
import utils.db
import json
from datetime import date
from handlers.auth import BaseHandler

def calculate_revenue(capacity, tickets_available, price):
        return (capacity - tickets_available) * price

class AdminHandler(BaseHandler):
    def initialize(self, db, fs):
        self.db = db
        self.fs = fs

    async def post(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
            name = data.get("name")
            city_name = data.get("city")
            state_name = data.get("state")
            country_name = data.get("country")
            category_name = data.get("category")
            is_active = data.get("isActive", True)
            image_base64 = data.get("image")
    
            if not image_base64:
                self.set_status(400)
                self.write({"status": False, "message": "Image is required."})
                return

            spot = await utils.db.findSpotByName(name)
    
            if spot is None:
                try:
                    image_data = base64.b64decode(image_base64)
                    image_filename = data.get("imageFilename", "uploaded_image")
                    image_document = {
                        "data": image_data,
                        "filename": image_filename
                    }
                    image_id = await utils.db.insertImage(image_document)

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
                    spot = {
                        "name": name,
                        "address": address,
                        "category": category_id,
                        "isActive": is_active,
                        "image_id": image_id,
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
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            usersGender=await utils.db.findMaleFemaleUsers()
            usersAge=await utils.db.findAgeWiseUsers()
            spots = await utils.db.findAllSpots()
            for spot in spots:
                # print(spot)
                spot['_id'] = str(spot['_id'])
                city= await utils.db.findCityById(spot['address']['city'])
                states=await utils.db.findStateById(spot['address']['state'])
                country=await utils.db.findCountryById(spot['address']['country'])
                category=await utils.db.findCategoryById(spot['category'])
                spot['address']['city'] = city['name']
                spot['address']['state'] = states['name']
                spot['address']['country'] = country['name']
                spot['category'] = category['name']
                # spot['category'] = str(spot['category'])
                spot_ticket_details = await utils.db.findSpotTicket(ObjectId(spot['_id']))
                # print(spot_ticket_details)
                revenue = 0
                for detail in spot_ticket_details:
                    for date, data in detail.items():
                        if date not in ["_id", "spot_id"]:
                            if isinstance(date, str):
                                date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

                                capacity = data.get("capacity", 0)
                                tickets_available = data.get("tickets_available", 0)
                                price = data.get("price", 0.0)
                                revenue = calculate_revenue(capacity, tickets_available, price)+revenue

                spot['image_id'] = str(spot['image_id'])
                spotImages= await utils.db.findSpotImages(ObjectId(spot['image_id']))
                if spotImages:
                    spotImages['_id'] = str(spotImages['_id'])
                    spotImages['data'] = base64.b64encode(spotImages['data']).decode('utf-8')
            # print(revenue)
            self.set_status(200)
            self.write(({"status": "success", "data": spots,"spot-image":spotImages,"revenue":revenue,"usersGender":usersGender,"usersAge":usersAge}))
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))

    async def put(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            spot_id = self.get_query_argument("spot_id")
            data = tornado.escape.json_decode(self.request.body)
            name = data.get("name")
            city_name = data.get("city")
            state_name = data.get("state")
            country_name = data.get("country")
            category_name = data.get("category")
            is_active = data.get("isActive", True)
            image_base64 = data.get("image")
            if not image_base64:
                self.set_status(400)
                self.write({"status": False, "message": "Image is required."})
                return
            spot= await utils.db.findSpotByName(name)
            if spot is not None:
                image_data = base64.b64decode(image_base64)
                image_filename = data.get("imageFilename", "uploaded_image")
                data = image_data
                filename = image_filename  
                
                if not ([spot['_id'], name, city_name, country_name, is_active, state_name, category_name]):
                    self.set_status(400)
                    self.write({"status": "error", "message": "Missing required parameters"})
                    return
            
                spot_id = ObjectId(spot_id)
                await utils.db.updateSpotAll(spot['_id'],spot['address']['country'],spot['address']['state'],spot['address']['city'],spot['category'])

                spotImages= await utils.db.findSpotImages(spot['image_id'])
                if spotImages:
                    await utils.db.updateImage(ObjectId(spotImages['_id']),data,filename)
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

            
                    await utils.db.updateSpot(ObjectId(spot['_id']),name,address,category_name,is_active)
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
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            spot_id = self.get_query_argument("spot_id")
            spot_id = ObjectId(spot_id)
            spot= await utils.db.findSpotById(spot_id)
            country_id=spot['address']['country']
            state_id=spot['address']['state']
            city_id=spot['address']['city']
            category_id = spot['category']
            if spot is not None:
                spotImages= await utils.db.findSpotImages(spot['image_id'])
                if spotImages:
                    await utils.db.deleteSpot(ObjectId(spot_id),ObjectId(spotImages['_id']),country_id,state_id,city_id,category_id)

                    self.set_status(200)
                    self.write({"status": True, "message": "Spot Deleted successfully"})
            else:
                self.set_status(400)
                self.write({"status": False, "message": "Spot Not Found"})
            
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": f"An error occurred: {e}"})
