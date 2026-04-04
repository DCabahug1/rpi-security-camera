import threading
import time
import random
from queue import Queue


def producer(q: Queue[str]):
    for i in range(5):
        print(f"message_{str(i)} sent.")

        latency = random.randint(2, 10)
        time.sleep(latency)

        q.put("message_" + str(i))
    q.put(None)


def consumer(q: Queue[str]):
    while True:
        message = q.get()

        if message == None:
            return

        print(f"        {message} received.")


q: Queue[str] = Queue()

prod = threading.Thread(target=producer, args=(q,))
cons = threading.Thread(target=consumer, args=(q,))

print("Conversation started.")
prod.start()
cons.start()

prod.join()
cons.join()
print("Conversation ended.")
