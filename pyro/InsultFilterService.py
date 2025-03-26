# pyro/insult_filter_service.py
import Pyro4
from queue import Queue

# List of insult words to censor.
INSULTS = ["stupid", "idiot", "dumb"]

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultFilterService(object):
    def __init__(self):
        self.queue = Queue()
        self.filtered_results = []

    def submit_text(self, text):
        self.queue.put(text)
        return "Text submitted for filtering."

    def get_results(self):
        self.process_queue() #manually trigger process_queue to simulate the behaviour of a working queue.
        return self.filtered_results

    def process_queue(self):
        """Process texts from the queue until there's no text left."""
        while not self.queue.empty():
            text = self.queue.get()
            filtered_text = text
            for insult in INSULTS:
                filtered_text = filtered_text.replace(insult, "CENSORED")
            self.filtered_results.append(filtered_text)
            print(f"Processed text: {filtered_text}")
            self.queue.task_done()
        return f"Queue processed"

def main():
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()

    filter_service = InsultFilterService()
    uri = daemon.register(filter_service)
    ns.register("example.insultfilter", uri)

    print(f"InsultFilterService is running. URI: {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    main()
