import xmlrpc.client
import time

def main():
    server_url = "http://localhost:9001"
    proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)
    
    # Submit texts for filtering
    print(proxy.submit_text("This is a stupid mistake"))
    print(proxy.submit_text("You are an idiot and dumb"))
    
    # Wait a bit for the worker to process the texts
    time.sleep(2)
    
    results = proxy.get_results()
    print("Filtered texts:")
    for res in results:
        print(res)

if __name__ == "__main__":
    main()
