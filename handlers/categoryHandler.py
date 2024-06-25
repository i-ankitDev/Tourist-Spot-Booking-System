import tornado
from utils.jwt import decode
import utils.db


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def get_current_user(self):
        auth_cookie = self.get_secure_cookie("auth_token")
        if auth_cookie:
            try:
                token = auth_cookie.decode('utf-8')
                return decode(token)
            except Exception as e:
                print(f"Error decoding token: {e}")
                return None
        return None
    
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
