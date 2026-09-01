
import depthai as dai
import numpy as np
import time


N = 50
DISCARD_N = 10 # Packets to discard (due to queue sizes, system booting up, etc.)
SIZE = 1000 * 1000 * 10 # 20MB

pipeline = dai.Pipeline()

script = pipeline.create(dai.node.Script)
script.setScript(f"""
import time

# Measure downlink first
sent_ts = []
buff = Buffer({SIZE})
for i in range({N}):
    node.io['out'].send(buff)
    sent_ts.append(time.time())
    if i == {DISCARD_N-1}:
        # node.warn('{DISCARD_N-1}th buffer sent at' + str(time.time()))
        pass
    # node.warn('Sent buffer ' + str(i))
# node.warn('{N}th buffer sent at' + str(time.time()))
total_time = sent_ts[-1] - sent_ts[{DISCARD_N-1}]
total_bits = ({N-DISCARD_N}) * {SIZE} * 8
downlink = total_bits / total_time
downlink_mbps = downlink / (1000 * 1000)
# node.warn('Downlink ' + str(downlink_mbps) + ' mbps')

# Measure uplink
receive_ts = []
for i in range({N}):
    node.io['in'].get()
    receive_ts.append(time.time())
    if i == {DISCARD_N-1}:
        # node.warn('{DISCARD_N-1}th buffer received at' + str(time.time()))
        pass
    # node.warn('Received buffer ' + str(i))
# node.warn('{N}th buffer received at' + str(time.time()))

total_time = receive_ts[-1] - receive_ts[{DISCARD_N-1}]
total_bits = ({N-DISCARD_N}) * {SIZE} * 8
uplink = total_bits / total_time
uplink_mbps = uplink / (1000 * 1000)
# node.warn('Uplink ' + str(uplink_mbps) + ' mbps')
""")

qin = script.inputs['in'].createInputQueue()
qout = script.outputs['out'].createOutputQueue()

pipeline.start()

# Downlink
receive_ts = []
for i in range(N):
    qout.get()
    receive_ts.append(time.time())
    if i == DISCARD_N-1:
        pass

total_time = receive_ts[-1] - receive_ts[DISCARD_N-1]
total_bits = (N-DISCARD_N) * SIZE * 8
downlink = total_bits / total_time
print('Downlink {:.1f} mbps'.format(downlink/ (1000 * 1000)))

buffer = dai.Buffer()
buffer.setData(np.zeros(SIZE, dtype=np.uint8))
sent_ts = []
for i in range(N):
    qin.send(buffer)
    sent_ts.append(time.time())
    if i == DISCARD_N-1:
        pass

total_time = sent_ts[-1] - sent_ts[DISCARD_N-1]
total_bits = (N-DISCARD_N) * SIZE * 8
uplink = total_bits / total_time
print('Uplink {:.1f} mbps'.format(uplink/ (1000 * 1000)))

input("Press any key to continue...")