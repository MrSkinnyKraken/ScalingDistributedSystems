import xmlrpc.client

def main():
    server_url = "http://localhost:9000"
    proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)
    
    # Add insults
    print(proxy.add_insult("You're an idiot"))
    print(proxy.add_insult("You're an idiot"))  # Testing duplicate
    print(proxy.add_insult("You look stupid"))
    
    # Retrieve insults
    insults = proxy.get_insults()
    print("Current insults:")
    for insult in insults:
        print(insult)
    
    # Example: Register as a subscriber.
    # (Assuming your client implements its own XMLRPC server with a notify method.)
    subscriber_url = "http://localhost:9002"
    print(proxy.register_subscriber(subscriber_url))

if __name__ == "__main__":
    main()
