import random
import json
import uuid

all_businesses = dict()
temp_set = set()
temp_set2 = set()
all_users = list()

with open("businesses.json") as json_file:
    all_businesses = json.load(json_file)

for business in all_businesses:
  business['business_id']  = uuid.uuid1()
  if random.randint(0,10) > 8:
    temp_set.add(business['business_id'])
  elif random.randint(0,20) < 4:
    temp_set2.add(business['business_id'])

person1 = {
  'id': 4,
  'preferences': {
    'price': 3,
    'culture': 5,
    'food': 3,
    'outdoors': 2,
    'entertainment': 3,
    'relaxation': 2,
    'shopping': 1,
    'sports': 1
  },
  'liked_businesses': set()
}

person2 = {
  'id': 2,
  'preferences': {
    'price': 4,
    'culture': 5,
    'food': 2,
    'outdoors': 2,
    'entertainment': 5,
    'relaxation': 1,
    'shopping': 3,
    'sports': 1
  },
  'liked_businesses': set()
}

person2['liked_businesses'] = temp_set

person3 = {
  'id': 1,
  'preferences': {
    'price': 1,
    'culture': 1,
    'food': 5,
    'outdoors': 5,
    'entertainment': 3,
    'relaxation': 5,
    'shopping': 3,
    'sports': 4
  },
  'liked_businesses': set()
}

person4 = {
  'id': 9,
  'preferences': {
    'price': 1,
    'culture': 1,
    'food': 1,
    'outdoors': 1,
    'entertainment': 1,
    'relaxation': 1,
    'shopping': 1,
    'sports': 1
  },
  'liked_businesses': set()
}

person4['liked_businesses'] = temp_set2

all_users.append(person1)
all_users.append(person2)
all_users.append(person3)
all_users.append(person4)
