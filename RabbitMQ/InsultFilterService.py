import pika
import threading
import time

class InsultFilterService:
    def __init__(self, rabbit_host='localhost'):
        self.rabbit_host = rabbit_host
        self.insults = ['stupid', 'lazy', 'ugly', 'smelly', 'dumb', 'slow']

        # Conexiones y canales separados para cada thread
        self.connection_filter = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbit_host)
        )
        self.channel_filter = self.connection_filter.channel()
        self.channel_filter.queue_declare(queue="insult_raw", durable=True)
        self.channel_filter.basic_qos(prefetch_count=1)

        self.connection_new = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbit_host)
        )
        self.channel_new = self.connection_new.channel()
        self.channel_new.exchange_declare(exchange="new_insults", exchange_type="fanout")
        self.queue_new = self.channel_new.queue_declare(queue='', exclusive=True).method.queue
        self.channel_new.queue_bind(exchange="new_insults", queue=self.queue_new)

        self.lock = threading.Lock()  # Para acceso concurrente a la lista insults

    def filter_text(self, text):
        with self.lock:
            insults_copy = list(self.insults)
        for insult in insults_copy:
            if insult in text:
                text = text.replace(insult, "CENSORED")
        return text

    def process_texts(self):
        def callback(ch, method, properties, body):
            original = body.decode()
            filtered = self.filter_text(original)
            print(f"[Filter] Original: {original} | Filtered: {filtered}")
            ch.basic_publish(exchange='insult_filtered', routing_key='', body=filtered)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        print("[Filter] Waiting for insults to filter...")
        self.channel_filter.basic_consume(
            queue="insult_raw",
            on_message_callback=callback,
            auto_ack=False
        )
        self.channel_filter.start_consuming()

    def process_new_insults(self):
        def callback(ch, method, properties, body):
            insult = body.decode()
            with self.lock:
                if insult not in self.insults:
                    self.insults.append(insult)
                    print(f"[Service] New insult added: {insult}")

        print("[Service] Waiting for new insults...")
        self.channel_new.basic_consume(
            queue=self.queue_new,
            on_message_callback=callback,
            auto_ack=True
        )
        self.channel_new.start_consuming()

def main():
    service = InsultFilterService()
    t1 = threading.Thread(target=service.process_new_insults, daemon=True)
    t2 = threading.Thread(target=service.process_texts)

    t1.start()
    t2.start()
    t2.join()

if __name__ == "__main__":
    main()
