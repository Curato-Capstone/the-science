# The Science

Here's how to science!

### Installing dependencies
You won't have any, I'm dealing with it.

## Microservice API Calls (server.py)
**_GET /suggestions_**

Function:

Get some sweet, sweet suggestions.

Query params:
```yaml
  {
    user_id: (String, required) user's uuid,
    q: (String, optional) query term to earch on,
    num_sugg: (String or int, optional) number of suggestions you want back
  }
```

Response body (200):

An array of JSON objects from Foursquare, that looks like this:

```yaml
  {
    "allowMenuUrlEdit": (Boolean), not relevant to user,
    "categories": (Array of JSON objects) some stuff in them that the client doesn't need to see
     "contact": {
        "formattedPhone": (String) formatted like so: "(xxx) xxx-xxxx",
        "phone": (String) another phone number format: "xxxxxxxxxxx"
     },
     "hereNow": (JSON object) if we used Foursquare accounts this would matter,
     "id": (String) venue id,
     "location": {
        "address": (String) street address,
        "cc": (String) country code,
        "city": (String) city name,
        "country": (String) country name,
        "distance": (Int, probably) distance from given coords in meters,
        "formattedAddress": (Array of strings) streed address, city/state/zip, country,
        "lat": (Float) lat,
        "lng": (Float) long,
        "postalCode": (String) zipcode,
        "state": (String) state name abbreviation
     },
     "name": (String) name of business/point of interest,
     "referralId": (String) meh,
     "specials": (Object) also meh,
     "stats": (Object) some info about people who have left tips or checked in here,
     "url": (String) url for the place,
     "venueChains": (Array of strings) venue id's for other stores in the chain,
     "verified": (Boolean) are you real or are you fake?
  }
```

Response (400):

```
{
  message: (String) reminds you to send the user id
}
```

**_POST /suggestions_**

Function:

Get suggestions in the absense of a user ID

Request body (JSON):
```json
{
  "price": 1,
  "culture": 1,
  "food": 1,
  "outdoors": 5,
  "entertainment": 1,
  "relaxation": 1,
  "shopping": 1,
  "sports": 1
}
```

Response body:

Same as above.



**_POST /business-info_**

Function:

Get business info for specific businesses

Request body (JSON):
```yaml
{
  favorites ([String]): list of venue ids
}
```

Response body:

Same as above.

Thanks Foursquare, we love your API dawg