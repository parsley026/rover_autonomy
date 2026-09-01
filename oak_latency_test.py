
import depthai as dai
import threading
import time
import numpy as np

pipeline = dai.Pipeline()

N = 100

script = pipeline.create(dai.node.Script)
script.setScript("""
while True:
    buf = node.io['in'].get()
    node.io['out'].send(buf)
""")

timestamps = []
def send_buff(q):
    for i in range(N):
        buffer = dai.Buffer()
        buffer.setData([1])
        q.send(buffer)
        print('Sending buffer', i)
        timestamps.append(time.time())
        time.sleep(0.2)

qin = script.inputs["in"].createInputQueue()
qout = script.outputs["out"].createOutputQueue()

pipeline.start()

thread = threading.Thread(target=send_buff, args=(qin,))
thread.start()

latencies = np.array([])
for i in range(N):
    buff: dai.Buffer = qout.get()
    latency = time.time() - timestamps[i]
    if i != 0: # Skip first buffer
        latency *= 1000 # to milliseconds
        latencies = np.append(latencies, latency)
        print('Got {}. buffer, latency {:.2f} ms'.format(i, latency))

print()
print('Average latency {:.2f} ms, Std: {:.1f}'.format(np.average(latencies), np.std(latencies)))