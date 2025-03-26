# pyro/client/FilterClient.py
import Pyro4

def main():
    # Locate the Pyro Name Server
    ns = Pyro4.locateNS()
    
    # Retrieve the URI for the InsultFilterService
    filter_uri = ns.lookup("example.insultfilter")
    insult_filter = Pyro4.Proxy(filter_uri)

    # Submit texts containing insults
    print(insult_filter.submit_text("This is a stupid mistake"))
    print(insult_filter.submit_text("You are an idiot and dumb"))

    # Retrieve and print filtered results
    results = insult_filter.get_results() #dynamically this method triggers process_queue to simulate the behaviour of a working queue.
    print("Filtered results:")
    for res in results:
        print(res)

if __name__ == "__main__":
    main()
