# InsultFilterService.py
import redis
import threading

class InsultFilterService:
    def __init__(self, host='localhost', port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        self.insults = set(self.redis.smembers('INSULTS'))

    def filter_text(self, text):
        for insult in self.insults:
            if insult in text:
                print(f"[Filter] Found insult: {insult}")
                text = text.replace(insult, "CENSORED")
        return text

    def process_texts(self):
        print("[Filter] Waiting for texts...")
        while True:
            _, text = self.redis.brpop('insult_raw')
            filtered = self.filter_text(text)
            print(f"[Filter] Filtered text: {filtered}")
            self.redis.publish('filtered_insults', filtered)

    def listen_for_new_insults(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe('new_insults')

        print("[Filter] Listening for new insults...")
        for message in pubsub.listen():
            if message['type'] == 'message':
                insult = message['data']
                if insult not in self.insults:
                    self.insults.add(insult)
                    print(f"[Filter] New insult added: {insult}")

def main():
    service = InsultFilterService()
    t1 = threading.Thread(target=service.listen_for_new_insults, daemon=True)
    t2 = threading.Thread(target=service.process_texts)
    
    t1.start()
    t2.start()
    t2.join()


if __name__ == "__main__":
    main()
