import random
import json
import uuid

all_businesses = dict()

yay_sets = [set(), set(), set(), set(), set(), set(), set()]

all_users = list()

def user_generator(id):
  all_users.append({
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
  })

with open("businesses.json") as json_file:
    all_businesses = json.load(json_file)

for business in all_businesses:
  business['business_id']  = uuid.uuid1()
  the_set = random.sample(yay_sets[:-1], 1)[0]
  the_set.add(business['business_id'])

for i in range(0,10000):
  user_generator(i)

