import redis

class InsultServiceClient:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.pubsub_channel = "insult_broadcast"

    def listen_for_insults(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.pubsub_channel)
        print("Listening for insults...")
        for message in pubsub.listen():
            if message['type'] == 'message':
                print(f"Received insult: {message['data']}")

def main():
    client = InsultServiceClient()
    client.listen_for_insults()

if __name__ == "__main__":
    main()