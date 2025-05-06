import redis

INSULTS = ["stupid", "idiot", "dumb"]

class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.filtered_key = "filtered_texts"

    def submit_text(self, text):
        for insult in INSULTS:
            text = text.replace(insult, "CENSORED")
        self.redis.rpush(self.filtered_key, text)
        return "Text submitted for filtering."

    def get_results(self):
        return list(self.redis.lrange(self.filtered_key, 0, -1))

def main():
    filter_service = InsultFilterService()
    filter_service.submit_text("This is a stupid mistake.")
    print("Filtered results:", filter_service.get_results())

if __name__ == "__main__":
    main()