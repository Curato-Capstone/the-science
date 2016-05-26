# -*- coding: utf-8 -*-

import redis
import rethinkdb as r
import json
import urllib2

KEEP_ATTRS = ['id', 'name', 'contact', 'location', 'categories', 'url', 'hours', 'rating', 'description', 'tags',
              'image', 'stats']
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

FOURSQUARE_CLIENT = ""
RETHINK_HOST = ""
REDIS_HOST = ""


with open("secret/foursquare.json") as json_file:
  FOURSQUARE_CLIENT = json.load(json_file)
with open("secret/connections.json") as json_file:
  hosts = json.load(json_file)
  RETHINK_HOST = hosts['rethinkdb']
  REDIS_HOST = hosts['redis']

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
      image = "http://i.imgur.com/JGq91FT.jpg"

  else:
    image = "http://i.imgur.com/JGq91FT.jpg"
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
    if detail == 'hours':
      venue_details[detail] = format_hours(venue_details[detail])


  rd.set(venue_details['id'], json.dumps(venue_details))
  return venue_details

def format_hours(hours_json):
  hours = hours_json['timeframes']
  formatted_hours = {}

  for item in hours:
    open_hours = item['open'][0]['renderedTime']
    num_bundles = item['days'].split(',')
    num_bundles = [item.strip() for item in num_bundles]

    for bundle in num_bundles:
      result = bundle.encode('utf-8').split('–')

      if len(result) > 1:
        start = DAYS.index(result[0])
        end = DAYS.index(result[1]) + 1

        if start == 7:
          start = 0
          formatted_hours['Sun'] = open_hours

        for i in range(start, end, 1):
          formatted_hours[DAYS[i]] = open_hours
      else:
        formatted_hours[DAYS[DAYS.index(result[0])]] = open_hours

  if len(formatted_hours.keys()) < 7:
    for day in DAYS:
      if day not in formatted_hours.keys():
        formatted_hours[day] = 'Closed'

  return formatted_hours

# Grab all keys for cached businesses
def get_cached_businesses():
  return rd.keys()

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

# Get a user's preferences that are equal to or higher than a five
def get_good_prefs(user):
  good_prefs = set()
  user_prefs = user['preferences']

  # if a user likes something enough, save it
  for pref in user_prefs:
    if user_prefs[pref] >= 3:
      good_prefs.add(pref)
  return good_prefs
