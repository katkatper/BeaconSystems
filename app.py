from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)

CORS(app)

#temp in-memory database

persons= []

@app.route("/persons", methods=["GET"])
def get_persons():
    return jsonify(persons)

@app.route("/persons", methods=["POST"])
def add_person():
    data= request.json
    persons.append(data)
    return jsonify ({"message": "Person Added"}), 201

if __name__=="__main__":
    app.run(debug=True)


