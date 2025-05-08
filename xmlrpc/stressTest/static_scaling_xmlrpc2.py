# static_scaling_xmlrpc2.py

import xmlrpc.client
import multiprocessing
import time
import matplotlib.pyplot as plt

# ── Configuration ────────────────────────────────────────────────────
SERVER_PORTS    = [9000, 9001, 9002]   # the three server nodes you have running
HOST            = "localhost"
TOTAL_REQUESTS  = 1600                 # keep this constant for all N
NUM_PROCESSES   = 10                   # client‑side parallelism
# ────────────────────────────────────────────────────────────────────