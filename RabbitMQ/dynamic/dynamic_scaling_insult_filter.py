# dynamic_scaling_rabbitmq.py
import pika
import subprocess
import time
import math

# ── Configuración ─────────────────────────────────────────────────────────
RABBIT_HOST   = 'localhost'
QUEUE_NAME    = 'insult_raw'
T_PROCESS     = 0.001             # tiempo medio de filtrar un mensaje (s/msg)
C_WORKER      = 1 / T_PROCESS
T_RESPONSE    = 1.0
MAX_WORKERS   = 100
MIN_WORKERS   = 1
SCALE_INTERVAL= 0.5            # intervalo de escalado (s)
# ─────────────────────────────────────────────────────────────────────────

def start_filter():
    return subprocess.Popen(
        ['python3', 'RabbitMQ/InsultFilterService.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def terminate(p):
    p.terminate()
    p.wait()

def get_backlog():
    conn = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
    ch = conn.channel()
    q = ch.queue_declare(queue=QUEUE_NAME, passive=True)
    conn.close()
    return q.method.message_count

def dynamic_scale():
    workers = []
    try:
        while True:
            B = get_backlog()
            ArrivalRate = B / SCALE_INTERVAL  # aproximación

            N_req = math.ceil((B + ArrivalRate * T_RESPONSE) / C_WORKER)
            N_req = min(max(N_req, MIN_WORKERS), MAX_WORKERS)

            delta = N_req - len(workers)
            if delta > 0:
                for _ in range(delta):
                    workers.append(start_filter())
                print(f"[Scale-Up] Launched {delta} workers (total {len(workers)})")
            elif delta < 0:
                for _ in range(-delta):
                    terminate(workers.pop())
                print(f"[Scale-Down] Terminated {-delta} workers (total {len(workers)})")
            
            print(f"[Monitor] Backlog={B}, ArrivalRate≈{ArrivalRate:.1f}/s, Workers={len(workers)}")
            time.sleep(SCALE_INTERVAL)
    finally:
        for p in workers:
            terminate(p)

if __name__ == "__main__":
    dynamic_scale()
