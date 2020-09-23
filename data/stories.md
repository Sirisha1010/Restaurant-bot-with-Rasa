## happy path
* greet
  - utter_greet
* mood_great
  - utter_happy

## sad path 1
* greet
  - utter_greet
* mood_unhappy
  - utter_cheer_up
  - utter_did_that_help
* affirm
  - utter_happy

## sad path 2
* greet
  - utter_greet
* mood_unhappy
  - utter_cheer_up
  - utter_did_that_help
* deny
  - utter_goodbye

## say goodbye
* goodbye
  - utter_goodbye

## bot challenge
* bot_challenge
  - utter_iamabot
  
## Restaurant_bot
* greet
  - utter_greet
* search_restaurants
  - utter_ask_location
* location
  - action_set_location
  - slot{"location": "Hyderabad"}
  - utter_ask_cuisine
* cuisine_info{"cuisine":"chinese"}
  - slot{"cuisine": "chinese"}
  - action_show_restaurants
