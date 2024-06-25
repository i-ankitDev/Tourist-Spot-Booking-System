from bson import ObjectId
import gridfs
import motor.motor_tornado

myclient = motor.motor_tornado.MotorClient('mongodb://localhost:27017')
mydb = myclient["Tourist_Spot_Booking_System"]

fs = motor.motor_tornado.MotorGridFSBucket(mydb)


def getDatabase():
    return mydb

def getGrid():
    return fs

def findAdmin(mobileNumber):
     return mydb.admin.find_one({"mobileNumber": mobileNumber})

def updateAdmin(mobileNumber,otp):
    mydb.admin.update_one(
                {"mobileNumber": mobileNumber},
                {"$set": {"otp": otp}},
            )
    
async def create_user(dict):
    await mydb.user.insert_one(dict)

async def create_subadmin(dict):
    await mydb.subadmin.insert_one(dict)
    
async def findUserByEmail(email):
    user = await mydb.user.find_one({"email":email})
    return user

async def findUserByMobileNumber(mobileNumber):
    user = await mydb.user.find_one({"mobileNumber":mobileNumber})
    return user

async def findSubAdminById(_id):
    subAdmin = await mydb.subadmin.find_one({"_id":_id})
    return subAdmin

async def findSubAdminByMobileNumber(mobileNumber):
    subAdmin = await mydb.subadmin.find_one({"mobileNumber":mobileNumber})
    return subAdmin

async def findSubAdminByEmail(email):
    subAdmin = await mydb.subadmin.find_one({"email":email})
    return subAdmin

async def insertImage(image_document):
    result = await mydb.spotImages.insert_one(image_document)
    image_id = result.inserted_id
    return image_id

async def addSpot(spot):
    spot_id=await mydb.spots.insert_one(spot)
    return spot_id

async def findSpotByName(name):
    spot = await mydb.spots.find_one({"name":name})
    return spot

async def findSpotById(_id):
    spot = await mydb.spots.find_one({"_id":_id})
    return spot

async def findSpotBySpotId(_id):
    spot = await mydb.spots.find_one({"_id":_id})
    return spot

async def findAllSpots():
    cursor = mydb.spots.find({})
    result = await cursor.to_list(length=None)
    return result

async def findAllUsers():
    cursor = mydb.user.find({})
    result = await cursor.to_list(length=None)
    return result

async def findMaleFemaleUsers():
    pipeline=[
        {
            '$group': {
                '_id': '$gender',
                'count': {
                    '$sum': 1
                }
            }
        },
        {
            '$project': {
                '_id': 0, 
                'gender': '$_id', 
                'count': 1 
            }
        }
    ]
    cursor = mydb.user.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result

async def findAgeWiseUsers():
    pipeline = [
        {
            '$group': {
                '_id': '$age',
                'count': {
                    '$sum': 1
                }
            }
        },
        {
            '$project': {
                '_id': 0, 
                'age': '$_id',  
                'count': 1 
            }
        }
    ]
    cursor = mydb.user.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result

async def findSpotImages(_id):
    spotImage = await mydb.spotImages.find_one({"_id":_id})
    return spotImage    

async def updateImage(_id,data,filename):
    result = await mydb.spotImages.update_one({"_id": _id},
                    {"$set": {"data": data,"filename":filename}})

    return result

async def updateSpot(_id,name,address,category_name,is_active):
    await mydb.spots.update_many({"_id": _id},
                    {"$set": {"name": name,"address":address,"category":category_name,"isActive":is_active}})
 
async def deleteSpot(_id,image_id,country_id,state_id,city_id,category_id):
    await mydb.spots.delete_one({"_id": _id})
    await mydb.spotImages.delete_one({"_id": image_id})
    await mydb.country.update_many({"_id": country_id}, {"$pull": {"spots": _id}})
    await mydb.states.update_many({"_id": state_id}, {"$pull": {"spots": _id}})
    await mydb.city.update_many({"_id": city_id}, {"$pull": {"spots": _id}})
    await mydb.category.update_many({"_id": category_id}, {"$pull": {"spots": _id}})

