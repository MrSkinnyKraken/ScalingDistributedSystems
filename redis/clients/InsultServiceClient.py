# inultServiceClient.py
import redis

def main():
    r = redis.Redis(decode_responses=True)
    while True:
        insult = input("Enter a new insult: ").strip()
        if insult:
            r.publish('new_insults', insult)
            print(f"[Client] Published insult: {insult}")

if __name__ == "__main__":
    main()
