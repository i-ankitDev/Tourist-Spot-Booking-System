import tornado
from utils.jwt import decode
import utils.db
from handlers.auth import BaseHandler
    
class CategoriesHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def get(self):
        if not self.current_user:
            self.set_status(401)
            self.write({"status": False, "message": "Unauthorized"})
            return
        try:
            categories = await utils.db.findAllCategories()
            categoriesNames = []
            if categories is not None:
                for category in categories:
                    categoriesNames.append(category['name'])
                
                self.set_status(200)
                self.write(({"status": True, "categorynames": categoriesNames}))
            else:
                self.set_status(400)
                self.write(({"status": False, "message": "no country founds"}))

        except Exception as e : 
            self.set_status(500)
            self.write(({"status": False, "message": str(e)}))
