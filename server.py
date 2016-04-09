from flask import Flask, Response, request
import flask
import algo
import rethinkdb as r

app = Flask(__name__)

@app.route('/suggestions')
def special_thing():
    query = request.args.get('q')
    user_id = int(request.args.get('user_id'))

    if user_id is None:
      return flask.abort(400)
    elif query is None:
      query = ""

    sugg = flask.json.dumps(algo.get_suggestions(user_id, 3, query))
    return Response(sugg,  mimetype='application/json')

@app.route('/')
def main_thing():
  return "You aren't supposed to be here."

@app.errorhandler(400)
def invalid_request(e):
  response = flask.jsonify({"message": "Send the user ID"})
  response.status_code = 400
  return response

if __name__ == '__main__':
  app.run(debug=True)

