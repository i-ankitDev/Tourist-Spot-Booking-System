import tornado
from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler
    
class CityHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        try:
            cities = await utils.db.findAllCities()
            cityNames = []
            if cities is not None:
                for city in cities:
                    cityNames.append(city['name'])
                
                self.set_status(200)
                self.write(({"status": True, "citynames": cityNames}))
            else:
                self.set_status(400)
                self.write(({"status": False, "message": "no city founds"}))

        except Exception as e : 
            self.set_status(500)
            self.write(({"status": False, "message": str(e)}))