async def updateSpotAll(_id,country_id,state_id,city_id,category_id):
    await mydb.country.update_many({"_id": country_id}, {"$pull": {"spots": _id}})
    await mydb.states.update_many({"_id": state_id}, {"$pull": {"spots": _id}})
    await mydb.city.update_many({"_id": city_id}, {"$pull": {"spots": _id}})
    await mydb.category.update_many({"_id": category_id}, {"$pull": {"spots": _id}})

async def bookTicket(dict,spot_id,current_date,new_tickets_available):
    result= await mydb.ticketBooking.insert_one(dict)
    id = result.inserted_id
    await mydb.spotTicket.update_one({"spot_id": spot_id},
       {"$set": { f"{current_date}.tickets_available": new_tickets_available},
        "$push": {f"{current_date}.ticketBookings": id}})
 
async def findUserById(_id):
    user = await mydb.user.find_one({"_id":_id})
    return user

async def findTicketDetails(_id):
   ticketDetails = await mydb.ticketBooking.find_one({"_id":_id})
   return ticketDetails

async def updateTicketDetails(_id):
    await mydb.ticketBooking.update_one({"_id": _id},
                    {"$set": {"attendence":True}})

async def cancelTicket(_id,spot_id,slotAvailable,current_date,new_tickets_available):
    await mydb.ticketBooking.update_one({"_id": _id},{"$set": {"isValid":False}})
    await mydb.spotTicket.update_one({"spot_id": spot_id},
       {"$set": { f"{current_date}.tickets_available": new_tickets_available}})
    
async def findTicketHistory(_id):
    pipeline = [
    {
        '$match': {
            'user_id': _id
        }
    }, {
        '$lookup': {
            'from': 'ticketBooking', 
            'localField': '_id', 
            'foreignField': 'user_id', 
            'as': 'ticket_history'
        }
    }
]
    cursor = mydb.ticketBooking.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result

async def find(query,projection):
    return await mydb.spots.find(query, projection).to_list(length=None)

async def findCountry(countryName):
    return await mydb.country.find_one({"name": countryName})

async def findState(stateName):
    return await mydb.states.find_one({"name": stateName})

async def findCity(cityName):
    return await mydb.city.find_one({"name": cityName})

async def findSpot(spotName):
    return await mydb.spots.find_one({"name": spotName})

async def findCategory(categoryName):
    return await mydb.category.find_one({"name": categoryName})

async def addState(stateDetails):
        result = await mydb.states.insert_one(stateDetails)
        return result.inserted_id

async def addCountry(countryDetails):
        result= await mydb.country.insert_one(countryDetails)
        return result.inserted_id

async def addCity(cityDetails):
        result =await mydb.city.insert_one(cityDetails)
        return result.inserted_id

async def addCategory(categoryDetails):
        result= await mydb.category.insert_one(categoryDetails)
        return result.inserted_id

async def updateStateWithSpot(state_id, spot_id):
    await mydb.states.update_one({"_id": state_id}, {"$addToSet": {"spots": spot_id}})

async def updateCityWithSpot(city_id, spot_id):
    await mydb.city.update_one({"_id": city_id}, {"$addToSet": {"spots": spot_id}})

async def updateCountryWithSpot(country_id, spot_id):
    await mydb.country.update_one({"_id": country_id}, {"$addToSet": {"spots": spot_id}})

async def updateCategoryWithSpot(category_id, spot_id, city_id, state_id, country_id):
    await mydb.category.update_many(
        {"_id": category_id}, 
        {
            "$addToSet": {
                "spots": spot_id
            },
            "$set": {
                "city_id": city_id,
                "state_id": state_id,
                "country_id": country_id
            }
        }
    )

async def findSpotTicketById(spot_id):
    return await mydb.spotTicket.find_one({"spot_id": spot_id})

async def spotTicket(spot_id,todayDate,capacity,tickets_available,price,attendence):
    await mydb.spotTicket.update_one(
    {"spot_id": spot_id},
    {
        "$set": {
            todayDate: {
                "capacity": capacity,
                "tickets_available": tickets_available,
                "price": price,
                "attendence":attendence
            }
        }
    },
    upsert=True
)
    
