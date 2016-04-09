import math
from users import *

def find_user_by_id(id):
  for user in all_users:
    if user['id'] == id:
      return user
  return "no user"

def find_business_by_id(bid):
  for business in all_businesses:
    if business['business_id'] == bid:
      return business

def k_nearest_neighbors(person, k):
  d = dict()
  for user in all_users:
    if user['id'] == person['id']:
      continue
    else:
      distance = calc_distance(person['preferences'], user['preferences'])
      d[user['id']] = distance

  return sorted(d.items(), key=lambda x: x[1])[0:k]


def calc_distance(pref1, pref2):
  sum = 0
  for pref in pref1:
    sum += (pref1[pref] - pref2[pref]) ** 2
  return math.sqrt(sum)


def suggestions(neighbors):
  master_set = set()
  for neighbor in neighbors:
    user = find_user_by_id(neighbor[0])
    master_set.update(user['liked_businesses'])
  return random.sample(master_set, 3)

neighbors = k_nearest_neighbors(person1, 1)
person_suggestions = suggestions(neighbors)

for sugg in person_suggestions:
  print find_business_by_id(sugg)['name']
