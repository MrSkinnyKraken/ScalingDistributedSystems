# InsultFilterService.py
import pika
import threading

class InsultFilterService:
    def __init__(self, rabbit_host='localhost'):
        self.rabbit_host = rabbit_host
        self.insults = ['stupid', 'lazy', 'ugly', 'smelly', 'dumb', 'slow']
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbit_host)
        )
        self.channel = self.connection.channel()

        # Cola de trabajo
        self.channel.queue_declare(queue="insult_raw")
        # QoS: un mensaje a la vez por consumidor
        self.channel.basic_qos(prefetch_count=1)

        # Exchanges (si los necesitas)
        self.channel.exchange_declare(exchange="insult_filtered", exchange_type="fanout")
        self.channel.exchange_declare(exchange="new_insults", exchange_type="fanout")

    def filter_text(self, text):
        for insult in self.insults:
            if insult in text:
                text = text.replace(insult, "CENSORED")
        return text

    def start(self):
        def callback(ch, method, properties, body):
            original = body.decode()
            filtered = self.filter_text(original)
            # Publica el resultado
            ch.basic_publish(exchange='insult_filtered', routing_key='', body=filtered)
            # ACK manual para balancear correctamente
            ch.basic_ack(delivery_tag=method.delivery_tag)

        print("[Filter] Waiting for insults to filter...")
        self.channel.basic_consume(
            queue="insult_raw",
            on_message_callback=callback,
            auto_ack=False
        )
        self.channel.start_consuming()

def main():
    service = InsultFilterService()
    service.start()

if __name__ == "__main__":
    main()
