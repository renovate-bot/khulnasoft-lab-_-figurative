# Figurative Server
Figurative Server is a gRPC service that acts as a wrapper around  [Figurative](https://github.com/khulnasoft-lab/figurative), to support projects like the [Figurative User Interface (MUI)](https://github.com/khulnasoft-lab/FigurativeUI). Figurative Server is designed to allow developers to more easily create tools around Figurative that aren't in Python or to allow for Figurative to be run and managed in the cloud/remotely.

❗NOTE❗: The server is not published or packaged anywhere and is intended to be installed from source in a clean Python virtual environment. The server is only tested for compatibility with the version of Figurative living in the parent directory; this version of Figurative is installed when installing the server.

# Usage
Create a new Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the server with `pip install .`. This will install Figurative from the parent directory.

The Figurative Server can be run via `figurative_server`, and it will run on port `50010`.

Your Figurative Server client will require the relevant gRPC client code. You can find out how to generate gRPC client code in your desired language from [the gRPC website](https://grpc.io/docs/languages/).

You may refer to the [Protobuf Specification](figurative_server/FigurativeServer.proto) for information about the RPC services provided and the message types.
