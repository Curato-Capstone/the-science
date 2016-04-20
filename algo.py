import math
import redis
import rethinkdb as r
import urllib2
import json
import random

# Basic test taxonomy to help remove items from suggestions
TAXONOMY = {
  "outdoors": ["park"],
  "culture": ["art", "museum", "history", "landmark"],
  "sports": [],
  "price": [],
  "food": ["restaurant", "food"],
  "entertainment": [],
  "relaxation": [],
  "shopping": []
}

FOURSQUARE_CLIENT = ""
RETHINK_HOST = ""
REDIS_HOST = ""
KEEP_ATTRS = ['id', 'name', 'contact', 'location', 'categories', 'url', 'hours', 'rating', 'description', 'tags', 'image']

with open("secret/foursquare.json") as json_file:
  FOURSQUARE_CLIENT = json.load(json_file)
with open("secret/connections.json") as json_file:
  hosts = json.load(json_file)
  RETHINK_HOST = hosts['rethinkdb']
  REDIS_HOST = hosts['redis']

'''
Here are some connections
#rd = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
'''
conn = r.connect(RETHINK_HOST, 28015, db="curato").repl()
rd = redis.StrictRedis(host="localhost",port=6379, db=0)


# Find and return a user by their ID
def find_user_by_id(id):
  user = r.table("users").get(id).run(conn)
  return user

# Get all users currently defined
def get_all_users():
  users = r.table("users").run(conn)
  return users

# Find a business by it's business id and return it
def find_business_by_id(bid):
  cache_keys = get_cached_businesses()
  for key in cache_keys:
    business = rd.get(key)
    business = json.loads(business)

    if business['id'] == bid:
      return business
  return find_venue_by_foursquare(bid)

# Find and cache a venue by it's venue id
def find_venue_by_foursquare(venue_id):
  venue = "https://api.foursquare.com/v2/venues/" + \
          venue_id + "?client_id=" + FOURSQUARE_CLIENT['CLIENT_ID'] + \
          "&client_secret=" + FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&v=20130815"
  venue_details = json.load(urllib2.urlopen(venue))['response']['venue']

  image_url = "https://api.foursquare.com/v2/venues/" + venue_id + "/photos?client_id=" + FOURSQUARE_CLIENT['CLIENT_ID'] \
              + "&client_secret=" + FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&v=20130815"
  venue_json = urllib2.urlopen(image_url)

  venue_images = json.load(venue_json)['response']['photos']
  if 'items' in venue_images.keys():
    if len(venue_images['items'] > 0):
      image = venue_images['items'][0]['prefix'] + "original" + venue_images['items'][0]['suffix']
      venue_details['image'] = image
    else:
      image = "http://imgur.com/laeYgMM"
      venue_details['image'] = image
  else:
    image = "http://imgur.com/laeYgMM"
    venue_details['image'] = image

  for detail in venue_details.keys():
    if detail not in KEEP_ATTRS:
      del venue_details[detail]

  rd.set(venue_details['id'], json.dumps(venue_details))
  return venue_details

# Grab all keys for cached businesses
def get_cached_businesses():
  return rd.keys()

# TODO: make this not crappy
def k_nearest_neighbors(person, k):
  d = dict()
  for user in get_all_users():
    if user['id'] == person['id']:
      continue
    else:
      distance = calc_distance(person['preferences'], user['preferences'])
      d[user['id']] = distance

  new_k = len(d) if len(d) < k else k

  return sorted(d.items(), key=lambda x: x[1])[0:new_k]

# Takes two user preferences and returns distance between all dimensions
def calc_distance(pref1, pref2):
  sum = 0
  for pref in pref1:
    sum += (pref1[pref] - pref2[pref]) ** 2
  return math.sqrt(sum)

