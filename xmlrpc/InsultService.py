from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import time
import random
import argparse

class InsultService:
    def __init__(self):
        self.insults = ['stupid', 'lazy', 'ugly', 'smelly', 'dumb', 'slow']
        self.subscribers = []

    def add_insult(self, insult):
        #this method adds an insult to the list of insults only if the insult is not already in the list
        if insult not in self.insults:
            self.insults.append(insult)
            return f"Insult {insult} added to the list"
        else:
            return f"Insult {insult} already in the list"
    
    def get_insults(self):
        #this method returns the list of insults
        return self.insults
        
    def register_subscriber(self, subscriber):
        self.subscribers.append(subscriber)
        return f"Subscriber {subscriber} registered"
    
    def register_subscriber(self, subscriber_url):
        #this method registers a subscriber to the list of subscribers
        if subscriber_url not in self.subscribers:
            self.subscribers.append(subscriber_url)
            return f"Subscriber '{subscriber_url}' registered."
        else:
            return f"Subscriber '{subscriber_url}' already registered."
    
    def unregister_subscriber(self, subscriber_url):
        #this method unregisters a subscriber from the list of subscribers
        if subscriber_url in self.subscribers:
            self.subscribers.remove(subscriber_url)
            return f"Subscriber '{subscriber_url}' unregistered."
        else:
            return f"Subscriber '{subscriber_url}' not found."

    def broadcast_insult(self):
        # This background method notifies all subscribers every 5 seconds
        while True:
            time.sleep(5)
            if self.insults and self.subscribers:
                insult = random.choice(self.insults)
                print(f"Broadcasting insult: {insult}")
                for subscriber_url in self.subscribers:
                    try:
                        import xmlrpc.client
                        proxy = xmlrpc.client.ServerProxy(subscriber_url, allow_none=True)
                        proxy.notify(insult)
                    except Exception as e:
                        print(f"Failed to notify subscriber {subscriber_url}: {e}")

def run_insult_service_server(host: str, port: int):
    server = SimpleXMLRPCServer((host, port), logRequests=True, allow_none=True)
    service = InsultService()
    server.register_instance(service)
    print(f"XMLRPC InsultService running on {host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run XMLRPC InsultService")
    p.add_argument("--host", default="localhost", help="Host to bind")
    p.add_argument("--port", type=int, default=9000, help="Port to bind")
    args = p.parse_args()
    run_insult_service_server(host=args.host, port=args.port)