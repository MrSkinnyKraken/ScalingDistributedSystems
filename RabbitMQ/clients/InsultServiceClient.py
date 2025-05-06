import pika

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='new_insults', exchange_type='fanout')

    while True:
        insult = input("Enter a new insult to add: ").strip()
        if insult:
            channel.basic_publish(exchange='new_insults', routing_key='', body=insult)
            print(f"[Client] Sent insult: {insult}")

if __name__ == "__main__":
    main()
