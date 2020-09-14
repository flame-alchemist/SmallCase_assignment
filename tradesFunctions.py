#function to create a new/update trade data
def newTrade(trade, security, request, mongodb):
    tradeType = request.json["tradeType"]
    price = request.json["price"]
    shares = request.json["shares"]
    new_data = {}
    secID = ""

    if trade==None:
        secID = request.json["secID"]    
    elif security==None:
        secID = trade["secID"]
        security = mongodb.portfolio.find_one({"_id":secID})

    if tradeType=="Sell":
        totalShares = security["totalShares"]
        if shares >= totalShares:
            return -1
        else:
            shares = -shares
        new_data = {"secID":secID, "tradeType":tradeType, "shares":shares, "price":0}

    elif tradeType=="Buy":
        new_data = {"secID":secID, "tradeType":tradeType, "shares":shares, "price":price}
    
    else:
        return -2
    
    return new_data
