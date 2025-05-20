import pika
import time
import random
import threading

class InsultService:
    def __init__(self, rabbit_host='localhost'):
        self.rabbit_host = rabbit_host
        self.insults = ['stupid', 'lazy', 'ugly', 'smelly', 'dumb', 'slow']
        
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_host))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue="insult_raw", durable=True)
        self.channel.exchange_declare(exchange="new_insults", exchange_type="fanout")

    def broadcast_insult(self):
        while True:
            time.sleep(5)
            insult = random.choice(self.insults)
            print(f"[Service] Broadcasting insult: {insult}")
            self.channel.basic_publish(exchange='', routing_key="insult_raw", body=insult)

    def listen_for_new_insults(self):
        # conexión separada para escuchar nuevos insultos
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_host))
        channel = connection.channel()

        # Crear cola exclusiva para este consumidor (fanout)
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='new_insults', queue=queue_name)

        def callback(ch, method, properties, body):
            insult = body.decode()
            if insult not in self.insults:
                self.insults.append(insult)
                print(f"[Service] New insult added: {insult}")
            else:
                print(f"[Service] Insult already exists: {insult}")

        print("[Service] Listening for new insults...")
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

def main():
    service = InsultService()
    t1 = threading.Thread(target=service.broadcast_insult, daemon=True)
    t2 = threading.Thread(target=service.listen_for_new_insults)

    t1.start()
    t2.start()
    t2.join()

if __name__ == "__main__":
    main()
