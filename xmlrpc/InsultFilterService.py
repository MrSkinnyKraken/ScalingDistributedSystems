from xmlrpc.server import SimpleXMLRPCServer
from queue import Queue

# Define a simple list of words to filter out.
INSULTS = ["stupid", "idiot", "dumb"]

class InsultFilterService:
    def __init__(self):
        self.queue = Queue()
        self.filtered_results = []

    def submit_text(self, text):
        self.queue.put(text)
        return "Text submitted for filtering."

    def process_queue(self):
        # Process all texts in the queue synchronously.
        while not self.queue.empty():
            text = self.queue.get()
            filtered_text = text
            for insult in INSULTS:
                filtered_text = filtered_text.replace(insult, "CENSORED")
            self.filtered_results.append(filtered_text)
            self.queue.task_done()
        return "Queue processed."

    def get_results(self):
        # Process any pending tasks before returning results.
        self.process_queue()
        return self.filtered_results

def run_insult_filter_service_server(host="localhost", port=9001):
    server = SimpleXMLRPCServer((host, port), logRequests=True, allow_none=True)
    service = InsultFilterService()
    server.register_instance(service)
    print(f"XMLRPC InsultFilterService running on {host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_insult_filter_service_server()
