import pika
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
RABBIT_HOST = 'localhost'
QUEUE_NAME = 'new_insults'
NUM_PROCESSES = 10
REQUEST_STEPS = [100,1000, 10000, 100000, 1000000]  # Total de mensajes a enviar
# ──────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    """Cada proceso abre su propia conexión a RabbitMQ y envía N mensajes."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    for i in range(reqs):
        msg = f"test_insult_{i}"
        channel.basic_publish(exchange='new_insults', routing_key='', body=msg)

    connection.close()

def run(total_requests):
    """Distribuye las peticiones entre los procesos y mide el tiempo total."""
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def main():
    throughputs = []
    times = []

    print("Single-node throughput test (InsultService via RabbitMQ)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")

    for total in REQUEST_STEPS:
        t = run(total)
        tp = total / t
        times.append(t)
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:8.1f}")

    # Gráfico de throughput
    plt.figure()
    plt.plot(REQUEST_STEPS, throughputs, marker='o')
    plt.xscale('log')
    plt.xlabel('Total requests issued')
    plt.ylabel('Throughput (requests/sec)')
    plt.title('Single-node InsultService Throughput vs Load (RabbitMQ)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