async def updatespotTicket(spot_id,todayDate,attendence):
    await mydb.spotTicket.update_one(
    {"spot_id": spot_id},
    {
        "$set": {
            todayDate: {
                "attendence":attendence
            }
        }
    },
    upsert=True
)

async def findTicketAvailable(spot_id,current_date):
    query = {
        "spot_id": ObjectId(spot_id),
        current_date: {"$exists": True}
    }
    
    projection = {
        f"{current_date}.tickets_available": 1,
        "_id": 0
    }
    
    spot_booking_details = await mydb.spotTicket.find_one(query, projection)
    if spot_booking_details:
        tickets_available = spot_booking_details.get(current_date, {}).get('tickets_available', None)
        return tickets_available
    else:
        return None
    
async def updateAttendence(spot_id, current_date, new_attendence):
    query = {"spot_id": spot_id}
    update_query = {
        "$set": {
            f"{current_date}.attendence": new_attendence
        }
    }
    
    await mydb.spotTicket.update_one(query, update_query)


async def fetch(pipeline):
    cursor = mydb.spotTicket.aggregate(pipeline)
    result = await cursor.to_list(length=None)  # Co
    return result

async def fetchStateByName(name):
   return await mydb.states.find_one({"name":name})

async def fetchCategoryByName(name):
   return await mydb.category.find_one({"name":name})

async def fetchCityByName(name):
   return await mydb.city.find_one({"name":name})

async def findCityByStateId(state_id):
    cursor= mydb.city.find({"state_id":state_id})
    result = await cursor.to_list(length=None)  
    return result

async def findAllCategories():
    return await mydb.category.find().to_list(length=None)

async def findAllCities():
    return await mydb.city.find().to_list(length=None)

async def findAllCountries():
    return await mydb.country.find().to_list(length=None)

async def findSpotsByIds(spot_ids):
    return await mydb.spots.find({"_id": {"$in": spot_ids}}, {"name": 1,"address.city":1}).to_list(length=None)

async def findSpotTicket(spot_id):
    # return await mydb.spotTicket.find({"spot_id":spot_id})  
    cursor= mydb.spotTicket.find({"spot_id":  spot_id})
    result = await cursor.to_list(length=None)  
    return result

async def findCategoryBySpotId(spot_id):
    result = mydb.states.find({"array_field": {"$in": spot_id}})

async def findSpotsByCategory(category_id):
    return await mydb.spots.find({"address.state": category_id}).to_list(length=None)

async def findSpotsByCategories(category_id):
    cursor = mydb.spots.find({"category": category_id})
    spots = await cursor.to_list(length=None)  # Convert cursor to list
    return spots

async def findCategoriesByCity(city_id):
    return await mydb.category.find({"city_id": city_id}).to_list(length=None)

async def findAllStates():
    return await mydb.states.find().to_list(length=None)

async def findSpotTicketInRange(start_date, end_date):
    return await mydb.spotTicket.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(length=None)

async def findCityById(_id):
    return await mydb.city.find_one({"_id":_id})

async def findStateById(_id):
    return await mydb.states.find_one({"_id":_id})

async def findCountryById(_id):
    return await mydb.country.find_one({"_id":_id})

async def findCategoryById(_id):
    return await mydb.category.find_one({"_id":_id})

async def saveRating(mydict):
    return await mydb.rating.insert_one(mydict)

async def findRating(user_id):
    return await mydb.rating.find_one({"user_id":user_id})

async def findRatingBySpotId(spot_id):
    return await mydb.rating.find_one({"spot_id":spot_id})

async def updateRating(_id,rating,comment):
    await mydb.rating.update_one(
    {"_id": _id},
    {
        "$set": {
            "rating":rating,
            "comment":comment
        }
    },
    upsert=True
)
    

async def get_average_rating(spot_id):
    pipeline = [
        {
            "$group": {
                "_id": spot_id,
                "average": {
                    "$avg": "$rating"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "average_rating": "$average"
            }
        }
    ]
    cursor = mydb.rating.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result

async def get_numberOf_rating(spot_id):
    pipeline = [
    {
        '$group': {
            '_id': spot_id, 
            'count': {
                '$sum': 1
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'total_rating': '$count'
        }
    }
]
    cursor = mydb.rating.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    return result