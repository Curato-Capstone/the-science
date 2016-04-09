import json
import urllib2


def scraper(results):
  for result in results['results']:
    place_id = result['place_id']
    place_query = place + place_id
    new_data = urllib2.urlopen(place_query)
    place_results = json.load(new_data)
    some_place = place_results['result']

    del some_place['reference']
    del some_place['address_components']
    del some_place['adr_address']
    del some_place['vicinity']
    del some_place['scope']
    del some_place['utc_offset']
    del some_place['icon']
    del some_place['place_id']
    del some_place['url']
    del some_place['id']

    if 'photos' in some_place.keys():
      del some_place['photos']
    if 'reviews' in some_place.keys():
      del some_place['reviews']
    if 'access_points' in some_place['geometry'].keys():
      del some_place['geometry']['access_points']
    if 'opening_hours' in some_place.keys():
      del some_place['opening_hours']['open_now']
      del some_place['opening_hours']['periods']
    if 'rating' in some_place.keys():
      del some_place['rating']
      del some_place['user_ratings_total']
    if 'international_phone_number' in some_place.keys():
      del some_place['international_phone_number']

    some_place['tags'] = some_place['types']
    del some_place['types']

    all_places.append(some_place)

def by_city(city):
  open_data = urllib2.urlopen(city)
  page_one = json.load(open_data)
  has_next_page = False

  if 'next_page_token' in page_one.keys():
    has_next_page = True
    next_page = page_one['next_page_token']

  should_break = False

  for i in range(0, 10):
    if should_break:
      break

    if i == 0:
      scraper(page_one)
    elif has_next_page:
      new_page = city + "&pagetoken=" + next_page
      new_data = urllib2.urlopen(new_page)
      page = json.load(new_data)
      if 'next_page_token' in page.keys():
        next_page = page['next_page_token']
      else:
        should_break = True
      scraper(page)

token = "AIzaSyAYTwNs3Mk-NsSVSsUOHay_Z2vgtCPFTPI"
seattle = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=47.6097,-122.3331&radius=5000&type=museum&key=" + token
bellevue = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=47.6104,-122.2007&radius=5000&type=museum&key=" + token
tacoma = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=47.258728,-122.465973&radius=5000&type=museum&key=" + token
place = "https://maps.googleapis.com/maps/api/place/details/json?key=" + token + "&placeid="
all_places = []

by_city(seattle)
by_city(bellevue)
by_city(tacoma)

print len(all_places)

with open('businesses.json', 'w') as outfile:
  json.dump(all_places, outfile, indent=2)
