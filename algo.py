import math
from users import *

# Basic test taxonomy to help remove items from suggestions
TAXONOMY = {
  "outdoors": ["park"],
  "culture": ["art_gallery", "museum"],
  "sports": [],
  "price": [],
  "food": ["restaurant", "food"],
  "entertainment": [],
  "relaxation": [],
  "shopping": []
}

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

def get_all_businesses():
  return all_businesses

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
def choose_suggestions(user_id, neighbors, query=""):
  num_sugs = 3
  temp_set = set()
  final_set = set()
  query_set = set()
  too_few = False

  # Store all items liked by neighbors
  for neighbor in neighbors:
    user = find_user_by_id(neighbor[0])
    temp_set.update(user['liked_businesses'])

  # For all items, get business info and add to the final set of businesses if there needs to be a query term
  for suggestion in temp_set:
    bus = find_business_by_id(suggestion)
    if query and query not in bus['tags']:
        continue
    final_set.add(suggestion)


  if len(final_set) >= 3:
    final_set = filter_suggestions(user_id, final_set, query)
  elif len(final_set) >= 0:
    if query:
      query_set.update(final_set)
    too_few = True
    final_set.update(filter_suggestions(user_id, get_all_businesses(), query))

  # give preference to search term rather than their interests
  if query and too_few:
    for item in final_set:
      if query in find_business_by_id(item)['tags']:
        query_set.add(item)

    if len(query_set) > 3:
      return random.sample(query_set, 3)

    query_set.add(random.sample(final_set, num_sugs - len(query_set))[0])
    return query_set

  return random.sample(final_set, num_sugs)

# Filters suggestions by a user's preferences and returns it
def filter_suggestions(user_id, suggestions, query):
  user_prefs = find_user_by_id(user_id)['preferences']
  good_prefs = set()

  # if a user likes something enough, save it
  for pref in user_prefs:
    if user_prefs[pref] >= 3:
      good_prefs.add(pref)

  filtered = set()

  # For the cold start, if no other users exist and have no suggestions, choose
  # places that people might like based off taxonomy
  if type(suggestions) != set:
    for suggestion in suggestions:
      for pref in good_prefs:
        intersect = set(suggestion['tags']).intersection(TAXONOMY[pref])
        if len(intersect) !=  0 or query in suggestion['tags']:
          filtered.add(suggestion['business_id'])
  else:
    for suggestion in suggestions:
      buss = find_business_by_id(suggestion)

      # Filter out suggestions if they are something that the user isn't interested in
      for pref in good_prefs:
        intersect = set(buss['tags']).intersection(TAXONOMY[pref])
        if len(intersect) != 0 or query in buss['tags']:
          filtered.add(suggestion)

  return filtered


# Called by microservice, gets all them suggestions
def get_suggestions(user_id, k_num, query):
  user = find_user_by_id(user_id)
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(user_id, neighbors, query)
  things = []
  for sugg in suggestions:
    things.append(find_business_by_id(sugg))
  return things

