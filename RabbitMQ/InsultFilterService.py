import pika
import threading

class InsultFilterService:
    def __init__(self, rabbit_host='localhost'):
        self.rabbit_host = rabbit_host
        self.insults = ['stupid', 'lazy', 'ugly', 'smelly', 'dumb', 'slow']
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_host))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue="insult_raw")
        self.channel.exchange_declare(exchange="insult_filtered", exchange_type="fanout")
        self.channel.exchange_declare(exchange="new_insults", exchange_type="fanout")

    def filter_text(self, text):
        for insult in self.insults:
            if insult in text:
                print(f"[Filter] Found insult: {insult}")
                text = text.replace(insult, "CENSORED")
        return text

    def listen_for_new_insults(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_host))
        channel = connection.channel()
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='new_insults', queue=queue_name)

        def callback(ch, method, properties, body):
            insult = body.decode()
            if insult not in self.insults:
                self.insults.append(insult)
                print(f"[Filter] New insult added: {insult}")
            else:
                print(f"[Filter] Insult already exists: {insult}")

        print("[Filter] Listening for new insults...")
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    def start(self):
        def callback(ch, method, properties, body):
            original = body.decode()
            filtered = self.filter_text(original)
            print(f"[Filter] Sending filtered insult: {filtered}")
            self.channel.basic_publish(exchange='insult_filtered', routing_key='', body=filtered)

        print("[Filter] Waiting for insults to filter...")
        self.channel.basic_consume(queue="insult_raw", on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()

def main():
    service = InsultFilterService()
    t1 = threading.Thread(target=service.listen_for_new_insults, daemon=True)
    t2 = threading.Thread(target=service.start)

    t1.start()
    t2.start()
    t2.join()

if __name__ == "__main__":
    main()