# Choose some random suggestions based on the neighbors and optional query string
def choose_suggestions(main_user, neighbors, num_sugg, query=""):
  temp_set = set()
  final_set = set()
  query_set = set()

  # Store all items favorited by neighbors
  for neighbor in neighbors:
    user = find_user_by_id(neighbor[0])
    temp_set.update(set(user['favorites']))

  # For all items, get business info and add to the final set of businesses if it:
  # has the query term in the tags or the name, else just add it anyways.
  if query:
    for suggestion in temp_set:
      bus = find_business_by_id(suggestion)
      if 'tags' in bus.keys():
        if not any(query in tag for tag in bus['tags']):
          continue
        elif query in bus['name'].lower():
          final_set.add(suggestion)
  else:
    final_set = temp_set

  # Initial filter of suggestions based on user preferences
  final_set = filter_suggestions(main_user, final_set, query)

  if query:
    query_set.update(final_set)

  # If there aren't enough suggestions, update with all the cached businesses.
  # If there still aren't enough, update it with an API call.
  if len(final_set) < num_sugg:
    final_set.update(filter_suggestions(main_user, get_cached_businesses(), query))

    if len(final_set) < num_sugg:
      more_results = get_suggestions_by_preferences(main_user)
      final_set.update(more_results)

  diff = num_sugg - len(query_set)

  # Update the query set with the cached businesses, or updated it again with an API call
  if query and diff > 0:

    query_set.update(filter_suggestions(main_user, get_cached_businesses(), query))

    if num_sugg - len(query_set) > 0:
      query_result = get_suggestions_by_query(query)
      new_suggs = random.sample(query_result, diff if diff < len(query_result) else len(query_result))
      for item in new_suggs:
        query_set.add(item)

    return random.sample(query_set, num_sugg if num_sugg - len(query_set) <= 0 else len(query_set))
  elif query:
    return random.sample(query_set, num_sugg)
  else:
    return random.sample(final_set, len(final_set) if len(final_set) < num_sugg else num_sugg)

# Filters suggestions by a user's preferences and returns it
def filter_suggestions(main_user, suggestions, query):
  good_prefs = get_good_prefs(main_user)
  filtered = set()

  # For the cold start, if no other users exist and have no suggestions, choose
  # places that people might like based off taxonomy
  for suggestion in suggestions:
    buss = find_business_by_id(suggestion)

    # Filter out suggestions if they are something that the user isn't interested in
    for pref in good_prefs:
      if 'tags' in buss.keys():
        tags = buss['tags']
        for word in TAXONOMY[pref]:
          if any(word in tag for tag in tags):
            filtered.add(suggestion)
          if query and any(query in tag for tag in tags):
            filtered.add(suggestion)
      else:
        for word in TAXONOMY[pref]:
          if word in buss['name'].lower():
            filtered.add(suggestion)
          elif query and query in buss['name'].lower():
            filtered.add(suggestion)
          elif any(word in cat['name'] for cat in buss['categories']):
            filtered.add(suggestion)
          elif query and any(query in cat['name'] for cat in buss['categories']):
            filtered.add(suggestion)

  return filtered


# Get a user's preferences that are equal to or higher than a five
def get_good_prefs(user):
  good_prefs = set()
  user_prefs = user['preferences']

  # if a user likes something enough, save it
  for pref in user_prefs:
    if user_prefs[pref] >= 3:
      good_prefs.add(pref)
  return good_prefs

# Find businesses with foursquare by a user's preferences and return them
def get_suggestions_by_preferences(user):
  prefs = get_good_prefs(user)
  all_items = []
  all_ids = []
  url = "https://api.foursquare.com/v2/venues/search?client_id=" + \
        FOURSQUARE_CLIENT['CLIENT_ID'] + "&client_secret=" + \
        FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&limit=10&v=20130815&ll=47.606,-122.3&query="
  for pref in prefs:
    api_call = url + pref
    venues = json.load(urllib2.urlopen(api_call))['response']['venues']
    for venue in venues:
      all_items.append(venue)
  for item in all_items:
    rd.set(item['id'], json.dumps(item))
    all_ids.append(item['id'])
  return set(all_ids)

# Find businesses with foursquare based on the query term and return them
def get_suggestions_by_query(query):
  print "ping"
  all_items = []
  all_ids = []
  url = "https://api.foursquare.com/v2/venues/search?client_id=" + \
        FOURSQUARE_CLIENT['CLIENT_ID'] + "&client_secret=" + \
        FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&limit=10&v=20130815&ll=47.606,-122.3&query="
  api_call = url + query
  venues = json.load(urllib2.urlopen(api_call))['response']['venues']
  for venue in venues:
    all_items.append(venue)
  for item in all_items:
    rd.set(item['id'], json.dumps(item))
    all_ids.append(item['id'])
  return set(all_ids)

# Called by microservice, gets all them suggestions
def get_suggestions(user_id, num_sugg, k_num, query):
  user = find_user_by_id(user_id)
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(user, neighbors, num_sugg, query)
  things = []
  for sugg in suggestions:
    things.append(find_business_by_id(sugg))
  return things

def get_new_user_suggestions(preferences, num_sugg, k_num, query):
  user = {
    'id': -1,
    'preferences': preferences
  }
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(user, neighbors, num_sugg, query)
  things = []
  for sugg in suggestions:
    things.append(find_business_by_id(sugg))
  return things