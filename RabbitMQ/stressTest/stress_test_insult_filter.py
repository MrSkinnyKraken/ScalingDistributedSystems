#stress_test_insult_filter.py
import pika
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
RABBIT_HOST = 'localhost'
QUEUE_NAME = 'insult_raw'  
NUM_PROCESSES = 10
REQUEST_STEPS = [100,1000, 10000, 100000, 1000000]  # Total de mensajes a enviar
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

    print("Single-node throughput test (InsultFilterService via RabbitMQ)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|--------------------")

    for total in REQUEST_STEPS:
        t = run(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:15.1f}")

    plt.figure()
    plt.plot(REQUEST_STEPS, throughputs, marker='s', label="FilterService")
    plt.xscale('log')
    plt.xlabel('Total texts submitted')
    plt.ylabel('Throughput (texts processed/sec)')
    plt.title('Single-node InsultFilterService Throughput vs Load (RabbitMQ)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
