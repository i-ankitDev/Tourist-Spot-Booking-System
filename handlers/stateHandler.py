import tornado
from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler
    
class StateHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        # if not self.current_user:
        #     self.set_status(401)
        #     self.write({"status": False, "message": "Unauthorized"})
        #     return
        try:
            states = await utils.db.findAllStates()
            stateNames = []
            if states is not None:
                for state in states:
                    stateNames.append(state['name'])
                
                self.set_status(200)
                self.write(({"status": True, "statenames": stateNames}))
            else:
                self.set_status(400)
                self.write(({"status": False, "message": "no state founds"}))

        except Exception as e : 
            self.set_status(500)
            self.write(({"status": False, "message": str(e)}))
