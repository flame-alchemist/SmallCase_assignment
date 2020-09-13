from flask import Flask, render_template, request,abort,jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.json_util import dumps
from bson.objectid import ObjectId
import json
import os,base64,hashlib
import tradesFunctions 
import portfolioFunctions

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['MONGO_DBNAME'] = 'new_database'
app.config["MONGO_URI"] = "mongodb://localhost:27017/smallcase_database"
mongo = PyMongo(app)

'''-----------------------PORTFOLIO APIS-----------------------'''
#ADD PORTFOLIO
@app.route('/api/portfolio', methods=['POST'])            
def add_portfolio():
    portfolio = mongo.db.portfolio
    if not request.is_json or request=={}:
        abort(405)
    
    secID = request.json["secID"]
    avgPrice = request.json["avgPrice"]
    totalShares = request.json["totalShares"]

    if totalShares < 0:
        return jsonify({"Response Message":"Shares must be positive"}), 405
    
    security = portfolio.find_one({"_id":secID})

    if security:
        return jsonify({"Response Message":"Portfolio exists"}), 405
    else:
        portfolio.insert_one({"_id":secID, "totalShares":totalShares, "avgPrice":avgPrice, "totalTrades":[]})
        return jsonify({}),200
    
    return jsonify({}),204

#FETCH HOLDINGS
@app.route('/api/holding', methods=['GET'])            
def get_holdings():
    portfolio = mongo.db.portfolio
    if not request.is_json or request=={}:
        abort(405)

    count = portfolio.count()
    if count:
        securityList = []
        securities = portfolio.find()
        for security in securities:
            securityList.append({"secID":security["_id"], "totalShares":security["totalShares"], "avgPrice":security["avgPrice"]})
        return jsonify(securityList),200
    else:
        return jsonify({}), 204

#FETCH PORTFOLIOS
@app.route('/api/portfolio', methods=['GET'])            
def get_portfolios():
    portfolio = mongo.db.portfolio
    trade = mongo.db.trade
    if not request.is_json or request=={}:
        abort(405)

    count = portfolio.count()
    if count:
        securityList = []
        securities = portfolio.find()
        for security in securities:
            tradeList = []
            for tradeID in security["totalTrades"]:
                currentTrade = trade.find_one({"_id":ObjectId(tradeID)})
                if currentTrade["shares"] > 0:
                    tradeList.append({"id":str(currentTrade["_id"]), "tradeType":currentTrade["tradeType"], "shares":currentTrade["shares"], "price":currentTrade["price"]})
                else:
                    tradeList.append({"id":str(currentTrade["_id"]), "tradeType":currentTrade["tradeType"], "shares":-currentTrade["shares"]})
            securityList.append({"secID":security["_id"], "totalTrades":tradeList})
        return jsonify(securityList),200
    else:
        return jsonify({}), 204

#FETCH RETURNS
@app.route('/api/returns', methods=['GET'])            
def get_returns():
    portfolio = mongo.db.portfolio
    trade = mongo.db.trade
    if not request.is_json or request=={}:
        abort(405)

    count = portfolio.count()
    if count:
        securities = portfolio.find()
        returnValue = 0
        for security in securities:
            returnValue = returnValue + 100*security["totalShares"]
        
        return jsonify({"Returns":returnValue}),200
    else:
        return jsonify({}), 204

'''-----------------------TRADES APIS-----------------------'''
#ADD TRADES
@app.route('/api/trade', methods=['POST'])            
def add_trade():
    trade = mongo.db.trade
    portfolio = mongo.db.portfolio
    if not request.is_json or request=={}:
        abort(405)
    
    if request.json["shares"] < 0:
        return jsonify({"Response Message":"Shares must be positive"}), 405

    secID = request.json["secID"]
    
    security = portfolio.find_one({"_id":secID})
    if security:
        new_data = tradesFunctions.newTrade(None, security, request, mongo)
        
        if new_data==-1:
            return jsonify({"Response Message":"Not enough shares"}), 405
        elif new_data==-2:
            return jsonify({"Response Message":"Trade type not Buy/Sell"}), 405
        
        trade.insert_one(new_data)
        portfolioFunctions.updatePortfolio1(secID, None, "add", mongo)

        return jsonify({}),200
    else:
        return jsonify({"Response Message":"Security does not exist"}), 405

    return jsonify({}), 204

#DELETE TRADES
@app.route('/api/trade', methods=['DELETE'])            
def delete_trade():
    trade = mongo.db.trade
    portfolio = mongo.db.portfolio
    if not request.is_json or request=={}:
        abort(405)
    
    tradeID = request.json["tradeID"]

    currentTrade = trade.find_one({"_id":ObjectId(tradeID)})
    if currentTrade:
        secID = currentTrade["secID"]
        portfolioFunctions.updatePortfolio1(secID, tradeID, "delete", mongo)
        trade.remove(currentTrade)
        return jsonify({}),200
    else:
        return jsonify({"Response Message":"Trade does not exist"}), 405

    return jsonify({}), 204

#UPDATE TRADES
@app.route('/api/trade', methods=['PUT'])            
def update_trade():
    trade = mongo.db.trade
    portfolio = mongo.db.portfolio
    if not request.is_json or request=={}:
        abort(405)
    
    if request.json["shares"] < 0:
        return jsonify({"Response Message":"Shares must be positive"}), 405
    
    tradeID = request.json["tradeID"]
    
    currentTrade = trade.find_one({"_id":ObjectId(tradeID)})
    if currentTrade:
        new_data = tradesFunctions.newTrade(currentTrade, None, request, mongo)
        print(new_data)
        if new_data==-1:
            return jsonify({"Response Message":"Not enough shares"}), 405
        elif new_data==-2:
            return jsonify({"Response Message":"Trade type not Buy/Sell"}), 405
                
        portfolioFunctions.updatePortfolio2(currentTrade["secID"], tradeID, new_data, mongo)
        trade.find_one_and_update({"_id":ObjectId(tradeID)},{"$set": new_data})

        return jsonify({}),200
    else:
        return jsonify({"Response Message":"Trade does not exist"}), 405

    return jsonify({}), 204

@app.route('/')
def index():
    return "<h1>SmallCase Backend Assignment!!</h1>"

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080, debug=True)
