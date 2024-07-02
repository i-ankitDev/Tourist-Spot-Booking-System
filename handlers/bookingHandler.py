import base64
from io import BytesIO
import json
from bson import ObjectId
import motor
import tornado.web
import tornado.ioloop
from utils.jwt import decode
import utils.db
from utils.validation import is_valid_mobile_number
import qrcode
import datetime
from handlers.auth import BaseHandler


myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = myclient["Tourist_Spot_Booking_System"]
    
class BookingHandler(BaseHandler):

    def initialize(self, db):
        self.db = db

    async def post(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            spot_id = self.get_query_argument("spot_id")
            spot_id = ObjectId(spot_id)
            spot= await utils.db.findSpotById(spot_id)
            # user=self.get_current_user()
            # user=await utils.db.findUserById(ObjectId(user['_id']))
            user = self.get_query_argument("user_id")
            user=await utils.db.findUserById(ObjectId(user))
            if spot is not None and spot['isActive'] == True:
                data = tornado.escape.json_decode(self.request.body)
                date = data.get("date")
                start_time_str = data.get('start_time')
                end_time_str = data.get('end_time')
                date = datetime.datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
                start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time()
                timeslot_str = {
                    "start_time":start_time.isoformat(),
                    "end_time":end_time.isoformat()
                }
                pipeline=[
                    {
                        '$lookup': {
                            'from': 'spot_time_slot', 
                            'localField': '_id', 
                            'foreignField': 'date_id', 
                            'as': 'daywise_timeslot_details'
                        }
                    }, {
                        '$unwind': '$daywise_timeslot_details'
                    }, {
                        '$match': {
                            'date': date
                        }
                    }, {
                        '$match': {
                            'daywise_timeslot_details.timeslot': timeslot_str
                        }
                    }
                ]
            result = await db.spot_daywise_details.aggregate(pipeline).to_list(length=None)
            if result is not None:
                pipeline=[
                    {
                        '$lookup': {
                            'from': 'spot_daywise_details',
                            'localField': 'date_id',
                            'foreignField': '_id',
                            'as': 'date_details'
                        }
                    },
                    {
                        '$unwind': '$date_details'
                    },
                    {
                        '$match': {
                            'spot_id': ObjectId(spot["_id"]),
                            'timeslot': timeslot_str,
                            'date_details.date': date
                        }
                    },
                    {
                        '$project':{
                            'ticketsAvailable':'$details.tickets_available'
                        }
                    }
                ]
                ticketsAvailable = await db.spot_time_slot.aggregate(pipeline).to_list(length=None)
            if ticketsAvailable is not None:
                try:
                    tickets_available = int(ticketsAvailable[0]['ticketsAvailable']) 
                    if tickets_available > 0:
                        name = data.get("name")
                        mobileNumber = data.get("mobileNumber")
                        address = data.get("address")
                        age = int(data.get("age"))
                        number_of_tickets = int(data.get("number_of_tickets"))
                       
                        if is_valid_mobile_number(mobileNumber):
                            now = datetime.datetime.now()
                            mydict = {
                            "spot_id": ObjectId(spot['_id']),
                            "user_id": ObjectId(user['_id']),
                            "name": name,
                            "age": age,
                            "mobileNumber": mobileNumber,
                            "attendence": False,
                            "time-slot":timeslot_str,
                            "date":date,
                            "address": address,
                            "isValid": True,
                            "number_of_tickets":number_of_tickets,
                            "tickedBookedOn": now,
                            }
                            new_tickets_available = tickets_available - number_of_tickets 
                            result= await db.ticketBooking.insert_one(mydict)
                            id = result.inserted_id 
                            pipeline = [
                            {
                                '$lookup': {
                                    'from': 'spot_daywise_details',
                                    'localField': 'date_id',
                                    'foreignField': '_id',
                                    'as': 'date_details'
                                }
                            },
                            {
                                '$unwind': '$date_details'
                            },
                            {
                                '$match': {
                                    'spot_id': ObjectId(spot["_id"]),
                                    'timeslot': timeslot_str,
                                    'date_details.date': date
                                }
                            },
                            {
                                '$project': {
                                    'spot_id': 1,
                                    'timeslot': 1,
                                    'details': 1,
                                    'ticketBookings':1
                                    
                                }
                            },
                           {
                                '$set': {
                                    'details.tickets_available': new_tickets_available
                                }
                            },
                            {
                                '$addFields': {
                                    'ticketBookings': {
                                        '$concatArrays': [
                                            { '$ifNull': ['$ticketBookings', []] }, 
                                            [ObjectId(id)]
                                        ]
                                    }
                                }
                            },
                            {
                                '$merge': {
                                    'into': 'spot_time_slot',
                                    'whenMatched': 'merge',
                                    'whenNotMatched': 'fail'
                                }
                            }
                        ]
                        # Execute the aggregation pipeline
                            result = await db.spot_time_slot.aggregate(pipeline).to_list(length=None)

                            self.write({"status": True, "message": "Ticket Booked successfully.","ticket_id":str(id)})
                        else:
                            self.set_status(400)
                            self.write({"status": False, "message": "Invalid Mobile Number"})
                    else:
                        self.set_status(400)
                        self.write({"status": False, "message": "Slot not Available"})
                except Exception as e:
                    self.set_status(500)
                    self.write({"status": False, "message": f"An error occurred: {e}"})
            else:
                self.set_status(400)
                self.write({"status": False, "message": "No ticket details found."})
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": f"An error occurred: {e}"})

    async def get(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            ticket_idStr = self.get_query_argument("ticket_id")
            data = tornado.escape.json_decode(self.request.body)
            attendence_input=int(data.get("attendence"))
            ticket_id = ObjectId(ticket_idStr)
            ticket = await utils.db.findTicketDetails(ticket_id)
            spot=await utils.db.findSpotById(ticket['spot_id'])
            spot['_id'] = str(spot['_id'])
            attedence = ticket['attendence']
            isValid = ticket['isValid']
            if attedence is False and isValid is True:
                pipeline1 = [
                    {
                        '$match': {
                            'ticketBookings': {
                                '$in': [
                                    ObjectId('66812444ccdac4aaf156266e')
                                ]
                            }
                        }
                    }, {
                        '$project': {
                            'attendence': '$details.attendence'
                        }
                    }
                ]
                totalattendence = await db.spot_time_slot.aggregate(pipeline1).to_list(length=None)
                totalattendence = (totalattendence[0]['attendence'])
                db.ticketBooking.update_one({"_id":ObjectId(ticket['_id'])},
                                            {'$set':{'attendence':True,'isValid':False}})
                print(totalattendence - attendence_input)
                pipeline2 = [
                    {
                        "$match": {
                            "ticketBookings": { "$in": [ObjectId(ticket['_id'])] }
                        }
                    },
                    {
                        "$addFields": {
                            "details.attendence": totalattendence - attendence_input
                        }
                    },
                    {
                        "$merge": {
                            "into": "spot_time_slot",
                            "whenMatched": "merge",
                            "whenNotMatched": "fail"
                        }
                    }
                ]
                await db.spot_time_slot.aggregate(pipeline2).to_list(length=None)
                ticket_details = {
                    "id" : str(ticket_id),
                    "Customer_Name" : ticket['name'],
                    "Spot_Name" : spot['name'],
                    "Contact_no" : ticket['mobileNumber']
                }
                ticket_details_json = json.dumps(ticket_details)

                # Generate QR code
                qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
                )
                qr.add_data(ticket_details_json)
                qr.make(fit=True)

                img = qr.make_image(fill='black', back_color='white')

                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_str = buffer.getvalue()

                img_base64 = base64.b64encode(img_str).decode('utf-8')

                img.save("booking_qrcode.png")

                self.set_status(200)
                self.write(({"status": True, "ticket_details": ticket_details,"qr_code":img_base64}))
            else:
                self.set_status(500)
                self.write(({"status": False, "message": "Ticket expired"}))
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))

    async def delete(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        
        try:
            ticket_id = self.get_query_argument("ticket_id")
            ticket_id = ObjectId(ticket_id)
            ticket = await utils.db.findTicketDetails(ticket_id)
            spot_id=(ticket['spot_id'])
            spot= await utils.db.findSpotById(ObjectId(spot_id))
            slotAvailable=(spot['slotAvailable'])
            if ticket is not None:
                await utils.db.cancelTicket(ObjectId(ticket['_id']),spot_id,slotAvailable)
                self.set_status(200)
                self.write({"status": True, "message": "Ticket Deleted Successfully"})
            else:
                self.set_status(400)
                self.write({"status": False, "message": "Ticket not found"})
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))