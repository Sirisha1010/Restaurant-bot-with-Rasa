# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/


# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []


from typing import Any, Text, Dict, List, Union, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import ast
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormAction
import time




class BingLocationExtractor:

    def __init__(self):
        self.bing_baseurl = "http://dev.virtualearth.net/REST/v1/Locations"
        self.bing_api_key = "AqZbER9OpJ9z_jtiIaqNvSIspMSqcaItEW33mIRSm4qIHL77w8XIuxGf2xKzPjbU"  # Update Bing API key here

    def getLocationInfo(self, query, tracker):

        list_cities = []
        queryString = {
            "query": query,
            "key": self.bing_api_key
        }
        res = requests.get(self.bing_baseurl, params=queryString)

        res_data = res.json()

        if res.status_code != 200 or "low" == (res_data["resourceSets"][0]["resources"][0]["confidence"]).lower():
            return None, None
        else:
            if "locality" in res_data["resourceSets"][0]["resources"][0]["address"]:
                return res_data["resourceSets"][0]["resources"][0]["address"]["locality"], \
                       res_data["resourceSets"][0]["resources"][0]["name"]
            else:
                return "that", res_data["resourceSets"][0]["resources"][0]["name"]


class ActionSetLocation(Action):

    def name(self):
        return "action_set_location"

    def run(self, dispatcher, tracker, domain):
        user_input = tracker.latest_message['text']

        le = BingLocationExtractor()
        locality, location_name = le.getLocationInfo(str(user_input), tracker)

        dispatcher.utter_message(template="Thanks for sharing you location. " + locality.capitalize() + " is pretty place.")
        return [SlotSet("location", location_name)]




class Zomato:

    def __init__(self):
        self.base_url = "https://developers.zomato.com/"
        self.api_key = "e687e99a0f0e8c428740dc4b73178d30"  # Update Zomato API key here
        

    def getZomatoLocationInfo(self, location):
        
        # list storing latitude,longitude...
        location_info = []

        queryString = {"query": location}

        headers = {'Accept': 'application/json', 'user-key': self.api_key}

        res = requests.get(self.base_url + "locations", params=queryString, headers=headers)

        data = res.json()

        if len(data['location_suggestions']) == 0:
            raise Exception('invalid_location')

        else:
            location_info.append(data["location_suggestions"][0]["latitude"])
            location_info.append(data["location_suggestions"][0]["longitude"])
            location_info.append(data["location_suggestions"][0]["entity_id"])
            location_info.append(data["location_suggestions"][0]["entity_type"])
            return location_info

    def get_cuisines(self, location_info):
       
        headers = {'Accept': 'application/json', 'user-key': self.api_key}

        queryString = {
            "lat": location_info[0],
            "lon": location_info[1]
        }

        res = requests.get(self.base_url + "cuisines", params=queryString, headers=headers).content.decode("utf-8")

        a = ast.literal_eval(res)
        all_cuisines_in_a_city = a['cuisines']

        cuisines = {}

        for cuisine in all_cuisines_in_a_city:
            current_cuisine = cuisine['cuisine']
            cuisines[current_cuisine['cuisine_name'].lower()] = current_cuisine['cuisine_id']

        return cuisines

    def get_cuisine_id(self, cuisine_name, location_info):
       
        cuisines = self.get_cuisines(location_info)

        return cuisines[cuisine_name.lower()]

    def get_all_restraunts(self, location, cuisine):
        
        location_info = self.getZomatoLocationInfo(location)
        cuisine_id = self.get_cuisine_id(cuisine, location_info)

        queryString = {
            "entity_type": location_info[3],
            "entity_id": location_info[2],
            "cuisines": cuisine_id,
            "count": 5
        }

        headers = {'Accept': 'application/json', 'user-key': self.api_key}
        res = requests.get(self.base_url + "search", params=queryString, headers=headers)

        list_of_all_rest = res.json()["restaurants"]

        json = []
        for rest in list_of_all_rest:
            name = rest["restaurant"]["name"]
            url = rest["restaurant"]["url"]
            json.append(name)        
            json.append(url)


        return json

   
 class ActionShowRestaurants(Action):

    def name(self):
        return "action_show_restaurants"

    def run(self, dispatcher, tracker, domain):

        user_input = tracker.latest_message['text']

        zo = Zomato()

        # Extracting location either from "location" slot or user input
        le = BingLocationExtractor()
        location_name = tracker.get_slot('location')
        if not location_name:
            locality, location_name = le.getLocationInfo(str(user_input), tracker)

        if not location_name:
            # Utter template
            dispatcher.utter_template(template='utter_ask_location', tracker=tracker)
        else:
            cuisine_type = tracker.get_slot('cuisine')
            list_all_restaurants = zo.get_all_restraunts(location=location_name, cuisine=str(cuisine_type))

            if list_all_restaurants:
                finaldata = []
                for i in range(len(list_all_restaurants)):
                    if i % 3 != 0:
                        continue

                    mydata = {
                        "title": list_all_restaurants[i],
                        "image_url": list_all_restaurants[i + 1],
                        "subtitle": "I don't know anything about it",
                        "default_action": {
                            "type": "web_url",
                            "url": list_all_restaurants[i + 2],
                            "webview_height_ratio": "tall"
                        },
                        "buttons": [
                            {
                                "type": "web_url",
                                "url": list_all_restaurants[i + 2],
                                "title": "View Website"
                            }, {
                                "type": "postback",
                                "title": "Start Chatting",
                                "payload": "DEVELOPER_DEFINED_PAYLOAD"
                            }
                        ]
                    }

                    finaldata.append(mydata)

                message = {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": "{}".format(finaldata)
                        }
                    }
                }

                dispatcher.utter_message(json_message=message)
            else:
                dispatcher.utter_message(template=
                    "Sorry no such restaurant of " + cuisine_type.capitalize() + " available at " + location_name + ". Try looking for some other cuisine.")

        return []
