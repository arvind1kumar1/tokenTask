# 1. Endpoint to generate unique token in the pool.
# 2. Endpoint to assign unique token. On hitting this endpoint, server should assign available random token from the pool and should not serve the same token again until it's freed or unblocked. If no free token is available in pool, it should serve 404.
# 3. Endpoint to unblock the token in the pool. Unblocked token can then be served in (2)
# 4. Endpoint to delete the token in the pool. Deleted token should be removed from the pool.
# 5. Endpoint to keep the tokens alive. All tokens should receive this endpoint within 5 minutes. If a token doesn't receive a keep-alive in last 5 mins, it should be deleted from pool and should not be served again.
# 6. By default each token will be freed/released automatically after 60s of use. To keep the token allocated to himself, client should request keep-alive (5) on same token within 60s.
# Enforcement: No operation should result in iteration of whole set of tokens; i.e, complexity cannot be O(n).
# Please deploy the same on Heroku and also share the postman collection of all those apis.


from flask import Flask,request,abort
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime,timedelta
import uuid
app = Flask(__name__)

allTokens = []
freeTokens = []
allocatedTokens = []
tokenDict = {}

@app.route('/generateToken')
def generateToken():
    token = uuid.uuid1()
    print(token)
    allTokens.append(str(token))
    freeTokens.append(str(token))
    tokenDict[str(token)] = {"keepAliveTime":datetime.now().replace(microsecond=0),"refreshTime":datetime.now().replace(microsecond=0)}
    print("tokenDict ",tokenDict)
    return str(token)

@app.route('/assignToken',methods = ['POST'])
def assignToken():
    # userId = request.post["userId"]    
    print("request ",request)
    data = request.get_json()
    print(data["userId"])
    if len(freeTokens) > 0:
        token = freeTokens.pop(0)
        allocatedTokens.append(token)
        tokenDict[token]["clientId"] = data["userId"] 
        # if token in tokenDict.keys():
        #     tokenDict[token]["clientId"] = data["userId"]       
        # else:
        #     tokenDict[str(token)] = {"keepAliveTime":datetime.now().replace(microsecond=0),"refreshTime":datetime.now().replace(microsecond=0),"clientId":data["userId"]}

    else:
        abort(404)
    print("tokenDict ",tokenDict)
    return str("assign token successfully")

@app.route('/unblokToken',methods = ['POST'])
def unblokToken():
    data = request.get_json()
    token = data["token"]
    print('token ',token) 
    if token not in allTokens:
        return "this is wrong token"  
    elif token in freeTokens:
        return "token already freed/unblock"
    else:
        tokenDict[token]["keepAliveTime"] = datetime.now().replace(microsecond=0)
        tokenDict[token]["clientId"] = ""
        freeTokens.append(token)
        allocatedTokens.remove(token)
        return "unblock token successfully"

@app.route('/deleteToken',methods = ['POST'])
def deleteToken():
    data = request.get_json()
    token = data["token"]
    print('token ',token) 
    if token not in allTokens:
        return "this is wrong token"  
    elif token in allocatedTokens:
        return "token allocated this time"
    else:
        if token in tokenDict.keys():
            del tokenDict[token]
        if token in freeTokens:
            freeTokens.remove(token) 
            allTokens.remove(token)
        if tokens in allocatedTokens:
            allocatedTokens.remove(token)
            allTokens.remove(token)
        return "token is deleted successfully"

@app.route('/keepAliveToken',methods = ['POST'])
def keepAliveToken():
    data = request.get_json()
    token = data["token"]
    print('token ',token) 
    if token not in allTokens:
        return "this is wrong token"      
    else:
        if token in tokenDict.keys():
            tokenDict[token]["keepAliveTime"] = datetime.now().replace(microsecond=0)         
            return "token is keepAlived successfully"  
        return "token does not exist in oken dictionary"

def cronjob():
    print("cronJob Called")
    sched = BackgroundScheduler()
    sched.start()            # c
    after60SecondsFreedToken = sched.add_job(after60SecondsFreed, 'interval',id="id1",minutes=1)
    after5MinutesDeleteToken = sched.add_job(after5MinutesDelete, 'interval',id="id2", minutes=1)
 
def after60SecondsFreed():
    print("after60SecondsFreed is called")
    currentDateTime = datetime.now()   
    filterData = filter(lambda x: tokenDict[x]["refreshTime"] + timedelta(seconds=60) <= currentDateTime,tokenDict)
    ll = list(filterData)
    print("filter data in after60SecondsFreed ",ll)
    for token in ll:
        tokenDict[token]["refreshTime"] = currentDateTime
        if token in allocatedTokens:
            allocatedTokens.remove(token)
        freeTokens.append(token)
        

def after5MinutesDelete():
    print("after5MinutesDelete is called")
    currentDateTime = datetime.now()
    filterData = filter(lambda x: tokenDict[x]["keepAliveTime"] + timedelta(minutes=5) <= currentDateTime,tokenDict)
    ll = list(filterData)
    print("filter data in after5MinutesDelete ",ll)
    for token in ll:
        print("deleted token ",token)
        del tokenDict[token]
        print('tokenDict ',tokenDict)
        allTokens.remove(token)
        if token in allocatedTokens:
            allocatedTokens.remove(token)
        if token in freeTokens:
            freeTokens.remove(token)
        
if __name__ =="__main__":  
    cronjob()
    app.run(debug = True)  