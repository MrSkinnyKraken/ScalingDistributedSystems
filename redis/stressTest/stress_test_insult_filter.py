# stress_test_insult_filter_redis.py
import redis
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
LIST_NAME = 'insult_raw'
NUM_PROCESSES = 10
REQUEST_STEPS = [100, 1000, 10000, 100000, 1000000, 10000000]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    r = redis.Redis(host='localhost', decode_responses=True)
    pipe = r.pipeline()
    for i in range(reqs):
        msg = f"This is a stupid mistake {i}"
        pipe.lpush(LIST_NAME, msg)
        if i % 1000 == 0:   # cada 1000 comandos, enivamos el pipeline con 1000 comandos a la vez, 
            pipe.execute()  # en vez de uno a uno para mejorar el rendimiento bruscamente
    pipe.execute()  # ejecutar lo que quede


def run(total_requests):
    per_process = total_requests // NUM_PROCESSES
    tasks = [per_process] * NUM_PROCESSES

    start = time.time()
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(send_requests, tasks)
    end = time.time()
    return end - start

def main():
    throughputs = []

    print("Single-node throughput test (InsultFilterService via Redis)")
    print(f"Concurrency (processes): {NUM_PROCESSES}")
    print("TotalReq | Time (s) | Throughput (req/s)")
    print("---------|----------|--------------------")

    for total in REQUEST_STEPS:
        t = run(total)
        tp = total / t
        throughputs.append(tp)
        print(f"{total:8d} | {t:8.3f} | {tp:15.1f}")

    # Gráfico
    plt.figure()
    plt.plot(REQUEST_STEPS, throughputs, marker='o', label="FilterService (Redis)")
    plt.xscale('log')
    plt.xlabel('Total requests issued')
    plt.ylabel('Throughput (requests/sec)')
    plt.title('Single-node InsultFilterService Throughput vs Load (Redis)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
