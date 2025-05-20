import random
import redis
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
QUEUE_NAME = 'insult_raw'  
NUM_PROCESSES = 10
REQUEST_STEPS = [1000, 10000, 100000, 10000, 1000, 100, 10]
WORKER_KEY = 'active_workers'  # Clave Redis para número de workers
# ──────────────────────────────────────────────────────────────────────────

# Listas para almacenar resultados
throughputs = []
worker_counts = []
times = []

def send_requests(reqs):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    pipe = r.pipeline()
    for i in range(reqs):
        text = f"This is a stupid mistake {i}"
        pipe.lpush(QUEUE_NAME, text)
        if i % 1000 == 0:
            pipe.execute()
    pipe.execute()

def run(total_requests):
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES
    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    return time.time() - start

def real_workers(connection):
    # Convertir a entero, usar 0 si no existe la clave
    return int(connection.get(WORKER_KEY))

def main():
    connection = redis.Redis(host=REDIS_HOST, decode_responses=True)
    connection.ltrim(QUEUE_NAME, 1, 0)

    print("Stress test (InsultFilterService via Redis)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("Press Ctrl+C or click the trash to kill the test.")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|--------------------")

    t_start = time.time()

    for reqs in REQUEST_STEPS:
        # Esperar a que la cola esté vacía
        while connection.llen(QUEUE_NAME) > 0:
            time.sleep(0.5)

        now = time.time() - t_start

        # Enviar peticiones
        t = run(reqs)
        tp = reqs / t
        throughputs.append(tp)
        # Obtener y registrar el número de workers
        workers = real_workers(connection)
        worker_counts.append(workers)
        times.append(now)

        print(f"{reqs:8d} | {t:8.3f} | {tp:15.1f}")
    time.sleep(5)  # Esperar para que se estabilice el último worker
    # ── Gráfica ──────────────────────────────────────────────────────────
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    # Ejes con colores distintos
    ax1.plot(times, worker_counts, 'g-o', label='Worker count')   # Eje izquierdo
    ax2.plot(times, throughputs, 'b-s', label='Throughput (req/sec)')  # Eje derecho

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Worker count', color='g')
    ax2.set_ylabel('Throughput (req/sec)', color='b')

    ax1.set_ylim(0, max(worker_counts))  # Eje izquierdo fijo entre 0-100 workers
    if throughputs:
        ax2.set_ylim(0, max(throughputs) * 1.2)  # Escala dinámica del eje derecho

    ax1.grid(True)
    plt.title('Dynamic-Scaling Redis InsultService: Workers & Throughput Over Time')

    # Leyenda combinada
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
