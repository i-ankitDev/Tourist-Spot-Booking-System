import tornado
from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler
    
class CountryHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        try:
            countries = await utils.db.findAllCountries()
            countryNames = []
            if countries is not None:
                for country in countries:
                    countryNames.append(country['name'])
                
                self.set_status(200)
                self.write(({"status": True, "countrynames": countryNames}))
            else:
                self.set_status(400)
                self.write(({"status": False, "message": "no country founds"}))

        except Exception as e : 
            self.set_status(500)
            self.write(({"status": False, "message": str(e)}))
