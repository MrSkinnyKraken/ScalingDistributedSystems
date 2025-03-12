from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
from queue import Queue

# Define a simple list of words to filter out.
INSULTS = ["stupid", "idiot", "dumb"]

class InsultFilterService:
    def __init__(self):
        self.queue = Queue()
        self.filtered_results = []
        # Start the worker thread to process texts.
        worker_thread = threading.Thread(target=self.worker, daemon=True)
        worker_thread.start()

    def submit_text(self, text):
        self.queue.put(text)
        return "Text submitted for filtering."

    def get_results(self):
        return self.filtered_results

    def worker(self):
        while True:
            text = self.queue.get()
            filtered_text = text
            for insult in INSULTS:
                filtered_text = filtered_text.replace(insult, "CENSORED")
            self.filtered_results.append(filtered_text)
            self.queue.task_done()

def run_insult_filter_service_server(host="localhost", port=9001):
    server = SimpleXMLRPCServer((host, port), logRequests=True, allow_none=True)
    service = InsultFilterService()
    server.register_instance(service)
    print(f"XMLRPC InsultFilterService running on {host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_insult_filter_service_server()
