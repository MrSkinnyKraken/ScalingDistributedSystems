# pyro/InsultService.py
import Pyro4
import time
import random

@Pyro4.expose
@Pyro4.behavior(instance_mode="single") #Orders a singleton
class InsultService(object):
    def __init__(self):
        self.insults = []
        self.subscribers = []

    def add_insult(self, insult):
        if insult not in self.insults:
            self.insults.append(insult)
            return f"Insult '{insult}' added."
        else:
            return f"Insult '{insult}' already exists."

    def get_insults(self):
        return self.insults

    def register_subscriber(self, subscriber_uri):
        if subscriber_uri not in self.subscribers:
            self.subscribers.append(subscriber_uri)
            return f"Subscriber {subscriber_uri} registered."
        else:
            return f"Subscriber {subscriber_uri} already registered."

    def unregister_subscriber(self, subscriber_uri):
        if subscriber_uri in self.subscribers:
            self.subscribers.remove(subscriber_uri)
            return f"Subscriber {subscriber_uri} unregistered."
        else:
            return f"Subscriber {subscriber_uri} not found."

    def broadcast_insult(self):
        """Background thread: every 5 seconds, notify all subscribers with a random insult."""
        while True:
            time.sleep(5)
            if self.insults and self.subscribers:
                insult = random.choice(self.insults)
                print(f"[Broadcast] Sending insult: {insult}")
                # Notify each subscriber by creating a proxy from their URI.
                for sub_uri in self.subscribers:
                    try:
                        subscriber = Pyro4.Proxy(sub_uri)
                        subscriber.notify(insult)
                    except Exception as e:
                        print(f"Failed to notify subscriber {sub_uri}: {e}")

def main():
    # Create the Pyro daemon and locate the Name Server.
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()

    # Create the InsultService instance and register it with the daemon.
    insult_service = InsultService()
    uri = daemon.register(insult_service)
    ns.register("example.insultservice", uri)

    print(f"InsultService is running. URI: {uri}")

    # Enter the request loop.
    daemon.requestLoop()

if __name__ == "__main__":
    main()
