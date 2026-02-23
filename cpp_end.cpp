#include <iostream>
#include <vector>
#include <string>
#include <cstring>

#include <mosquitto.h>

#include "packet.pb.h"  
#include <google/protobuf/stubs/common.h>

static void on_message(struct mosquitto* mosq, void* userdata, const struct mosquitto_message* msg)
{
    if (!msg || !msg->payload || msg->payloadlen <= 0) return;

    demo::Packet packet;
    if (!packet.ParseFromArray(msg->payload, msg->payloadlen)) {
        std::cerr << "Failed to parse protobuf payload\n";
        return;
    }

    std::cout << "Received Packet:\n";
    std::cout << "  id: " << packet.id() << "\n";
    std::cout << "  label: " << packet.label() << "\n";

    const auto& arr = packet.array();
    std::cout << "  dtype: " << arr.dtype() << "\n";
    std::cout << "  shape: [";
    for (int i = 0; i < arr.shape_size(); i++) {
        std::cout << arr.shape(i) << (i + 1 < arr.shape_size() ? ", " : "");
    }
    std::cout << "]\n";

    //rebuild float32 array
    if (arr.dtype() == "float32") {
        const std::string& data = arr.data();
        if (data.size() % 4 != 0) {
            std::cerr << "Wrong float32 length\n";
            return;
        }

        size_t n = data.size() / 4;
        std::vector<float> values(n);
        std::memcpy(values.data(), data.data(), data.size());

        //flattened array
        std::cout << "  first values: ";
        for (size_t i = 0; i < std::min<size_t>(n, 6); i++) {
            std::cout << values[i] << (i + 1 < std::min<size_t>(n, 6) ? ", " : "");
        }
        std::cout << "\n";
    } else {
        std::cerr << "Wrong dtype: " << arr.dtype() << "\n";
    }

}

int main()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    mosquitto_lib_init();

    mosquitto* mosq = mosquitto_new(nullptr, true, nullptr);
    if (!mosq) {
        std::cerr << "mosquitto_new failed\n";
        return 1;
    }

    mosquitto_message_callback_set(mosq, on_message);

    int rc = mosquitto_connect(mosq, "127.0.0.1", 1884, 60);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "mosquitto_connect failed: " << rc << "\n";
        return 1;
    }

    mosquitto_subscribe(mosq, nullptr, "demo/packet", 1);

    std::cout << "Listening on demo/packet ...\n";
    while (true) {
        mosquitto_loop(mosq, -1, 1);
    }

    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    google::protobuf::ShutdownProtobufLibrary();
    return 0;
}
