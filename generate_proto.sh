#!/bin/bash

# Скрипт для генерации Python кода из .proto файлов

echo "Generating Python code from Protocol Buffers..."

/opt/anaconda3/envs/ml-python312/bin/python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./generated \
    --grpc_python_out=./generated \
    ./protos/model.proto

if [ $? -eq 0 ]; then
    echo "Code generated successfully in ./generated/"
    
    echo "Fixing imports in generated code..."
    sed -i.bak 's/^import model_pb2 as model__pb2$/from . import model_pb2 as model__pb2/' ./generated/model_pb2_grpc.py
    rm -f ./generated/*.bak
    
    ls -la ./generated/
    echo "Done"
else
    echo "Error generating code"
    exit 1
fi
