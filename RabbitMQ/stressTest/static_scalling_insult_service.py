import pika
import subprocess
import time
import multiprocessing
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
RABBIT_HOST = 'localhost'
EXCHANGE_NAME = 'new_insults'
NUM_PROCESSES = 10
TOTAL_MESSAGES = 10000
WORKER_COUNTS = [1, 2, 3]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    """Cada proceso abre su propia conexión a RabbitMQ y envía N mensajes."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    for i in range(reqs):
        msg = f"test_insult_{i}"
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=msg)

    connection.close()

def run_sender(total_requests):
    """Distribuye las peticiones entre procesos y mide el tiempo total."""
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def launch_insult_service_instances(n):
    procs = []
    for _ in range(n):
        p = subprocess.Popen(['python3', 'RabbitMQ/InsultService.py'])
        procs.append(p)
    return procs

def terminate_instances(procs):
    for p in procs:
        p.terminate()
        p.wait()

def main():
    print("Static scaling test (InsultService via RabbitMQ)")
    print(f"Total messages: {TOTAL_MESSAGES} | Sender processes: {NUM_PROCESSES}")
    print("Workers | Time (s) | Speedup")

    base_time = None
    times = []
    speedups = []

    for n_workers in WORKER_COUNTS:
        services = launch_insult_service_instances(n_workers)
        time.sleep(5)  # Esperar a que se conecten

        t = run_sender(TOTAL_MESSAGES)

        if base_time is None:
            base_time = t

        sp = base_time / t
        times.append(t)
        speedups.append(sp)

        print(f"{n_workers:^7} | {t:8.3f} | {sp:7.2f}")

        terminate_instances(services)
        time.sleep(2)

    # Gráfico de speedup
    plt.figure()
    plt.plot(WORKER_COUNTS, speedups, marker='o', linestyle='-')
    plt.xlabel('Number of InsultService nodes')
    plt.ylabel('Speedup (T1 / TN)')
    plt.title('Static Scaling: Speedup of InsultService (RabbitMQ)')
    plt.grid(True)
    plt.xticks(WORKER_COUNTS)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
