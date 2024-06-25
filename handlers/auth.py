import bcrypt
from bson import ObjectId
from utils.jwt import decode, encode
import tornado.web
import tornado.ioloop
from utils.hashPassword import hashPassowrd
import utils.otp
import utils.db
from utils.validation import validate_email, is_valid_mobile_number

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

class LoginHandler(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        data = tornado.escape.json_decode(self.request.body)
        role = data.get("role")
        if role == "admin":    
            try:
                mobileNumber = data.get("mobileNumber")
                mobileNumber = str(mobileNumber)
                if not mobileNumber:
                    self.set_status(400)
                    self.write({"status": False, "message": "Number is required."})
                    return

                if not mobileNumber.startswith("+91"):
                    mobileNumber = "+91" + mobileNumber
                
                admin_document = await utils.db.findAdmin(mobileNumber)
                if admin_document:
                    admin_document['_id'] = str(admin_document['_id'])
                    otp = utils.otp.generate_otp()
                    utils.otp.send_otp_via_sms(mobileNumber, otp)
                    utils.db.updateAdmin(mobileNumber, otp)
                    self.write({"status": True, "message": "Admin found"})
                else:
                    self.write({"status": False, "message": "Admin not found"})            
        
            except Exception as e:
                self.set_status(500)
                self.write({"status": False, "message": f"An error occurred: {str(e)}"})
        elif role == "user":
            try:
                email = data.get("email")
                password = data.get("password")
            
                if not email or not password:
                    self.set_status(400)
                    self.write({"status": False, "message": "Email and password are required."})
                    return
                
                user = await utils.db.findUserByEmail(email)

                if user is None or not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                    self.set_status(401)
                    self.write({"status": False, "message": "Invalid email or password."})
                else:
                    encoded_user_id = encode(str(user["_id"]))
                    self.set_secure_cookie("auth_token", encoded_user_id, httponly=True, secure=True)
                    self.write({"status": True, "message": "User logged in successfully."})
            except Exception as e:
                self.set_status(500)
                self.write({"status": False, "message": f"An error occurred: {str(e)}"})
        elif role == "subadmin":
            try:
                email = data.get("email")
                password = data.get("password")
            
                if not email or not password:
                    self.set_status(400)
                    self.write({"status": False, "message": "Email and password are required."})
                    return

                subAdmin = await utils.db.findSubAdminByEmail(email)

                if subAdmin is None or not bcrypt.checkpw(password.encode('utf-8'), subAdmin["password"].encode('utf-8')):
                    self.set_status(401)
                    self.write({"status": False, "message": "Invalid email or password."})
                else:
                    encoded_id = encode(str(subAdmin["_id"]))
                    self.set_secure_cookie("auth_token", encoded_id, httponly=True, secure=True)
                    self.write({"status": True, "message": "Sub-Admin logged in successfully."})
            except Exception as e:
                self.set_status(500)
                self.write({"status": False, "message": f"An error occurred: {str(e)}"})
        else:
            self.set_status(401)
            self.write({"status": False, "message": "Invalid Role"})
    
    async def put(self):
        try:
            data = tornado.escape.json_decode(self.request.body)
            mobileNumber = data.get("mobileNumber")
            if not mobileNumber.startswith("+91"):
                mobileNumber = "+91" + mobileNumber
            otp = data.get("otp")
            if not otp:
                self.set_status(400)
                self.write({"status": False, "message": "OTP is required."})
                return
            
            admin = await utils.db.findAdmin(mobileNumber)
            stored_otp = admin.get('otp') if admin else None
            if stored_otp and stored_otp == otp:
                encoded_admin_id = encode(str(admin["_id"]))
                self.set_secure_cookie("auth_token", encoded_admin_id, httponly=True, secure=True)
                self.write({"status": True, "message": "OTP validated successfully"})
            else:
                self.write({"status": False, "message": "Invalid OTP"})
            
        except Exception as e:
            self.set_status(500)
            self.write({"status": False, "message": f"An error occurred: {str(e)}"})

class SignupModule(BaseHandler):
    def initialize(self, db):
        self.db = db

    async def post(self):
        data = tornado.escape.json_decode(self.request.body)
        role = data.get("role")
        if role == "user":
            try:
                email = data.get("email")
                password = data.get("password")
                name = data.get("name")
                mobileNumber = data.get("mobileNumber") 
                gender = data.get("gender") 
                age = int(data.get("age"))
                userByEmail = await utils.db.findUserByEmail(email)
                userByMobileNumber = await utils.db.findUserByMobileNumber(mobileNumber)
                if userByEmail is None and userByMobileNumber is None:
                    if validate_email(email):
                        if is_valid_mobile_number(mobileNumber): 
                            hashed_password = hashPassowrd.hash_password(password)
                            mydict = {"name": name, "email": email, "password": hashed_password, "mobileNumber": mobileNumber,"gender":gender,"age":age, "role": "user"}
                            try:
                                await utils.db.create_user(mydict)
                                self.write({"status": True, "message": "User registered successfully."})
                            except Exception as e:
                                self.set_status(500)
                                self.write({"status": False, "message": f"An error occurred: {e}"})
                        else:
                            self.write({"status": False, "message": "Invalid Mobile Number"})

                    else:
                        self.write({"status": False, "message": "Invalid Email"})
                else:
                    self.write({"status": False, "message": "User already exists"})   
            except Exception as e:
                self.set_status(500)
                self.write({"status": False, "message": f"An error occurred: {e}"})
        elif role == "subadmin":
            if not self.current_user:
                self.set_status(401)
                self.write({"status": False, "message": "Unauthorized"})
                return
            try:
                spot_id = self.get_query_argument("spot_id")
                spot = await utils.db.findSpotById(ObjectId(spot_id))
                if spot is not None: 
                    email = data.get("email")
                    password = data.get("password")
                    name = data.get("name")
                    mobileNumber = data.get("mobileNumber") 
                    subadmin = await utils.db.findSubAdminByMobileNumber(mobileNumber)
                    if subadmin is None:
                        if validate_email(email):
                            if is_valid_mobile_number(mobileNumber): 
                                hashed_password = hashPassowrd.hash_password(password)
                                mydict = {"spot_id": ObjectId(spot['_id']), "name": name, "email": email, "password": hashed_password, "mobileNumber": mobileNumber, "role": "subadmin"}
                                try:
                                    await utils.db.create_subadmin(mydict)
                                    self.write({"status": True, "message": "Sub-Admin registered successfully."})
                                except Exception as e:
                                    self.set_status(500)
                                    self.write({"status": False, "message": f"An error occurred: {e}"})
                            else:
                                self.set_status(400)
                                self.write({"status": False, "message": "Invalid Mobile Number"})
                        else:
                            self.set_status(400)
                            self.write({"status": False, "message": "Invalid Email"})
                    else:
                        self.set_status(400)
                        self.write({"status": False, "message": "Sub-Admin already exists"})   
                else:
                    self.set_status(400)
                    self.write({"status": False, "message": "Spot not found"}) 
            except Exception as e:
                self.set_status(500)
                self.write({"status": "error", "message": f"An error occurred: {str(e)}"})

class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("auth_token")
        self.write({"status": True, "message": "Logged out successfully."})
