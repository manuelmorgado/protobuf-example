import numpy as np
import paho.mqtt.client as mqtt

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
    arr = (np.random.rand(4, 3).astype(np.float32) * 10.0)

    data = MyData(
        id="run-001",
        label="test-frame",
        arr=arr,
        secret_note="Not included",
    )

    payload = to_proto_bytes(data)

    client = mqtt.Client()
    client.connect(broker_host, 1883, 60)
    client.publish(topic, payload, qos=1)
    client.disconnect()

    print(f"Published {len(payload)} bytes to {topic}")


if __name__ == "__main__":
    publish_example()
