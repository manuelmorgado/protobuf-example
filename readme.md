# Protobuf: C++ <-> Python (via MQTT)

Minimal end-to-end example of serializing a Protocol Buffers message in Python, publishing it over MQTT, and receiving and decoding it in C++.


The message schema is defined in packet.proto:
  
  - Python acts as the publisher.
  - C++ acts as the subscriber.

```
./
├── packet.proto
├── cpp_end.cpp
├── python_end.py
├── readme.md
```

Tested on:

  Ubuntu 22.04
  - GCC ≥ 11
  - Conda (Miniconda or Anaconda


  
## Prepare workspace


Install required system packages:
```bash
sudo apt update
sudo apt install build-essential cmake pkg-config \
                 libmosquitto-dev mosquitto \
                 python3-pip
```

Start the MQTT broker:
```bash
sudo systemctl start mosquitto
```

and check it is running:
```bash
systemctl status mosquitto
```

To build and install protobuf from source:
```bash
git clone --recursive https://github.com/protocolbuffers/protobuf.git
cd protobuf
git checkout v27.1
mkdir build && cd build
cmake -Dprotobuf_BUILD_TESTS=OFF -Dprotobuf_BUILD_SHARED_LIBS=ON ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

It should show something like:
```bash
/usr/local/bin/protoc
libprotoc 27.1
/usr/local/lib/libprotobuf.so.27.1.0
```

## 1. Install build dependencies

When using a conda environment, you can create:
```bash
conda create -n q-env python=3.9
conda activate q-env
```

and install mqtt:
```bash
pip install protobuf paho-mqtt
```

Checks:

``` bash
which protoc
protoc --version
pkg-config --version
```

It should show something like:
```bash
/usr/local/bin/protoc
libprotoc 27.1
0.29.2
```

------------------------------------------------------------------------

## 2. Generate protobuf files from the `.proto` schema

From the q-env conda environment:

### Generate C++ (`packet.pb.h` / `packet.pb.cc`)

``` bash
protoc -I . --cpp_out=. packet.proto
```

### Generate Python (`packet_pb2.py`)

``` bash
protoc -I . --python_out=. packet.proto
```

this will generate the files:

```
packet.pb.cc
packet.pb.h
packet_pb2.py
```

------------------------------------------------------------------------

## 3. Compile the C++ code

One should be able to compile it with:

```bash
g++ -std=c++17 -O2 cpp_end.cpp packet.pb.cc -I. $(pkg-config --cflags protobuf) -o cpp_end $(pkg-config --libs protobuf) $(pkg-config --libs libmosquitto) -Wl,-rpath,/usr/local/lib
```
  
if this does not work, you can try best when `pkg-config` finds libs:

``` bash
g++ -std=c++17 -O2   cpp_end.cpp packet.pb.cc   -o cpp_end   $(pkg-config --cflags --libs libmosquitto protobuf)
```

or using conda variable `$CONDA_PREFIX` explicitly (with missing libs):

``` bash
g++ -std=c++17 -O2   -I"$CONDA_PREFIX/include"   cpp_end.cpp packet.pb.cc   -L"$CONDA_PREFIX/lib"   -Wl,-rpath,"$CONDA_PREFIX/lib"   -lmosquitto -lprotobuf -pthread   -o cpp_end
```

One can verify with:
```bash
ldd ./cpp_end | grep -E 'protobuf|mosquitto'
```

Finally, run:

``` bash
./cpp_end
```

Expecting the following output:
```bash
Listening on demo/packet ...
```

From another terminal the python end can be runned:
```bash
python python_end.py
```

This will generate in something like this in the 

C++ terminal:
```bash
Received Packet:
  id: run-001
  label: test-frame
  dtype: float32
  shape: [4, 3]
  first values: ...
```

Python terminal:
```bash
Published XX bytes to demo/packet
```

In case of any rebuild, the necessary commands are:
```bash
rm -f packet.pb.cc packet.pb.h packet_pb2.py cpp_end

protoc -I . --cpp_out=. packet.proto
protoc -I . --python_out=. packet.proto
```

------------------------------------------------------------------------

## 4. Errors and fixes

### A) `packet.pb.h: No such file or directory`

It didn't generate the C++ protobuf outputs, or it's compiling in a
different directory.

Fix:

``` bash
cd ~/proto_demo
protoc -I . --cpp_out=. packet.proto
```

------------------------------------------------------------------------

### B) `fatal error: mosquitto.h: No such file or directory`

Mosquitto headers aren't installed in the active environment.

Fix:

``` bash
conda install -c conda-forge -y mosquitto
```

------------------------------------------------------------------------

### C) Linker errors like `undefined reference to ...protobuf...` or `...mosquitto...`

You are missing link flags, or the linker is picking the wrong libs.

Fix: use Option B compile line (with `$CONDA_PREFIX` and
`-Wl,-rpath,...`).

------------------------------------------------------------------------

### D) Program runs but doesn't receive messages

This code connects to MQTT at `127.0.0.1:1883` and subscribes to topic
`demo/packet`.

Make sure a broker is running locally:

``` bash
mosquitto -p 1883
```

### E) Maybe array missing

To ensure that the array is publish by python or cpp you can use a monitor of mosquitto as:
```bash
mosquitto_sub -h localhost -t demo/packet -C 1 | wc -c
```

### F) Too many MQTT brokers open (e.g., 1883/1884)

One can check a log of the mosquitto service:
```bash
sudo tail -f /var/log/mosquitto/mosquitto.log
```
where new pub/rcv will be shown up. They can be closed (ubuntu) with:
```bash
sudo snap stop mosquitto
```
and try again.


------------------------------------------------------------------------

## 5. Makefile

Create `Makefile`:

``` makefile
CXX := g++
CXXFLAGS := -std=c++17 -O2

PROTO := packet.proto
PB_CC := packet.pb.cc
PB_H  := packet.pb.h
PY_PB := packet_pb2.py

PKG_CFLAGS := $(shell pkg-config --cflags protobuf)
PKG_LIBS   := $(shell pkg-config --libs protobuf) $(shell pkg-config --libs libmosquitto)

RPATH := -Wl,-rpath,/usr/local/lib
PY_PROTOC := $(CONDA_PREFIX)/bin/protoc

all: cpp_end

$(PB_CC) $(PB_H): $(PROTO)
	/usr/local/bin/protoc -I . --cpp_out=. $(PROTO)

$(PY_PB): $(PROTO)
	$(PY_PROTOC) -I . --python_out=. $(PROTO)

proto: $(PB_CC) $(PB_H) $(PY_PB)

cpp_end: cpp_end.cpp $(PB_CC)
	$(CXX) $(CXXFLAGS) -I. $(PKG_CFLAGS) $^ -o $@ $(PKG_LIBS) $(RPATH)

clean:
	rm -f cpp_end $(PB_CC) $(PB_H) $(PY_PB)
```

This will then ```make proto`` for both protobuf files, ``make`` for only cpp_end and ``make clean`` that can be used to remove old artifacts.

------------------------------------------------------------------------

## 6. References

Protobuf tutorials:
   C++: https://protobuf.dev/getting-started/cpptutorial/
   Python: https://protobuf.dev/getting-started/pythontutorial/

Protobuf git:
   https://github.com/protocolbuffers/protobuf/blob/main/cmake/README.md
   
Other tutorials:
   https://victoriametrics.com/blog/go-protobuf-basic/
   https://medium.com/@staytechrich/protocol-buffers-tutorial-part-1-getting-started-with-protobuf-basics-17585e53c9e4
   
Other tutorials:
   https://victoriametrics.com/blog/go-protobuf-basic/
   https://medium.com/@staytechrich/protocol-buffers-tutorial-part-1-getting-started-with-protobuf-basics-17585e53c9e4
