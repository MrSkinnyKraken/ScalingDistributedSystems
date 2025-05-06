import redis

class FilterClient:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.filtered_key = "filtered_texts"

    def get_filtered_texts(self):
        return list(self.redis.lrange(self.filtered_key, 0, -1))

def main():
    client = FilterClient()
    print("Retrieved filtered texts:", client.get_filtered_texts())

if __name__ == "__main__":
    main()