from __future__ import print_function

import random
import logging

import grpc

import parallel_sorting_pb2
import parallel_sorting_pb2_grpc
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process
import threading
import random
import time
import math
import itertools
import shutil
import sys
from utils import min_max_sort
#from parallel_sorting_server import serve
NIL = parallel_sorting_pb2.NIL()

# chunk generator


def chunkify(arr, num_of_chunks=1):
    """
    generator method to split a list into n - chunks

    @param - arr - i/p list
    @param - num of chunks the list to be split

    @returns sub-list/chunks
    """
    start = 0
    chunk_size = math.ceil(len(arr)/num_of_chunks)
    for i in range(num_of_chunks):
        # print(i)
        i += 1  # avoiding a zero
        yield arr[start: i*chunk_size]
        start = i*chunk_size

def quicksort(_list):
    """
    quick sort implementation - used for validation

    @param - _list - unsorted list
    @return a list of sorted items
    """
    if len(_list) <= 1:
        return _list
    pivot = random.choice(_list)
    _list.remove(pivot)
    return quicksort([x for x in _list if x < pivot]) \
        + [pivot] \
        + quicksort([x for x in _list if x >= pivot])

# connect to a grpc server and make a stub call
def connect(servers, request):
    """
    connect to a grpc server and make a stub call

    @param server - server ip
    @param request - input tuple
    @return connection stub
    """
    server = random.choice(servers)
    channel = grpc.insecure_channel(server)
    stub = parallel_sorting_pb2_grpc.ParallelSortingStub(channel)
    return stub


def connect_to(machine_addr):
    """
    makes a connection and returns a stub
    """
    channel = grpc.insecure_channel(machine_addr)
    stub = parallel_sorting_pb2_grpc.ParallelSortingStub(channel)
    return stub


def setup(stub, peer_B):
    # start connection to process A
    status = stub.start_connection(NIL)
    if(status):
        # INFO: stub's connect_to not a local method in client
        addr = parallel_sorting_pb2.Address(addr=peer_B)
        # make process A connect to Peer B
        stub.connect_to(addr)
    else:
        logging.error("remote_process is busy")


def collect_result(stub):
    """
    method to collect the sorted chunk from remote process
    """
    logging.debug("#### collect_result ####")
    arr_B = stub.fetch_result_from_peer(NIL)
    peer_B_data = [x.item for x in arr_B]
    # end connection of process A
    stub.end_connection(NIL)
    return peer_B_data
    #raise NotImplementedError("Method not implemented")


def stream_ip_data(ip_arr):
    """
    generator method for streaming input data over the wire
    """
    data = [parallel_sorting_pb2.Data(item=item) for item in ip_arr]
    logging.debug("stream_ip_data {}".format(str(data)))
    for item in data:
        yield item


def parallel_sort(machine_a, machine_b, u_list_a, u_list_b):
    # connect to process_A
    logging.debug("connecting {} with {} ".format(machine_a, machine_b))
    stub = connect_to(machine_a)
    # setup connection to process_B from process_A
    setup(stub, machine_b)
    # send data to process A to be forwared to process B
    stub.forward_data_to_peer(stream_ip_data(u_list_b))
    # send data to process A and start the algorithm
    result_a = stub.process_data(stream_ip_data(u_list_a))
    result_a = [x.item for x in result_a]
    result_b = collect_result(stub)
    # u_list1 = result_1
    # u_list2 = result_2
    logging.debug("Thread {} - sorted ulist_a {} ulist_b {}".format(
        threading.currentThread().getName(), result_a, result_b))
    return (result_a, result_b)


def converge(u_list, partitions):
    flag = True
    #u_list = list((chunkify(unsorted_list, PARTITIONS)))
    for i in range(1, partitions):
        if (not isEmpty(u_list[i-1]) and not isEmpty(u_list[i])):
            flag = flag and (max(u_list[i-1]) <= min(u_list[i]))
    return flag


def isEmpty(_list):
    return len(_list) == 0


if __name__ == '__main__':
    logging.basicConfig(filename="logs.log", level=logging.INFO)
    PARTITIONS = 4
    num_of_elements = 10
    try:
        num_of_elements = int(sys.argv[2])
    except:
        pass
    #unsorted_list = [17, 16, 54, 129, 23, 20, 36, 18, 15, 55, 127, 24, 21, 37, 19, 14, 59, 131, 25, 22, 38, 13, 16, 57, 123, 27, 12, 31]
    unsorted_list = [random.randint(1, 100) for x in range(0, num_of_elements)]
    #unsorted_list = [1,6,4,2,3,5]
    print("unsorted list - {}".format(unsorted_list))
    try:
        PARTITIONS = int(sys.argv[1])
    except Exception as e:
        pass
    logging.info(" {} workers are being used to sort an list of {} items ".format(
        PARTITIONS, num_of_elements))
    u_list = list(chunkify(unsorted_list, PARTITIONS))
    start = time.time()
    qs = min_max_sort(list(itertools.chain(*u_list)))
    end = time.time() - start
    logging.info("seq sort took {:f} s".format(end))
    machine_lookup = ["localhost:50051", "localhost:50052", "localhost:50053",
                      "localhost:50054", "localhost:50055", "localhost:50056",
                      "localhost:50057", "localhost:50058", "localhost:50059", "localhost:50060"]
    start = time.time()
    with ThreadPoolExecutor(thread_name_prefix="worker") as executor:
        while(not converge(u_list, PARTITIONS)):
            # sorting even number chunks
            print("bef0re- {}".format(u_list))
            futures = [None for x in range(PARTITIONS)]
            for i in range(PARTITIONS):
                if(i % 2 == 0) and i+1 < PARTITIONS:
                    a, b = (i, i+1)
                    if(not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <= min(u_list[b]))):
                        # Spawn a thread adnd delegate function call to the thread
                        futures[a] = executor.submit(
                            parallel_sort, machine_lookup[a], machine_lookup[b], u_list[a], u_list[b])

            for i in range(PARTITIONS):
                if(i % 2 == 0) and i+1 < PARTITIONS:
                    a, b = (i, i+1)
                    # collect results from the threads
                    if(not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <= min(u_list[b]))):
                        u_list[a], u_list[b] = futures[a].result()

            # sorting odd number chunks
            for i in range(PARTITIONS):
                if(i % 2 != 0 and i+1 < PARTITIONS):
                    a, b = (i, i+1)
                    if(not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <= min(u_list[b]))):
                        # Spawn a thread adnd delegate function call to the thread
                        futures[a] = executor.submit(
                            parallel_sort, machine_lookup[a], machine_lookup[b], u_list[a], u_list[b])

            for i in range(PARTITIONS):
                if(i % 2 != 0 and i+1 < PARTITIONS):
                    a, b = (i, i+1)
                    if(not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <= min(u_list[b]))):
                        # collect results from the threads
                        u_list[a], u_list[b] = futures[a].result()
            print("after- {}".format(u_list))

    end = time.time() - start
    # flatten the list using itertools
    pqs = list(itertools.chain(*u_list))
    print("seq sorted-list - {} ".format(qs))
    print("parallel sorted-list - {} ".format(pqs))
    logging.info("parallel sorting took - {:f} seconds".format(end))

    # assertions for validation
    assert qs == pqs
    assert sum(unsorted_list) == sum(qs)
    assert sum(unsorted_list) == sum(pqs)
    assert quicksort(list(itertools.chain(*u_list))) == pqs
