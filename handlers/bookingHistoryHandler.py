from bson import ObjectId
import tornado.web
import tornado.ioloop

from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler

class BookingHistoryHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        user=self.get_current_user()
        user=await utils.db.findUserById(ObjectId(user['_id']))
        if user is not None:
            result=await utils.db.findTicketHistory(ObjectId(user['_id']))
            if result is not None:
                ticketDetailsUser = []
                for ticket_detail in result:
                    spot=await utils.db.findSpotById(ticket_detail['spot_id'])
                    spot['_id'] = str(spot['_id'])
                    ticket_detail['user_id'] = str(ticket_detail['user_id'])
                    
                    ticket_details = {
                    "id" : str(ticket_detail['_id']),
                    "Customer_Name" : spot['name'],
                    "Spot_Name" : ticket_detail['name'],
                    # "Spot_Location":spot['location'],
                    "Contact_no" : ticket_detail['mobileNumber']
                }
                    ticketDetailsUser.append(ticket_details)
                self.set_status(200)
                self.write(({"status": "success", "ticket_details": ticketDetailsUser}))
            else:
                self.set_status(400)
                self.write({"status": False, "message": "No history found"})
        else:
            self.set_status(400)
            self.write({"status": False, "message": "User not found"})