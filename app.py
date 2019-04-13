#Python libraries that we need to import for our bot
import random
from flask import Flask, request
from pymessenger.bot import Bot

app = Flask(__name__)
ACCESS_TOKEN = 'EAAEAeEOMjfQBAMOQhcClqXPSv3tLG0nh13GlMB3MihrYPcZBQTptAKqJt7vtRcmVx1I6VqrHfVYRoeh62RbGZCqWUPQG4q9FHCARF8ZCKV8lWbI8DPhW01UfrEYpM1MquAxQe1RHC517C0emCIjZCmbqmFMOxXZC4RiwpUMZBBZBmahROu3mRut'
VERIFY_TOKEN = 'TESTINGTOKEN'
bot = Bot(ACCESS_TOKEN)
user_loc = None

class washroom:
    def __init__(self, lat, long, building, floor, disabled, feminine):
        self.disabled = disabled
        self.feminine = feminine
        self.floor = floor
        self.lat = lat
        self.long = long
        self.building = building

class location:
    def __init__(self, building, lat, long):
        self.building = building
        self.lat = lat
        self.long = long

location_db = []
location_db.append(location('Bruininks Hall', 44.974103, -93.237467))
location_db.append(location('Appleby Hall', 44.974609, -93.237307))
location_db.append(location('Fraser Hall', 44.975563, -93.237265))

washroom_db = []
washroom_db.append(washroom(44.974103, -93.237467, "Bruininks Hall", 1, True, True))
washroom_db.append(washroom(44.974103, -93.237467, "Bruininks Hall", 2, False, True))
washroom_db.append(washroom(44.974103, -93.237467, "Bruininks Hall", 3, True, False))

def where_am_i(lat, long):
    list1 = []
    for x in location_db:
        lat_dif = abs(x.lat - lat)
        long_dif = abs(x.long - long)
        delta = (lat_dif + long_dif)
        list1.append((x.building, delta))
    min_val = [None,10]
    for x in list1:
        if x[1] < min_val[1] and x[1] < 0.0005:
            min_val = x
    return min_val[0]

#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    global awaiting, washroom_db, location_db

    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          if 'messaging' in event:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message'):
                    #Facebook Messenger ID for user so we know where to send response back to
                    recipient_id = message['sender']['id']
                    if 'attachments' in message.get('message'):
                        if (message.get('message')['attachments'][0]['type'] == 'location'):
                            lat = message.get('message')['attachments'][0]['payload']['coordinates']['lat']
                            long = message.get('message')['attachments'][0]['payload']['coordinates']['long']
                            send_message(recipient_id, "Seems like you're in "+where_am_i(lat, long))
                            user_loc = where_am_i(lat, long)
                            send_message(recipient_id, "Are there any requirements for you?")
                            awaiting = 1

                    elif 'text' in message.get('message'):
                        if 'hey' in message.get('message')['text'].lower():
                            send_message(recipient_id, "Hey There!")
                            user_loc = None
                            awaiting = 0

                        if 'where is the nearest' in message.get('message')['text'].lower():
                            send_message(recipient_id, "Could you share your location with us through the Messenger App?")
                                                
                        if 'looking for' in message.get('message')['text'].lower():
                            list1 = washroom_db
                            print (message.get('message')['text'].lower())
                            if 'menstrual products' in message.get('message')['text'].lower():
                                for x in list1:
                                    if x.feminine == False:
                                        list1.remove(x)
                            if 'disabled' in message.get('message')['text'].lower():
                                for x in list1:
                                    if x.disabled == False:
                                        list1.remove(x)
                            send_message(recipient_id, "Here are some washrooms near you: ")
                            for x in list1:
                                to_be_sent = "Floor "+str(x.floor)+" in "+x.building+"\n"
                                if x.feminine:
                                    to_be_sent += "\t\t\t-Menstrual Products : Yes\n"
                                if x.disabled:
                                    to_be_sent += "\t\t\t-Disabled Friendly: Yes\n"
                                send_message(recipient_id, to_be_sent)

                        if 'out of' in message.get('message')['text'].lower():
                            splited = message.get('message')['text'].lower().split()
                            hall_name = splited[:2]
                            floor = splited[2:4]
                            for x in washroom_db:
                                if x.building.lower() == ' '.join(hall_name) and x.floor == int(floor[-1]):
                                    x.feminine = False
                                    send_message(recipient_id, "Thanks for letting us know. We have informed the Housekeeping Staff.")
                                    break

    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

if __name__ == "__main__":
    app.run(host= '0.0.0.0',debug=True, port=8101)