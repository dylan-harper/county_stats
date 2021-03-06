from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import statistics
import json
import os

#initialize app
app = Flask(__name__)

#initialize db
base_directory = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_directory, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

#County model
class County(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zip = db.Column(db.String, unique=True, nullable=False)
    h_index = db.Column(db.Float, nullable=False)

    def __init__(self, zip, h_index):
        self.zip = zip
        self.h_index = h_index

#County Schema (excludes id from responses)
class CountySchema(ma.Schema):
    class Meta:
        fields = ('zip', 'h_index')

#create tables in db
db.create_all()

#import JSON Data
json_data = './happiness-index-seed-data.json'
with open(json_data) as file:
     counties = json.load(file)

#convert json key/values into instances of County and persist to db
for key in counties:
    count = County.query.filter_by(zip=key).count()
    if count > 0:
        break

    county = County(zip = key, h_index = counties[key])
    db.session.add(county)
    db.session.commit()

#takes arguments from user to calculate specified statistic
def calculate(action, indexes):
    if action == "mean":
        return statistics.mean(indexes)
    elif action == "median":
        return statistics.median(indexes)
    elif action == "stdev":
        stdev = statistics.stdev(indexes)
        return round(stdev, 2)
    else:
        range = max(indexes) - min(indexes)
        return round(range, 2)

#filters parameters and user entries
@app.route('/api/v1/county/happiness_stats/<action>', methods=['GET'])
def happiness_stats(action):
    stats = ["mean", "median", "stdev", "range"]
    if action not in stats:
        return jsonify({ "error": "Invalid statistic, choose one: [mean, median, stdev, range]"}), 400

    args = request.args
    if len(args) < 2:
        return jsonify({ "error": "Must include more than one county" }), 400

    indexes = []
    for arg in request.args:
        county = County.query.filter(County.zip == arg).first()
        if not county:
            return jsonify({ "error": arg + " is not included in the dataset"}), 400

        indexes.append(county.h_index)

    result = calculate(action, indexes)
    return jsonify({ action: result })

#get a county by id
@app.route('/api/v1/county/<zip>', methods=['GET'])
def show(zip):
    county = County.query.filter(County.zip == zip).first()
    if not county:
        return jsonify({ "error": zip + " is not included in the dataset"}), 400

    return CountySchema().jsonify(county)

#test route to get number of counties, ensure there are no doubles
@app.route('/api/v1/county', methods=['GET'])
def index():
    count = len(County.query.all())
    return jsonify({ "Number of stored counties": count })

#run server on http://127.0.0.1:5000
if __name__ == '__main__':
    app.run(debug=True)
