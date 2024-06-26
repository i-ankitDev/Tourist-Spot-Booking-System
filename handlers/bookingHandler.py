import base64
from io import BytesIO
import json
from bson import ObjectId
import tornado.web
import tornado.ioloop
from utils.jwt import decode
import utils.db
from utils.validation import is_valid_mobile_number
import qrcode
import datetime
from handlers.auth import BaseHandler
    
class BookingHandler(BaseHandler):

    def initialize(self, db):
        self.db = db

    async def post(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            spot_id = self.get_query_argument("spot_id")
            spot_id = ObjectId(spot_id)
            spot= await utils.db.findSpotById(spot_id)
            user=self.get_current_user()
            user=await utils.db.findUserById(ObjectId(user['_id']))
            if spot is not None and spot['isActive'] == True:
                current_date = datetime.date.today().isoformat()
                ticketsAvailable = await utils.db.findTicketAvailable(spot['_id'], current_date)
            if ticketsAvailable is not None:
                try:
                    tickets_available = int(ticketsAvailable)  # Convert to int
                    if tickets_available > 0:
                        data = tornado.escape.json_decode(self.request.body)
                        name = data.get("name")
                        mobileNumber = data.get("mobileNumber")
                        address = data.get("address")
                        age = int(data.get("age"))
                        number_of_tickets = int(data.get("number_of_tickets"))
                        if is_valid_mobile_number(mobileNumber):
                            now = datetime.datetime.now()
                            # currentDateAndTime = now.strftime("%d-%m-%y %H:%M:%S")
                            mydict = {
                            "spot_id": ObjectId(spot['_id']),
                            "user_id": ObjectId(user['_id']),
                            "name": name,
                            "age": age,
                            "mobileNumber": mobileNumber,
                            "attendence": False,
                            "address": address,
                            "isValid": True,
                            "number_of_tickets":number_of_tickets,
                            "tickedBookedOn": now
                            }
                            new_tickets_available = tickets_available - number_of_tickets
                            await utils.db.bookTicket(mydict, ObjectId(spot['_id']), current_date,new_tickets_available)  # Decrement available tickets
                            self.write({"status": True, "message": "Ticket Booked successfully."})
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
                self.write({"status": False, "message": "No ticket details found for today."})
        except Exception as e:
            self.set_status(500)
            self.write({"status": "error", "message": f"An error occurred: {e}"})

    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
        try:
            ticket_idStr = self.get_query_argument("ticket_id")
            data = tornado.escape.json_decode(self.request.body)
            attendence_input=int(data.get("attendence"))
            ticket_id = ObjectId(ticket_idStr)
            ticket = await utils.db.findTicketDetails(ticket_id)
            spot=await utils.db.findSpotById(ticket['spot_id'])
            spot['_id'] = str(spot['_id'])
            spotTicket=await utils.db.findSpotTicketById(ObjectId(spot['_id']))
            # print(spotTicket)
            current_date = datetime.date.today().isoformat()
            total_attendence = spotTicket.get(current_date, {}).get('attendence', None)
            attendence=total_attendence-attendence_input
            await utils.db.updateAttendence(ObjectId(spot['_id']),current_date,attendence)
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
            self.write(({"status": "success", "ticket_details": ticket_details,"qr_code":img_base64}))
        except Exception as e:
            self.set_status(500)
            self.write(({"status": "error", "message": str(e)}))

    async def delete(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        
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