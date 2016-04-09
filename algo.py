import math
from users import *

# TODO: make this rethinky
def find_user_by_id(id):
  for user in all_users:
    if user['id'] == id:
      return user
  return "no user"

# TODO: make this rethinky
def find_business_by_id(bid):
  for business in all_businesses:
    if business['business_id'] == bid:
      return business

# TODO: make this not crappy
def k_nearest_neighbors(person, k):
  d = dict()
  for user in all_users:
    if user['id'] == person['id']:
      continue
    else:
      distance = calc_distance(person['preferences'], user['preferences'])
      d[user['id']] = distance
  return sorted(d.items(), key=lambda x: x[1])[0:k]


# Takes two user preferences and returns distance between all dimensions
def calc_distance(pref1, pref2):
  sum = 0
  for pref in pref1:
    sum += (pref1[pref] - pref2[pref]) ** 2
  return math.sqrt(sum)

# Choose some random suggestions based on the neighbors and optional query string
def choose_suggestions(neighbors, query=""):
  temp_set = set()
  final_set = set()

  for neighbor in neighbors:
    user = find_user_by_id(neighbor[0])
    temp_set.update(user['liked_businesses'])

  for suggestion in temp_set:
    bus = find_business_by_id(suggestion)
    if query and query not in bus['tags']:
        continue
    final_set.add(suggestion)

  num_sugs = 3 if len(final_set) >= 3 else len(final_set)
  return random.sample(final_set, num_sugs)

# Called by microservice, gets all them suggestions
def get_suggestions(user_id, k_num, query):
  user = find_user_by_id(user_id)
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(neighbors, query)
  things = []
  for sugg in suggestions:
    things.append(find_business_by_id(sugg))
  return things

