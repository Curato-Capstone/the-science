import math
import json
import random
from helpers import *

# Basic test taxonomy to help remove items from suggestions
TAXONOMY = {
  "outdoors": ["park", "hike", "trail"],
  "art": ["art", "museum", "dance", "gallery"],
  "sports": ["field", "park", "skatepark"],
  "history": ["history", "landmark", "museum", "monument"],
  "food": ["restaurant", "food", "breakfast", "lunch", "dinner"],
  "entertainment": ["movie", "movies", "music", "theatre", "theater", "concert", "venue"],
  "relaxation": ["beach", "park", "spa", "nail salon", "salon"],
  "shopping": ["mall", "outlet", "outlets", "shopping", "shopping center", "centre", "outlet mall"],
  "culture": [],
  "price": [] #stopgaps
}


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
def choose_suggestions(main_user, neighbors, num_sugg, query=""):
  temp_set = set()
  final_set = set()
  query_set = set()

  # Store all items favorited by neighbors
  for neighbor in neighbors:
    user = find_user_by_id(neighbor[0])
    for item in user['favorites']:
      if item not in main_user['dislikes'] and item not in main_user['favorites']:
        temp_set.add(item)

  # For all items, get business info and add to the final set of businesses if it:
  # has the query term in the tags or the name, else just add it anyways.
  if query:
    for suggestion in temp_set:
      bus = find_business_by_id(suggestion)
      if 'tags' in bus.keys():
        if not any(query in tag.lower() for tag in bus['tags']):
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
  if len(final_set) < num_sugg and not query:
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
    if buss['id'] not in main_user['dislikes'] and buss['id'] not in main_user['favorites']:
      # Filter out suggestions if they are something that the user isn't interested in
      
      if 'tags' in buss.keys():
        tags = buss['tags']
        if query and any(query in tag.lower() for tag in tags):	  
          filtered.add(suggestion)
        else:
          for pref in good_prefs:
            for word in TAXONOMY[pref]:
              if any(word in tag.lower() for tag in tags):
                filtered.add(suggestion)
      if query and query in buss['name'].lower():
        filtered.add(suggestion)
      elif query and any(query in cat['name'].lower() for cat in buss['categories']):
        filtered.add(suggestion)
      else:
        for pref in good_prefs:
	  if any(pref in cat['name'].lower() for cat in buss['categories']):
	    filtered.add(suggestion)
	  if pref in buss['name'].lower():
	    filtered.add(suggestion) 
       
          for word in TAXONOMY[pref]:
            if any(word in cat['name'].lower() for cat in buss['categories']):
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
            keep = keep or val in category['name'].lower()
          if 'tags' in buss.keys():
            keep = keep or any(val in tag.lower() for tag in buss['tags'])
          if keep:
            final_filter.add(item)
      filtered = final_filter
    else:
      for item in filtered:
        buss = find_business_by_id(item)
        keep = query in buss['name'].lower()
        for category in buss['categories']:
          keep = keep or query in category['name'].lower()
          if 'tags' in buss.keys():
            keep = keep or any(query in tag.lower() for tag in buss['tags'])
          if keep:
            final_filter.add(item)
      filtered = final_filter
  return filtered


def find_preference_on_search(query):
  for item in TAXONOMY:
    if query in TAXONOMY[item]:
      return item
  return None

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
    'dislikes': [],
    'favorites': []
  }
  neighbors = k_nearest_neighbors(user, k_num)
  suggestions = choose_suggestions(user, neighbors, num_sugg, query)
  things = []
  for sugg in suggestions:
    things.append(find_business_by_id(sugg))
  return things
