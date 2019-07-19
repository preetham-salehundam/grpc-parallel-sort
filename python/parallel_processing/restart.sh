#! /bin/bash
kill $(ps -ef | grep parallel_sorting_ | awk '{print $2}')

python parallel_sorting_server.py 50051 &

python parallel_sorting_server.py 50052 &

python parallel_sorting_server.py 50053 &

python parallel_sorting_server.py 50054 &

python parallel_sorting_server.py 50055 &

python parallel_sorting_server.py 50056 &

python parallel_sorting_server.py 50057 &

python parallel_sorting_server.py 50058 &

python parallel_sorting_server.py 50059 &

python parallel_sorting_server.py 50060 &

#python -m grpc_tools.protoc --proto_path ../../_protos --python_out=. --grpc_python_out=. ../../_protos/parallel_sorting.proto
