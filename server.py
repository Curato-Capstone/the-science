from flask import Flask, Response, request
import flask
import algo
import json

app = Flask(__name__)

@app.route('/suggestions', methods=["GET", "POST"])
def suggestion_route():
    if request.method == "GET":
      query = request.args.get('q')
      user_id = request.args.get('user_id')
      num_places = request.args.get('num_sugg')

      if user_id is None:
        return flask.abort(400)
      elif query is None:
        query = ""

      if num_places is None:
        num_places = 10
      else:
        num_places = int(num_places)

      sugg = algo.get_suggestions(user_id, num_places, 3, query)

    else:
      # change to take a query param
      req = flask.json.loads(request.data)
      prefs = req['preferences']
      q = req['q']
      num_suggs = req['num_suggs']
      if len(prefs) == 0:
        return flask.abort(400)
      sugg = algo.get_new_user_suggestions(prefs, num_suggs, 3, q)

    resp = Response(flask.json.dumps(sugg),  mimetype='application/json')
    resp.headers["Access-Control-Allow-Origin"] = '*'
    return resp

@app.route('/place/<venue_id>')
def place_info(venue_id):
  sugg = algo.find_business_by_id(venue_id)

  resp = Response(flask.json.dumps(sugg), mimetype='application/json')
  resp.headers["Access-Control-Allow-Origin"] = '*'
  return resp

@app.route('/')
def main_route():
  return "You aren't supposed to be here."

@app.route('/business-info', methods=["POST"])
def business_route():
  businesses = flask.json.loads(request.data)['favorites']

  details = []
  for business in businesses:
    item = algo.find_business_by_id(business)
    details.append(item)

  resp = Response(flask.json.dumps(details), mimetype='application/json')
  resp.headers["Access-Control-Allow-Origin"] = '*'
  return resp

@app.errorhandler(400)
def invalid_request(e):
  response = flask.jsonify({"message": "Send the user ID"})
  response.status_code = 400
  return response

if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True, port=5000)

