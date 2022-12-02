from paho import mqtt

appsKey  = "CFB08A20046AB5FCE58158B38359CCF4"
appKey = "2B7E151628AED2A6ABF7158809CF4F3C"
DevAddr = "0033DABF"
MQTT_HOST = "3.19.22.2"
CLIENT_ID =  "centos"
BROKER_PORT = 2883
CA_CERT = "caCert.pem"
CERTFILE = "ServerCert.pem"
KEYFILE = "ServerKey.pem"
MQTT_KEEPALIVE_INTERVAL = 45
publish_topic = "user/3/device/8CF9572000023509/downlink"
subscribe_topic = "user/3/device/8CF9572000023509/uplink"
token = ""

client = mqtt.Client(CLIENT_ID, clean_session=False, userdata=None, transport="tcp")

def on_connect(client, userdata, flags, rc):
    if int(rc) == 0:
        print("Succesful connection")
        client.subscribe("user/3/device/8cf9572000023509/uplink")
    print("Error ! Result code {}".format(rc))

def on_message(client, userdata, msg):
    print(msg.payload)

client = mqtt.Client(CLIENT_ID, clean_session=True, userdata=None, transport="tcp")

client.tls_set(ca_certs=CA_CERT)

client.username_pw_set(username="UamhAqQTzXiOSSgz", password="HjoDgmLMHLsyTwyuyeGfQsKaBSISm")

client.on_connect = on_connect  # Define callback function for successful connection
client.on_message = on_message
client.connect(MQTT_HOST, BROKER_PORT, MQTT_KEEPALIVE_INTERVAL)

