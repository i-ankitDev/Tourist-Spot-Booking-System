import jwt
secretKey = 'nbkZgds8bKe3SFXKhX09B7AC8NwtUmxq86NBjW6iLGvxItZt_ST5_6j_4Xaz4gDhwMblO2voTTee1ui1ki4uP1ytcgtzPGgvp0VjzKqIpcVs'


def encode(user):
    
    payload = {
        "_id" : user
    }
    token = jwt.encode(payload,secretKey,algorithm="HS256") 
    return token

def decode(token):
    token=jwt.decode(token,secretKey,algorithms="HS256")
    return token