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
  "food": ["restaurant", "food", "breakfast", "lunch", "dinner"],
  "entertainment": [],
  "relaxation": [],
  "shopping": []
}

FOURSQUARE_CLIENT = ""
RETHINK_HOST = ""
REDIS_HOST = ""
KEEP_ATTRS = ['id', 'name', 'contact', 'location', 'categories', 'url', 'hours', 'rating', 'description', 'tags',
              'image', 'stats']

with open("secret/foursquare.json") as json_file:
  FOURSQUARE_CLIENT = json.load(json_file)
with open("secret/connections.json") as json_file:
  hosts = json.load(json_file)
  RETHINK_HOST = hosts['rethinkdb']
  REDIS_HOST = hosts['redis']

'''
Here are some connections
'''
conn = r.connect(RETHINK_HOST, 28015, db="curato").repl()
rd = redis.StrictRedis(host=REDIS_HOST,port=6379, db=1)

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
  item = rd.get(bid)
  if item is not None:
    return json.loads(item)
  else:
    return find_venue_by_foursquare(bid)

def get_venue_image(venue_id):
  image_url = "https://api.foursquare.com/v2/venues/" + venue_id + "/photos?client_id=" + FOURSQUARE_CLIENT['CLIENT_ID'] \
              + "&client_secret=" + FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&v=20130815"
  venue_json = urllib2.urlopen(image_url)

  venue_images = json.load(venue_json)['response']['photos']
  image = ""
  if 'items' in venue_images.keys():
    if len(venue_images['items']) > 0:
      image = venue_images['items'][0]['prefix'] + "original" + venue_images['items'][0]['suffix']
    else:
      image = "http://imgur.com/laeYgMM.jpg"

  else:
    image = "http://imgur.com/laeYgMM.jpg"
  return image

# Find and cache a venue by it's venue id
def find_venue_by_foursquare(venue_id):
  venue = "https://api.foursquare.com/v2/venues/" + \
          venue_id + "?client_id=" + FOURSQUARE_CLIENT['CLIENT_ID'] + \
          "&client_secret=" + FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&v=20130815"
  venue_details = json.load(urllib2.urlopen(venue))['response']['venue']

  venue_details['image'] = get_venue_image(venue_id)

  for detail in venue_details.keys():
    if detail not in KEEP_ATTRS:
      del venue_details[detail]

  rd.set(venue_details['id'], json.dumps(venue_details))
  return venue_details

# Grab all keys for cached businesses
def get_cached_businesses():
  return rd.keys()


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
  return math.pow(sum, 1.0/len(pref1))

# Choose some random suggestions based on the neighbors and optional query string
# TODO: FIX THIS LOL
def choose_suggestions(main_user, neighbors, num_sugg, query=""):
  temp_set = set()
  final_set = set()
  query_set = set()

  # Store all items favorited by neighbors
  for neighbor in neighbors:
    user = find_user_by_id(neighbor[0])
    for item in user['favorites']:
      if item not in main_user['dislikes']:
        temp_set.add(item)

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
    if buss['id'] not in main_user['dislikes']:
      # Filter out suggestions if they are something that the user isn't interested in

      if 'tags' in buss.keys():
        tags = buss['tags']
        if query and any(query in tag for tag in tags):
          filtered.add(suggestion)
        else:
          for pref in good_prefs:
            for word in TAXONOMY[pref]:
              if any(word in tag for tag in tags):
                filtered.add(suggestion)
      else:
        if query and query in buss['name'].lower():
          filtered.add(suggestion)
        elif query and any(query in cat['name'] for cat in buss['categories']):
          filtered.add(suggestion)
        else:
          for pref in good_prefs:
            for word in TAXONOMY[pref]:
              if any(word in cat['name'] for cat in buss['categories']):
                filtered.add(suggestion)
              elif word in buss['name'].lower():
                filtered.add(suggestion)

  if query != "":
    parent_name = find_preference_on_search(query)
    final_filter = set()

    if parent_name is not None:
      final_filter = set()
      for item in filtered:
        buss = find_business_by_id(item)
        for val in TAXONOMY[parent_name]:
          keep = val in buss['name'].lower()
          for category in buss['categories']:
            keep = keep or val in category['name']
          if 'tags' in buss.keys():
            keep = keep or any(val in tag for tag in buss['tags'])
          if keep:
            final_filter.add(item)
      filtered = final_filter
    else:
      for item in filtered:
        buss = find_business_by_id(item)
        keep = query in buss['name'].lower()
        for category in buss['categories']:
          keep = keep or query in category['name']
          if 'tags' in buss.keys():
            keep = keep or any(query in tag for tag in buss['tags'])
          if keep:
            final_filter.add(item)
      filtered = final_filter
  return filtered


def find_preference_on_search(query):
  for item in TAXONOMY:
    if query in TAXONOMY[item]:
      return item
  return None
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

      venue_details = find_venue_by_foursquare(venue['id'])
      all_items.append(venue_details)

  for item in all_items:
    all_ids.append(item['id'])
  return set(all_ids)

# Find businesses with foursquare based on the query term and return them
def get_suggestions_by_query(query):
  all_items = []
  all_ids = []
  url = "https://api.foursquare.com/v2/venues/search?client_id=" + \
        FOURSQUARE_CLIENT['CLIENT_ID'] + "&client_secret=" + \
        FOURSQUARE_CLIENT['CLIENT_SECRET'] + "&limit=10&v=20130815&ll=47.606,-122.3&query="
  api_call = url + query
  venues = json.load(urllib2.urlopen(api_call))['response']['venues']
  for venue in venues:
    venue_details = find_venue_by_foursquare(venue['id'])
    all_items.append(venue_details)
  for item in all_items:
    rd.set(item['id'], json.dumps(item))
    all_ids.append(item['id'])
  return set(all_ids)

# Called by microservice, gets all them suggestions
def get_suggestions(user_id, num_sugg, k_num, query):
  user = find_user_by_id(user_id)
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(user, neighbors, num_sugg, query)
  returned = []
  for sugg in suggestions:
    returned.append(find_business_by_id(sugg))
  if query == "":
    returned = sorted(returned, key=lambda k: k['stats'].get('checkinsCount'), reverse=True)
  return returned

def get_new_user_suggestions(preferences, num_sugg, k_num, query):
  user = {
    'id': -1,
    'preferences': preferences,
    'dislikes': []
  }
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(user, neighbors, num_sugg, query)
  things = []
  for sugg in suggestions:
    things.append(find_business_by_id(sugg))
  return things