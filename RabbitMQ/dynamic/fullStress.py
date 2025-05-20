import pika
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ──────────────────────────────────────────────
QUEUE_NAME = 'insult_raw'
NUM_PROCESSES = 10
REQUEST_STEPS = [1000, 10000, 100000, 10000, 1000, 100, 10]
# ───────────────────────────────────────────────────────────────

# Listas para almacenar resultados
throughputs = []
worker_counts = []
times = []

def send_requests(n_requests):
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = conn.channel()

    for i in range(n_requests):
        text = f"This is a stupid mistake {i}"
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=text
        )
    conn.close()

def run(total_requests):
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES
    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - start

def get_backlog():
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = conn.channel()
    queue = channel.queue_declare(queue=QUEUE_NAME, passive=True)
    count = queue.method.message_count
    conn.close()
    return count

def get_workers():
    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = conn.channel()
    queue = channel.queue_declare(queue=QUEUE_NAME, passive=True)
    workers = int(queue.method.consumer_count) 
    conn.close()
    return workers

def wait_until_empty():
    while get_backlog() > 0:
        time.sleep(0.5)

def main():
    print("Stress test (InsultFilterService via RabbitMQ)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("Press Ctrl+C or click the trash to kill the test.")
    print("TotalReq | Time (s) | Throughput (req/s)")

    t_start = time.time()

    for reqs in REQUEST_STEPS:
        wait_until_empty()
        now = time.time() - t_start

        t = run(reqs)
        workers = get_workers()
        tp = reqs / t
        throughputs.append(tp)
        workers = get_workers()
        worker_counts.append(workers)
        times.append(now)

        print(f"{reqs:8d} | {t:8.3f} | {tp:15.1f}")

    time.sleep(5)  # estabiliza workers finales

    # ── Gráfica ────────────────────────────────────────────────
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    ax1.plot(times, worker_counts, 'g-o', label='Worker count')   # Eje izq.
    ax2.plot(times, throughputs, 'b-s', label='Throughput (req/s)')  # Eje der.

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Worker count', color='g')
    ax2.set_ylabel('Throughput (req/s)', color='b')

    ax1.set_ylim(0, max(worker_counts) + 1)
    if throughputs:
        ax2.set_ylim(0, max(throughputs) * 1.2)

    ax1.grid(True)
    plt.title('Dynamic-Scaling RabbitMQ InsultService: Workers & Throughput Over Time')

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
