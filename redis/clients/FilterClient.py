# filterClient.py
import redis

def main():
    r = redis.Redis(decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe('filtered_insults')

    print("[Client] Listening for filtered texts...")
    for message in pubsub.listen():
        if message['type'] == 'message':
            print(f"[Client] Received: {message['data']}")

if __name__ == "__main__":
    main()
