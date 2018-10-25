from flask import Flask
from flask_restful import Api, Resource
import pymongo
from dbcreds import *
import time
import os

app = Flask(__name__)
api = Api(app)

allsolardata = []
allacmainsdata = []

connection = pymongo.MongoClient(DB_HOST, DB_PORT)
db = connection[DB_NAME]
db.authenticate(DB_USER, DB_PASS)
collections_list = db.list_collection_names()
#collection_1 = db['solar']
#collection_2 = db['acmains']

#Set time zone for Lagos Nigeria
#os.environ['TZ'] = 'Africa/Lagos'
#time.tzset()

class Root(Resource):
    def get(self):
        return {"message": "Welcome to etechtra RESTful service"}

class Update(Resource):
    def get(self, sourcetype, deviceid, voltage, current):
        power = format(round( (voltage * current)/1000 , 2))
        updatedata = {'deviceid': deviceid, 'voltage': voltage, 'current': current, 'power': power,
                      'logged': time.time()}
        if sourcetype in collections_list:
            collection = db[sourcetype]
            updatestatus = collection.insert_one(updatedata)
            if updatestatus.acknowledged:
                return {'status': 'update sucessfull'}, 200
            else:
                return {'error': 'there was a problem updating'}
        return {'error' : 'invalid sourcetype' }


class Getall(Resource):
    def get(self, sourcetype, deviceid, sorting = 'asc'):
        if sorting == 'desc':
            order = -1
        elif sorting == 'asc':
            order = 1
        else:
            return {'message': 'invalid sorting order'}
        query = {'deviceid': deviceid}
        if sourcetype in collections_list:
            collection = db[sourcetype]
            records = collection.find(query, {'_id': 0, 'deviceid': 0}).sort( 'logged', order)
            returndata = []
            for record in records:
                returndata.append(record)
            if not returndata:  # return data is empty
                return {'message': 'No Records found for device with id ' + str(deviceid)}, 200
            else:
                return {'data': returndata}, 200
        return {'error': 'invalid sourcetype'}

class Getlastentry(Resource):
    def get(self, sourcetype, deviceid):
        query = {'deviceid': deviceid}
        if sourcetype in collections_list:
            collection = db[sourcetype]
            records = collection.find(query, {'_id': 0, 'deviceid': 0}).sort( 'logged', -1).limit(1)
            returndata =  None
            for record in records:
                returndata = record
            if not returndata:  # return data is empty
                return {'message': 'No Records found for device with id ' + str(deviceid)}, 200
            else:
                return {'data': returndata}, 200
        return {'error': 'invalid sourcetype'}

class Getentries(Resource):
    def get(self, sourcetype, deviceid, entriesno, sorting = 'desc'):
        if sorting == 'asc':
            order = 1
        elif sorting == 'desc':
            order = -1
        else:
            return {'message': 'invalid sorting order'}
        query = {'deviceid': deviceid}
        if isinstance( entriesno, int):
            if sourcetype in collections_list:
                collection = db[sourcetype]
                records = collection.find(query, {'_id': 0, 'deviceid': 0}).sort( 'logged', order).limit(entriesno)
                returndata =  []
                for record in records:
                    returndata.append(record)
                if not returndata:  # return data is empty
                    return {'message': 'No Records found for device with id ' + str(deviceid)}, 200
                else:
                    return {'data': returndata}, 200
            return {'error': 'invalid sourcetype'}
        return {'error': 'invalid number of entries'}


api.add_resource(Root,'/')
api.add_resource(Update, '/update/<string:sourcetype>/<int:deviceid>/<float:voltage>/<float:current>')
api.add_resource(Getall, '/getall/<string:sourcetype>/<int:deviceid>', '/getall/<string:sourcetype>/<int:deviceid>/<string:sorting>')
api.add_resource(Getlastentry, '/getlastentry/<string:sourcetype>/<int:deviceid>')
api.add_resource(Getentries, '/getentries/<string:sourcetype>/<int:deviceid>/<int:entriesno>', '/getentries/<string:sourcetype>/<int:deviceid>/<int:entriesno>/<string:sorting>')

if __name__ == '__main__':
    app.run(port=5000)