import datetime
from bson import ObjectId
import motor
import tornado.web
import tornado.ioloop
from datetime import date
from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler

myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = myclient["Tourist_Spot_Booking_System"]

def calculate_revenue(capacity, tickets_available, price):
        return (capacity - tickets_available) * price

def generate_day_wise_details(spot_ticket_details):
        day_wise_details = {}

        for detail in spot_ticket_details:
            for date, data in detail.items():
                if date not in ["_id", "spot_id"]:
                    if isinstance(date, str):
                        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

                    capacity = data.get("capacity", 0)
                    tickets_available = data.get("tickets_available", 0)
                    price = data.get("price", 0.0)
                    revenue = calculate_revenue(capacity, tickets_available, price)

                    day_wise_details[str(date)] = {
                        "capacity": capacity,
                        "tickets_available": tickets_available,
                        "price": price,
                        "attendence": data.get("attendence", 0),
                        "revenue": revenue
                    }

        return day_wise_details

class AdminSpotHandler(BaseHandler):
    def initialize(self, db):
        self.db = db
    
    async def post(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        try:
            spot_id = self.get_query_argument("spot_id")
            data = tornado.escape.json_decode(self.request.body)
            capacity = int(data.get("capacity"))
            ticketPrice = float(data.get("ticketPrice"))
            tickets_available = capacity
            attendence = capacity
            current_date=date.today().isoformat()
            # current_date=(datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
            await utils.db.spotTicket(ObjectId(spot_id),current_date,capacity,tickets_available,ticketPrice,attendence)
            self.write({"status": True, "message": "Ticket details added successfully"})
        except Exception as e:
            self.set_status(500)
            self.write({"status": False, "message": f"An error occurred: {str(e)}"})


    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            start_date_str = self.get_query_argument("start_date", None)
            end_date_str = self.get_query_argument("end_date", None)
            state_name = self.get_query_argument("state_name", None)
            city_name = self.get_query_argument("city_name", None)
            category_name = self.get_query_argument("category_name", None)
            spot_name = self.get_query_argument("spot_name", None)
            
            query = {}
            projection = {'_id': 1, 'date': 1,'capacity':1}
            state_city_category_mapping = {}
            if start_date_str and end_date_str:
                try:
                    start_date = datetime.datetime.strptime(start_date_str, "%d-%m-%Y") if start_date_str else None
                    end_date = datetime.datetime.strptime(end_date_str, "%d-%m-%Y") if end_date_str else None
                    states = await utils.db.findAllStates()

                    for state in states:
                        state_name_d = state['name']
                        state_data = {}

                        cities = await utils.db.findCityByStateId(state['_id'])

                        for city in cities:
                            city_name_d = city['name']
                            city_data = {}

                            categories = await utils.db.findCategoriesByCity(city['_id'])

                            for category in categories:
                                category_name_d = category['name']
                                category_data = []
                                # print(category)
                                spots = await utils.db.findSpotsByCategories(category['_id'])  
                                # print(spots)
                                for spot in spots:
                                    # print(spot)
                                    spot_name_d = spot['name']
                                    spot_data = {}

                                    spot_ticket_details = await utils.db.findSpotTicket(spot['_id'])
                                    # print(spot_ticket_details)
                                    # Filter spot_ticket_details based on the date range
                                    filtered_ticket_details = []
                                    for detail in spot_ticket_details:
                                        for key in detail.keys():
                                            if key != '_id' and key != 'spot_id':
                                                try:
                                                    ticket_date = datetime.datetime.strptime(key, "%Y-%m-%d")
                                                    if (not start_date or ticket_date >= start_date) and (not end_date or ticket_date <= end_date):
                                                        filtered_ticket_details.append({key: detail[key]})
                                                except ValueError:
                                                    continue

                                    day_wise_details = generate_day_wise_details(filtered_ticket_details)

                                    spot_data['spot_name'] = spot_name_d
                                    spot_data['day_wise_details'] = day_wise_details
                                    category_data.append(spot_data)

                                city_data[category_name_d] = category_data

                            state_data[city_name_d] = city_data

                        state_city_category_mapping[state_name_d] = state_data

                    self.set_status(200)
                    self.write({"status": True, "data": state_city_category_mapping})
                except Exception as e:
                    self.set_status(400)
                    self.write({"status": False, "message": f"An error occurred: {str(e)}"})
                    
            
            
            if state_name:
                state_doc = await db.states.find_one({'name': {'$regex': state_name, '$options': 'i'}})
                if state_doc:
                    state_data = {}
                    cities = await db.city.find({'state_id': state_doc['_id']}).to_list(length=None)
                    for city in cities:
                        city_data = {}
                        categories = await db.category.find({'city_id': city['_id']}).to_list(length=None)
                        for category in categories:
                            category_data = []
                            spots = await db.spots.find({'category': category['_id']}).to_list(length=None)
                            for spot in spots:
                                spot_data = {}
                                spot_ticket_details = await db.spotTicket.find({'spot_id': spot['_id']}).to_list(length=None)
                                day_wise_details = generate_day_wise_details(spot_ticket_details)
                                spot_data['spot_name'] = spot['name']
                                spot_data['day_wise_details'] = day_wise_details
                                category_data.append(spot_data)
                            city_data[category['name']] = category_data
                        state_data[city['name']] = city_data

                    self.write({
                        'status': 'success',
                        state_doc['name']: state_data
                    })
                    return

            if city_name:
                city_doc = await db.city.find_one({'name': {'$regex': city_name, '$options': 'i'}})
                if city_doc:
                    city_data = {}
                    categories = await db.category.find({'city_id': city_doc['_id']}).to_list(length=None)
                    for category in categories:
                        category_data = []
                        spots = await db.spots.find({'category': category['_id']}).to_list(length=None)
                        for spot in spots:
                            spot_data = {}
                            spot_ticket_details = await db.spotTicket.find({'spot_id': spot['_id']}).to_list(length=None)
                            day_wise_details = generate_day_wise_details(spot_ticket_details)
                            spot_data['spot_name'] = spot['name']
                            spot_data['day_wise_details'] = day_wise_details
                            category_data.append(spot_data)
                        city_data[category['name']] = category_data

                    self.write({
                        'status': 'success',
                        city_doc['name']: city_data
                    })
                    return

            if category_name:
                category_doc = await db.category.find_one({'name': {'$regex': category_name, '$options': 'i'}})
                if category_doc:
                    query['category'] = category_doc['name']
                    if not spot_name:
                        spots = await db.spots.find({'category': category_doc['_id']}).to_list(length=None)
                        category_data = []
                        for spot in spots:
                            spot_data = {}
                            spot_ticket_details = await db.spotTicket.find({'spot_id': spot['_id']}).to_list(length=None)
                            day_wise_details = generate_day_wise_details(spot_ticket_details)
                            spot_data['spot_name'] = spot['name']
                            spot_data['day_wise_details'] = day_wise_details
                            category_data.append(spot_data)
                        self.write({
                            'status': 'success',
                            category_doc['name']: category_data
                        })
                        return

            if spot_name:
                spot_details = {}
                spot= await utils.db.findSpot(spot_name)
                if spot is not None:
                # print(state['name'])
                    if spot:
                        
                        spot_id = spot['_id']
                        spot_details[spot_name] = []
                        spot_ticket_details = await utils.db.findSpotTicket(spot_id)
                        day_wise_details=generate_day_wise_details(spot_ticket_details)
                                
                        spot_details[spot_name].append({
                            "day_wise_details": day_wise_details
                        })
                    self.set_status(200)
                    self.write({"status": True, "data": spot_details})  
                    # print(spot_details)
                else:
                    self.set_status(400)
                    self.write({"status": False, "message": "spot not found"}) 
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})