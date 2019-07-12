from __future__ import print_function

import random
import logging

import grpc

import route_guide_pb2
import route_guide_pb2_grpc
from concurrent.futures import ThreadPoolExecutor
import threading
import random
import time

SERVERS = ["localhost:50052", "localhost:50053" , "localhost:50054"]
#u_list = [7, 61, 54, 29, 32, 40, 56]
u_list = [17, 16, 54, 129, 23, 20, 36]


def get_pivot(_list):
    pivot = random.choice(_list)
    _list.remove(pivot)
    return pivot

def quicksort(_list):
    if len(_list) <= 1:
        return _list
    pivot = random.choice(_list)
    _list.remove(pivot)
    return quicksort([x for x in _list if x < pivot]) \
           + [pivot] \
           + quicksort([x for x in _list if x >= pivot])

#import route_guide_resources
def compare(stub, data):
    value=stub.compare(data)
    return value
    #print("comparing" +str(data.a)+ " and "+ str(data.b) +"val" + str(value) + "by worker "+ threading.currentThread().getName())


# connect to a grpc server and make a stub call
def connect(servers, request):
    """
    server - server ip

    request - input tuple
    """
    server = random.choice(servers)
    channel = grpc.insecure_channel(server)
    stub = route_guide_pb2_grpc.RouteGuideStub(channel)
    return stub

# pooling server connections
def connection_pooling(servers):
     executor = ThreadPoolExecutor(thread_name_prefix="worker")
     return executor

def parallel_qsort(_list, executor):
    if(len(_list)<=1):
        return _list
    logging.debug("jobs - {} threads - {}".format(executor._work_queue.qsize(), len(executor._threads)))
    logging.debug("{} - list {}".format(threading.currentThread().getName(), str(_list)))
    pivot = get_pivot(_list)
    logging.debug("{} - selected - pivot {}".format(threading.currentThread().getName(), str(pivot)))
    left_slice=[]
    right_slice= []
    for num in _list:
        request = route_guide_pb2.Tuple(a=num, b=pivot)
        logging.debug("{} - request {}".format(threading.currentThread().getName(), str(request)))
        # get stub and perform RMI
        stub = connect(SERVERS, None)
        result = compare(stub, request)
        logging.debug("{}  - result {}".format(threading.currentThread().getName(), str( result )))
        if(result.result < 0 or result.result == 0):
            left_slice.append(num)
        else:
            right_slice.append(num)
        logging.debug("{} - left {}".format(threading.currentThread().getName(), str(left_slice)))
        logging.debug("{} - right {}".format(threading.currentThread().getName(), str(right_slice)))
    # left_slice=[x for x in _list if x <= pivot]
    # right_slice = [x for x in _list if x > pivot]
    l_exec = executor.submit(parallel_qsort, left_slice, executor)
    r_exec = executor.submit(parallel_qsort, right_slice, executor)
    # l_exec.result()
    # r_exec.result()
    return (l_exec.result() + [pivot] + r_exec.result())

if __name__ == '__main__':
    logging.basicConfig(filename="logs.log" ,level=logging.DEBUG)
    executor= connection_pooling(SERVERS)
    N = 500
    u_list=[random.randint(1, N) for x in range(N)]
    start = time.time()
    print(quicksort(list(u_list))[:10])
    logging.info("sequential quick sort took {:f} s".format(time.time()-start))
    start = time.time()
    print(parallel_qsort(list(u_list), executor)[:10])
    logging.info("parallel quick sort took {:f} s".format(time.time()-start))
    executor.shutdown()


