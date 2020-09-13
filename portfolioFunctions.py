from bson.objectid import ObjectId

#function to update portfolio based on a trade (only for ADD and DELETE trade)
def updatePortfolio1(secID, tradeID, action, mongo):
    portfolio = mongo.db.portfolio
    trade = mongo.db.trade
    security = portfolio.find_one({"_id":secID})
    
    newPrice = 0
    currentPrice = security["avgPrice"]
    currentShares = security["totalShares"]

    if action=="add":
        totalTrades = security["totalTrades"]
        currentTrade = trade.find().sort([("_id",-1)]).limit(1)
        totalTrades.append(str(currentTrade[0]["_id"]))

        if currentTrade[0]["shares"] > 0:
            newPrice = currentPrice*currentShares + currentTrade[0]["price"]*currentTrade[0]["shares"] 
            newPrice = newPrice/(currentShares+currentTrade[0]["shares"])
        else:
            newPrice = currentPrice

        newShares = currentShares + currentTrade[0]["shares"]
        portfolio.find_one_and_update({"_id":secID}, {"$set": {"totalShares":newShares, "avgPrice":newPrice, "totalTrades":totalTrades}})

    elif action=="delete":
        totalTrades = security["totalTrades"]
        totalTrades.remove(tradeID)

        currentTrade = trade.find_one({"_id":ObjectId(tradeID)})

        newShares = currentShares - currentTrade["shares"]
        if currentTrade["shares"] > 0:
            newPrice = currentPrice*currentShares - currentTrade["price"]*currentTrade["shares"] 
            newPrice = newPrice/newShares
        else:
            newPrice = currentPrice
        
        portfolio.find_one_and_update({"_id":secID}, {"$set": {"totalShares":newShares, "avgPrice":newPrice, "totalTrades":totalTrades}})
    

#function to update portfolio based on a trade (only for UPDATE trade)
def updatePortfolio2(secID, tradeID, new_data, mongo):
    portfolio = mongo.db.portfolio
    trade = mongo.db.trade
    security = portfolio.find_one({"_id":secID})
    
    newPrice = 0
    currentPrice = security["avgPrice"]
    currentShares = security["totalShares"]

    currentTrade = trade.find_one({"_id":ObjectId(tradeID)})

    if currentTrade["tradeType"]==new_data["tradeType"]:
        newShares = currentShares - currentTrade["shares"] + new_data["shares"]
        if new_data["shares"] > 0:
            newPrice = currentPrice*currentShares - currentTrade["price"]*currentTrade["shares"] 
            newPrice = newPrice*(currentShares-currentTrade["shares"]) + new_data["price"]*new_data["shares"]
            newPrice = newPrice/newShares
        else:
            newPrice = currentPrice
    
    else:
        newShares = currentShares - currentTrade["shares"] + new_data["shares"]
        if new_data["shares"] > 0:
            newPrice = currentPrice*(currentShares-currentTrade["shares"]) + new_data["price"]*new_data["shares"]
            newPrice = newPrice/newShares
        else:
            newPrice = currentPrice*currentShares - currentTrade["price"]*currentTrade["shares"]
            newPrice = newPrice/(currentShares-currentTrade["shares"])

    portfolio.find_one_and_update({"_id":secID}, {"$set": {"totalShares":newShares, "avgPrice":newPrice}})
