#! /bin/bash
kill $(ps -ef | grep parallel_sorting_ | awk '{print $2}')

python parallel_sorting_server.py 50051 &

python parallel_sorting_server.py 50052 &

python parallel_sorting_server.py 50053 &

python parallel_sorting_server.py 50054 &


#python -m grpc_tools.protoc --proto_path ../../protos --python_out=. --grpc_python_out=. ../../protos/parallel_sorting.proto
