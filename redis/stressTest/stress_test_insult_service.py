# stress_test_insult_service_redis.py
import redis
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────
REDIS_HOST = 'localhost'
CHANNEL_NAME = 'new_insults'
NUM_PROCESSES = 10
REQUEST_STEPS = [100, 1000, 10000, 100000, 1000000, 10000000]
# ─────────────────────────────────────────────────────────────────────────

def send_requests(reqs):
    r = redis.Redis(host=REDIS_HOST, decode_responses=True)
    pipe = r.pipeline()
    for i in range(reqs):
        msg = f"stress_insult_{i}"
        pipe.publish(CHANNEL_NAME, msg)
        if i % 500 == 0:   # cada 1000 comandos, enivamos el pipeline con 1000 comandos a la vez, 
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

    print("Single-node throughput test (InsultService via Redis)")
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
    plt.plot(REQUEST_STEPS, throughputs, marker='s', label="InsultService (Redis)")
    plt.xscale('log')
    plt.xlabel('Total insults published')
    plt.ylabel('Throughput (messages/sec)')
    plt.title('Single-node InsultService Throughput vs Load (Redis)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
