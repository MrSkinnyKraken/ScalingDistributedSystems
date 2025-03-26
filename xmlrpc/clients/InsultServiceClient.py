import xmlrpc.client

def main():
    server_url = "http://localhost:9000"
    proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)
    
    # Add insults
    print(proxy.add_insult("You're an idiot"))
    print(proxy.add_insult("You're an idiot"))  # Testing duplicate
    print(proxy.add_insult("You look stupid"))
    
    # Retrieve insults
    insults = proxy.get_insults() #dynamically this method triggers process_queue to simulate the behaviour of a working queue.
    print("Current insults:")
    for insult in insults:
        print(insult)
    
    # Example: Register as a subscriber.
    subscriber_url = "http://localhost:9002"
    print(proxy.register_subscriber(subscriber_url))

if __name__ == "__main__":
    main()
