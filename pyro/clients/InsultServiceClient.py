# pyro/client/InsultServiceClient.py
import Pyro4

def main():
    # Locate the Pyro Name Server
    ns = Pyro4.locateNS()
    
    # Retrieve the URI for the InsultService
    service_uri = ns.lookup("example.insultservice")
    insult_service = Pyro4.Proxy(service_uri)

    # Add insults
    print(insult_service.add_insult("You're an idiot"))
    print(insult_service.add_insult("You look stupid"))
    print(insult_service.add_insult("This is a dumb idea"))

    # Retrieve insults
    insults = insult_service.get_insults()
    print("\nCurrent insults stored in the service:")
    for insult in insults:
        print(f"- {insult}")

if __name__ == "__main__":
    main()
