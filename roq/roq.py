import os
import pickle
import paho.mqtt.client as mqtt

_client = None
_config = None

def check_init(fn):
    def wrapper(*args, **kwargs):
        global _client
        if _client is None:
            raise Exception("roq.init() must be called before using any other roq functions")
        return fn(*args, **kwargs)
    return wrapper

def on_connect(client, userdata, flags, reason_code, properties):
    global _config
    if reason_code != 0 and _config["fail_on_connect"]:
        raise Exception(f"Connection failed with reason code {reason_code}")

def on_message(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")


def init(
        *,
        host,
        port,
        keepalive=60,
        username=None,
        password=None,
        transport="tcp",
        tls=False,
        client=None,
        fail_on_connect=True
    ):
        global _client
        global _config
    
        if client is not None:
            if username is not None or password is not None or transport is not None or tls is not None:
                raise Exception("If you pass a paho.mqtt.client.Client, you cannot pass any configuration argument")
            _client = client
        else:
            _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport=transport)
            if tls:
                _client.tls_set()
            if username is not None and password is not None:
                _client.username_pw_set(username, password)
            
        _client.on_connect = on_connect
        _client.on_message = on_message
        _client.connect(host, port, keepalive)

        _config = dict(
            fail_on_connect=fail_on_connect,
            bindings=dict()
        )

@check_init
def serve():
    global _client
    _client.loop_forever()

@check_init
def procedure(topic):
    global _config

    if topic in _config["bindings"]:
        raise Exception(f"Topic {topic} is already bound to a procedure")

    receive_topic = os.path.join(topic, "args")
    return_topic = os.path.join(topic, "return")
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return_value = fn(*args, **kwargs)
            payload = pickle.dumps(return_value)
            _client.publish(return_topic, payload)
        
        _client.subscribe(receive_topic)
        _config["bindings"][topic] = wrapper

    return decorator