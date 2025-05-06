import redis
import time
import random

class InsultService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insult_key = "insults"
        self.pubsub_channel = "insult_broadcast"

    def add_insult(self, insult):
        if not self.redis.sismember(self.insult_key, insult):
            self.redis.sadd(self.insult_key, insult)
            return f"Insult '{insult}' added."
        return f"Insult '{insult}' already exists."

    def get_insults(self):
        return list(self.redis.smembers(self.insult_key))

    def broadcast_insult(self):
        while True:
            insults = self.get_insults()
            if insults:
                random_insult = random.choice(insults)
                self.redis.publish(self.pubsub_channel, random_insult)
                print(f"[Broadcast] Sending insult: {random_insult}")
            time.sleep(5)

def main():
    service = InsultService()

    service.broadcast_insult()

if __name__ == "__main__":
    main()