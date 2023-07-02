from TransportNSW import TransportNSW
tnsw = TransportNSW()
journey = tnsw.get_trip('207537', '10101100', 'pSFggEFbtsGYto5KNCVOIMEO7BEp7ERtLKAl')
print(journey)

# import requests
# import datetime 
# from urllib.parse import urlencode

# api_key = 'pSFggEFbtsGYto5KNCVOIMEO7BEp7ERtLKAl'  

# origin_lat = -33.884080  
# origin_lon = 151.206290  
# destination_lat = -33.868804 
# destination_lon = 151.209111

# # Set API endpoint and parameters
# api_endpoint = 'https://api.transport.nsw.gov.au/v1/tp/'
# api_call = 'trip'

# # Build request parameters
# params = {
#     'outputFormat': 'rapidJSON',
#     'coordOutputFormat': 'EPSG:4326',
#     'coord': f'{origin_lon}:{origin_lat}:EPSG:4326',
#     'type_origin': 'coord',
#     'name_destination': f'{destination_lon}:{destination_lat}:EPSG:4326',
#     'type_destination':'coord',
#     'itdDate': datetime.date.today().strftime('%Y%m%d'),
#     'itdTime': datetime.datetime.now().strftime('%H%M'),
#     'depArrMacro': 'dep',
#     'numItineraries': 1,
#     'inclFilter': 1,  
#     'apikey': api_key  
# }

# # Make request and get response
# url = api_endpoint + api_call + '?' + urlencode(params)
# response = requests.get(url)
# print("Status code:", response.status_code)
# print("Response body:", response.text)
# data = response.json()

# # Get commute time 
# commute_time = data['journeys'][0]['legs'][0]['duration'] 
# print(f'The estimated commute time is {commute_time} minutes.')



# import requests
# import json

# # API URL and key 
# url = "https://api.transport.nsw.gov.au/v1/tp/trip" 
# key = "pSFggEFbtsGYto5KNCVOIMEO7BEp7ERtLKAl"  

# # Origin and destination addresses 
# origin = "2S Macdonald St, Sydney NSW 2000"
# destination = "Martin Airport Plaza Hotel, 9 Circuit Rd, Sydney NSW 2020"

# # Function to perform geocoding using Google's Geocoding API
# def geocode(address):
#     google_api_key = "AIzaSyA-V3L235PDvM4BJxA4vt_d-ADhpdoF3MU"
#     url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_api_key}"
#     response = requests.get(url)
#     data = response.json()
#     if data['status'] == 'OK':
#         latitude = data['results'][0]['geometry']['location']['lat']
#         longitude = data['results'][0]['geometry']['location']['lng']
#         return (latitude, longitude)
#     else:
#         raise Exception("Error geocoding address: " + data['status'])

# # Geocode the addresses to get latitude and longitude
# origin_coords = geocode(origin)  # Returns (lat, lng)
# destination_coords = geocode(destination) 

# # Construct the API request
# params = {
#     "key": key,
#     "departureTime": "2030-01-10T18:45:00Z",
#     "originCoord": f"{origin_coords[0]},{origin_coords[1]}",
#     "destinationCoord": f"{destination_coords[0]},{destination_coords[1]}" 
# }
# response = requests.get(url, params=params)
# print("Status code:", response.status_code)
# print("Response body:", response.text)

# # Parse the response
# data = json.loads(response.text)  
# journeys = data["journeys"]

# # Get commute time from the first journey 
# first_journey = journeys[0]   
# legs = first_journey["legs"]
# total_duration = 0
# for leg in legs: 
#     total_duration += leg["duration"]

# print(f"The total commute time is {total_duration} seconds ({total_duration/60} minutes).")

# ----------------------------------------------

# import requests
# import json

# def get_commute_time(from_location, to_location, date, time, isDepartureTime, apiKey):
#     url = "https://api.transport.nsw.gov.au/v1/tp/trip"
#     headers = {
#         "Authorization": "Bearer " + apiKey,
#         "Content-Type": "application/json"
#     }
#     body = {
#         "outputFormat": "rapidJSON",
#         "coordOutputFormat": "EPSG:4326",
#         "depArrMacro": "dep" if isDepartureTime else "arr",
#         "itdDate": date,
#         "itdTime": time,
#         "originCoord": {"id": from_location, "type": "stop"},
#         "destinCoord": {"id": to_location, "type": "stop"},
#         "calcNumberOfTrips": 5
#     }

#     response = requests.get(url, headers=headers, data=json.dumps(body))
#     print("Status code:", response.status_code)
#     print("Response body:", response.text)
#     data = response.json()

#     # Parse the response
#     for journey in data.get("journeys", []):
#         for leg in journey.get("legs", []):
#             print(f"Start: {leg['origin']['departureTimePlanned']}, End: {leg['destination']['arrivalTimePlanned']}, Duration: {leg['duration']} minutes")

# # Replace these values with your actual data
# from_location = "10101230"
# to_location = "10101231"
# date = "20230621"
# time = "08:00"
# isDepartureTime = True
# apiKey = "pSFggEFbtsGYto5KNCVOIMEO7BEp7ERtLKAl"

# get_commute_time(from_location, to_location, date, time, isDepartureTime, apiKey)

# ------------------------------------------------

# import requests
# import json

# # Function to perform geocoding using Google's Geocoding API
# def geocode(address):
#     # Replace with your actual API key
#     google_api_key = "AIzaSyA-V3L235PDvM4BJxA4vt_d-ADhpdoF3MU"
#     url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_api_key}"
#     response = requests.get(url)
#     data = response.json()
#     if data['status'] == 'OK':
#         latitude = data['results'][0]['geometry']['location']['lat']
#         longitude = data['results'][0]['geometry']['location']['lng']
#         return (latitude, longitude)
#     else:
#         raise Exception("Error geocoding address: " + data['status'])

# # Function to calculate commute time using the Trip Planner API
# def calculate_commute_time(start_address, end_address):
#     # Replace with your actual API key
#     nsw_api_key = "pSFggEFbtsGYto5KNCVOIMEO7BEp7ERtLKAl"
#     start_coordinates = geocode(start_address)
#     end_coordinates = geocode(end_address)
#     url = "https://api.transport.nsw.gov.au/v1/tp/trip"  # Replace with the actual API endpoint
#     headers = {"Authorization": "Bearer " + nsw_api_key}
#     params = {
#         "outputFormat": "rapidJSON",
#         "coordFrom": f"{start_coordinates[0]}, {start_coordinates[1]}",
#         "coordTo": f"{end_coordinates[0]}, {end_coordinates[1]}"
#     }
#     response = requests.get(url, headers=headers, params=params)
#     data = response.json()
#     # The actual structure of the response will depend on the API
#     # This is just a placeholder
#     commute_time = data['journeys'][0]['duration']
#     return commute_time

# start_address = "100 George St, Sydney NSW 2000, Australia"
# end_address = "1 Farrer Pl, Sydney NSW 2000, Australia"

# commute_time = calculate_commute_time(start_address, end_address)

# print(f"The estimated commute time from {start_address} to {end_address} is {commute_time} minutes.")