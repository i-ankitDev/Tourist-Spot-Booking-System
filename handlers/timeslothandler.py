import datetime
import motor
import tornado
from handlers.auth import BaseHandler

myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
db = myclient["Tourist_Spot_Booking_System"]
    
class TimeSlotHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        try:
            data = tornado.escape.json_decode(self.request.body)
            spot_name = data.get('spot_name', "")
            date_str = data.get("date", '')
            current_datetime = datetime.datetime.now()
            current_time_str = current_datetime.strftime('%H:%M:%S')
            print(current_time_str)
            pipeline = [
                {
                    '$lookup': {
                        'from': 'spot_time_slot',
                        'localField': '_id',
                        'foreignField': 'date_id',
                        'as': 'daywise_timeslot_details'
                    }
                },
                {
                    '$lookup': {
                        'from': 'spots',
                        'localField': 'spot_id',
                        'foreignField': '_id',
                        'as': 'spot'
                    }
                },
                {
                    '$unwind': '$spot'
                },
                {
                    '$unwind': '$daywise_timeslot_details'
                },
                {
                    '$match': {
                        '$and': [
                            {
                                'spot.name': {
                                    '$regex': spot_name,
                                    '$options': 'i'
                                }
                            },
                            {
                                'daywise_timeslot_details.timeslot.end_time': {
                                    '$gte': current_time_str
                                }
                            }
                        ]
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'name': '$spot.name',
                        'date': 1,
                        'timeslot': '$daywise_timeslot_details.timeslot'
                    }
                }
            ]
            if date_str:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                pipeline[4]['$match']['$and'].append({
                    'date': {
                        '$regex': date.isoformat(),
                        '$options': 'i'
                    }
                })
            cursor = db.spot_daywise_details.aggregate(pipeline)
            result = await cursor.to_list(length=None)
            self.set_status(200)
            self.write({"status": True, "data": result})
            

        except Exception as e:
            self.set_status(500)
            self.write(({"status": False, "message": str(e)}))
