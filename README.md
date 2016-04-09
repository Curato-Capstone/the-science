# The Science

Here's how to science!

## server.py
Microservices for all.

*GET /suggestions*
__params__
- q
..- Query string that a user searches on
..- String

- user_id
..- **required**
..- User ID value to find suggestions for
..- String (UUID, probably)

## algo.py

*find_user_by_id(user_id)*
Finds user by their ID

