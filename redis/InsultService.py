# InsultService.py
import redis
import time
import threading
import random

class InsultService:
    def __init__(self, host='localhost', port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        self.insults = ['stupid', 'lazy', 'ugly', 'smelly', 'dumb', 'slow']
        self.redis.delete('INSULTS')

        for insult in self.insults:
            self.redis.sadd('INSULTS', insult)

    def broadcast_insult(self):
        while True:
            time.sleep(5)
            insult = random.choice(self.insults)
            print(f"[Service] Sending insult to filter: {insult}")
            self.redis.lpush('insult_raw', insult)

    def process_new_insults(self):
        print("[Service] Waiting for new insults...")
        while True:
            try:
                pubsub = self.redis.pubsub()
                pubsub.subscribe('new_insults')  # Subscribe to the 'new_insults' channel
                for message in pubsub.listen():
                    if message['type'] == 'message':  # Process only actual messages
                        insult = message['data']
                        if not self.redis.sismember('INSULTS', insult):
                            self.redis.sadd('INSULTS', insult)
                            self.insults.append(insult)
                            print(f"[Service] New insult added: {insult}")
            except redis.exceptions.ConnectionError:
                print("[Service] Redis connection lost. Reconnecting...")
                time.sleep(1)  # Wait before reconnecting


def main():
    service = InsultService()
    t1 = threading.Thread(target=service.broadcast_insult, daemon=True)
    t2 = threading.Thread(target=service.process_new_insults)

    t1.start()
    t2.start()
    t2.join()

if __name__ == "__main__":
    main()
