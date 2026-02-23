import numpy as np
import paho.mqtt.client as mqtt
import time

import packet_pb2


class MyData:
    def __init__(self, id: str, label: str, arr: np.ndarray, secret_note: str):
        self.id = id
        self.label = label
        self.arr = arr
        self.secret_note = secret_note  #no serialized


def to_proto_bytes(obj: MyData) -> bytes:

    #ensure a consistent dtype + contiguous memory
    arr = np.ascontiguousarray(obj.arr)
    dtype = str(arr.dtype)

    msg = packet_pb2.Packet()
    msg.id = obj.id
    msg.label = obj.label

    msg.array.dtype = dtype
    msg.array.shape.extend(list(arr.shape))
    msg.array.data = arr.tobytes(order="C")

    #secret_note is ignored
    return msg.SerializeToString()


def publish_example(broker_host="127.0.0.1", topic="demo/packet"):
    arr = (np.random.rand(5000, 5000).astype(np.float32) * 10.0)

    data = MyData(
        id="run-001",
        label="test-frame",
        arr=arr,
        secret_note="Not included",
    )

    payload = to_proto_bytes(data)

    client = mqtt.Client()
    print("DBG: before connect")
    client.connect(broker_host, 1884, 60)
    print("DBG: after connect, before loop_start")
    client.loop_start()
    print("DBG: after loop_start, before publish")
    t0 = time.perf_counter_ns()
    info = client.publish(topic, payload, qos=1)
    print("DBG: after publish, before wait_for_publish")
    ok = info.wait_for_publish(timeout=10)
    print("DBG: wait_for_publish returned:", ok)
    dt_ms = (time.perf_counter_ns() - t0) * 1e-6
    print(f"publish+ack: {dt_ms:.2f} ms")
    client.loop_stop()
    client.disconnect()

    print(f"Published {len(payload)} bytes to {topic}")


if __name__ == "__main__":
    publish_example()
