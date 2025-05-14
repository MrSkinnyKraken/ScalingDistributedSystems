# InsultFilterService.py
import redis
import threading
import time

class InsultFilterService:
    def __init__(self, host='localhost', port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        self.insults = set(self.redis.smembers('INSULTS'))

    def filter_text(self, text):
        for insult in list(self.insults):  # copia inmutable
            if insult in text:
                print(f"[Filter] Found insult: {insult}")
                text = text.replace(insult, "CENSORED")
        return text

    def process_texts(self):
        print("[Filter] Waiting for texts...")
        while True:
            try:                                            # try catch para manejar la desconexión de redis por saturacion (+1M de mensajes)
                _, text = self.redis.blpop('insult_raw')
                filtered = self.filter_text(text)
                print(f"[Filter] Filtered text: {filtered}")
                self.redis.publish('filtered_insults', filtered)
            except redis.exceptions.ConnectionError:
                print("[Filter] Redis connection lost. Reconnecting...")
                time.sleep(1)

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
    service = InsultFilterService()
    t1 = threading.Thread(target=service.process_new_insults, daemon=True)
    t2 = threading.Thread(target=service.process_texts)

    t1.start()
    t2.start()
    t2.join()

if __name__ == "__main__":
    main()
