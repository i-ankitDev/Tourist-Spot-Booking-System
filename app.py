import tornado.ioloop
import tornado.web
from utils.db import getDatabase,getGrid
from utils.db import getDatabase,getGrid
from handlers.auth import LoginHandler, LogoutHandler, SignupModule
from handlers.adminHandler import AdminHandler
from handlers.subadminHandler import SubAdminHandler
from handlers.userHandler import UserHandler
from handlers.bookingHandler import BookingHandler
from handlers.bookingHistoryHandler import BookingHistoryHandler
from handlers.adminSpotHandler import AdminSpotHandler
from handlers.cityHandler import CityHandler
from handlers.stateHandler import StateHandler
from handlers.countryHandler import CountryHandler
from handlers.categoryHandler import CategoriesHandler
from handlers.ratingHandler import RatingHandler
from handlers.filterHandler import FilterHandler
from handlers.timeslothandler import TimeSlotHandler

def make_app():
    db=getDatabase()
    fs=getGrid()
    return tornado.web.Application([
        (r"/login", LoginHandler,dict(db=db)),
        (r"/signup", SignupModule,dict(db=db)),
        (r"/logout", LogoutHandler),
        (r"/admin/spot",AdminHandler ,dict(db=db,fs=fs)),
        (r"/admin/spot/edit",AdminSpotHandler ,dict(db=db)),
        (r"/subadmin",SubAdminHandler ,dict(db=db,fs=fs)),
        (r"/user",UserHandler ,dict(db=db,fs=fs)),
        (r"/user/booking",BookingHandler ,dict(db=db)),
        (r"/user/bookinghistory",BookingHistoryHandler ,dict(db=db)),
        (r"/getcities",CityHandler ,dict(db=db)),
        (r"/getstates",StateHandler ,dict(db=db)),
        (r"/getcountries",CountryHandler ,dict(db=db)),
        (r"/getcategories",CategoriesHandler ,dict(db=db)),
        (r"/user/rating",RatingHandler ,dict(db=db)),
        (r"/spot/filter",FilterHandler ,dict(db=db)),
        (r"/gettimeslot",TimeSlotHandler,dict(db=db)),

    ], cookie_secret="nbkZgds8bKe3SFXKhX09B7AC8NwtUmxq86NBjW6iLGvxItZt_ST5", debug=True)

if __name__ == "__main__":
    
    app = make_app()
    app.listen(8888)
    print("running in http://localhost:8888/")
    tornado.ioloop.IOLoop.current().start()
