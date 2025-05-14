# static_scaling_insult_filter.py
# for test correctly the stresstests,first purge the RabbitMQ queue
#  http://localhost:15672 --> Queues -- > insult_raw -- > Purgue
# ─────────────────────────────────────────────────────────────────────────
import pika
import subprocess
import time
import multiprocessing
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
RABBIT_HOST     = 'localhost'
QUEUE_NAME      = 'insult_raw'
NUM_PROCESSES   = 10
TOTAL_MESSAGES  = 100000
WORKER_COUNTS   = [1, 2, 3]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    """Envia N mensajes insult_raw."""
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    ch   = conn.channel()
    for i in range(reqs):
        msg = f"stupid insult {i}"
        ch.basic_publish(exchange='', routing_key=QUEUE_NAME, body=msg)
    conn.close()

def run_sender(total_requests):
    per = total_requests // NUM_PROCESSES
    tasks = [per] * NUM_PROCESSES
    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - start

def launch_workers(n):
    procs = []
    for _ in range(n):
        p = subprocess.Popen(['python3', 'RabbitMQ/InsultFilterService.py'])
        procs.append(p)
    return procs

def terminate_workers(procs):
    for p in procs:
        p.terminate()
        p.wait()

def wait_until_empty():
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    ch   = conn.channel()
    while True:
        q = ch.queue_declare(queue=QUEUE_NAME, passive=True)
        if q.method.message_count == 0:
            break
        time.sleep(0.05)
    conn.close()

def main():
    base = None
    times = []
    speedups = []

    print("Static scaling test (InsultFilterService via RabbitMQ)")
    print(f"Total messages: {TOTAL_MESSAGES} | Sender processes: {NUM_PROCESSES}")
    print("Workers | Time (s) | Speedup")

    for n in WORKER_COUNTS:
        # Arrancar n filtros
        workers = launch_workers(n)
        time.sleep(3)  # dejar que se suscriban

        # Enviar + esperar a vaciar cola
        start = time.time()
        run_sender(TOTAL_MESSAGES)
        wait_until_empty()
        elapsed = time.time() - start

        if base is None:
            base = elapsed
        sp = base / elapsed

        print(f"{n:^7} | {elapsed:8.3f} | {sp:7.2f}")
        times.append(elapsed)
        speedups.append(sp)

        terminate_workers(workers)
        time.sleep(1)

    # Gráfico
    plt.plot(WORKER_COUNTS, speedups, marker='o')
    plt.xlabel('Number of InsultFilterService nodes')
    plt.ylabel('Speedup (T1 / TN)')
    plt.title('Static Scaling: Speedup of InsultFilterService (RabbitMQ)')
    plt.grid(True)
    plt.xticks(WORKER_COUNTS)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
