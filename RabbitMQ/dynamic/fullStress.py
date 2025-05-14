#stress_test_insult_filter.py
import random
import pika
import multiprocessing
import time


# ── Configuración ─────────────────────────────────────────────────────────
RABBIT_HOST = 'localhost'
QUEUE_NAME = 'insult_raw'  
NUM_PROCESSES = 10
REQUEST_STEPS = [100,1000, 10000, 100000]  # Total de mensajes a enviar
# ──────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    """Cada proceso envía reqs mensajes de texto que contienen posibles insultos."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    for i in range(reqs):
        text = f"This is a stupid mistake {i}"
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=text)

    connection.close()

def run(total_requests):
    """Distribuye las peticiones entre los procesos y mide el tiempo de envío total."""
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def main():
    throughputs = []
    # Check if the RabbitMQ queue is empty
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    queue = channel.queue_declare(queue=QUEUE_NAME, passive=True)
    channel.queue_purge(queue=QUEUE_NAME) # Clear the queue before starting
    print("Single-node throughput test (InsultFilterService via RabbitMQ)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("Press Cntrl+C or click the trash to kill the test.")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|--------------------")
    while True:
        message_count = queue.method.message_count
        connection.close()

        if message_count == 0:
            reqs = random.choice(REQUEST_STEPS)
            t = run(reqs)
            tp = reqs / t
            throughputs.append(tp)
            print(f"{reqs:8d} | {t:8.3f} | {tp:15.1f}")


if __name__ == "__main__":
    main()
