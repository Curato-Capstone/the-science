import random
import json
import uuid

all_businesses = dict()

yay_sets = [set(), set(), set(), set(), set(), set(), set()]
park_set = set()
museum_set = set()

all_users = list()

def user_generator(id):
  some_user = {
    'id': id,
    'preferences': {
      'price': random.randint(1, 5),
      'culture': random.randint(1, 5),
      'food': random.randint(1, 5),
      'outdoors': random.randint(1, 5),
      'entertainment': random.randint(1, 5),
      'relaxation': random.randint(1, 5),
      'shopping': random.randint(1, 5),
      'sports': random.randint(1, 5)
    },
    'liked_businesses': random.sample(yay_sets, 1)[0]
  }

  '''if some_user['preferences']['outdoors'] == 4:
    some_user['liked_businesses'].update(random.sample(park_set, len(park_set)))
  elif some_user['preferences']['outdoors'] == 5:
    some_user['liked_businesses'] = park_set
  elif some_user['preferences']['culture'] == 4:
    some_user['liked_businesses'].update(random.sample(museum_set, len(museum_set)))
  elif some_user['preferences']['culture'] == 5:
    some_user['liked_businesses'] = museum_set'''

  all_users.append(some_user)

best_park = ""

with open("businesses.json") as json_file:
    all_businesses = json.load(json_file)

for business in all_businesses:
  business['business_id']  = uuid.uuid1()
  the_set = random.sample(yay_sets[:-1], 1)[0]
  the_set.add(business['business_id'])
  if 'park' in business['tags']:
    park_set.add(business['business_id'])
    best_park = business['business_id']
  elif 'museum' in business['tags'] or 'art_gallery' in business['tags']:
    museum_set.add(business['business_id'])

for i in range(0,10000):
  user_generator(i)

loves_parks = {
    'id': 98765,
    'preferences': {
      'price': 1,
      'culture': 1,
      'food': 1,
      'outdoors': 5,
      'entertainment': 1,
      'relaxation': 1,
      'shopping': 1,
      'sports': 1
    },
    'liked_businesses': set()
}

loves_art = {
    'id': 12345,
    'preferences': {
      'price': 1,
      'culture': 5,
      'food': 1,
      'outdoors': 1,
      'entertainment': 1,
      'relaxation': 1,
      'shopping': 1,
      'sports': 1
    },
    'liked_businesses': set()
}

loves_artpark = {
    'id': 12346,
    'preferences': {
      'price': 1,
      'culture': 5,
      'food': 1,
      'outdoors': 1,
      'entertainment': 1,
      'relaxation': 1,
      'shopping': 1,
      'sports': 1
    },
    'liked_businesses': set()
}

loves_artpark['liked_businesses'].add(best_park)

all_users.append(loves_parks)
all_users.append(loves_art)
all_users.append(loves_artpark)