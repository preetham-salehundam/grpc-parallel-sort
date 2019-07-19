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
import time, math, itertools, shutil,sys
from utils import min_max_sort
#from parallel_sorting_server import serve
NIL = parallel_sorting_pb2.NIL()

# chunk generator
def chunkify(arr, num_of_chunks=1):
    start = 0
    chunk_size = math.ceil(len(arr)/num_of_chunks)
    for i in range(num_of_chunks):
        #print(i)
        i += 1 #avoiding a zero
        yield arr[start: i*chunk_size]
        start = i*chunk_size
# def chunkify(_list, size, s_loc=0):
#     holder = []
#     s_loc, e_loc = (s_loc, size)
#     for i in range(0, math.ceil(len(_list)/size)):
#         holder.append(_list[s_loc: e_loc])
#         s_loc = e_loc
#         e_loc = s_loc + size
#     return holder

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
    stub = parallel_sorting_pb2_grpc.ParallelSortingStub(channel)
    return stub

# pooling server connections
def connection_pooling(servers):
     executor = ThreadPoolExecutor(thread_name_prefix="worker")
     return executor

# not used
# def parallel_qsort(_list, executor):
#     if(len(_list)<=1):
#         return _list
#     logging.debug("jobs - {} threads - {}".format(executor._work_queue.qsize(), len(executor._threads)))
#     logging.debug("{} - list {}".format(threading.currentThread().getName(), str(_list)))
#     pivot = get_pivot(_list)
#     logging.debug("{} - selected - pivot {}".format(threading.currentThread().getName(), str(pivot)))
#     left_slice=[]
#     right_slice= []
#     for num in _list:
#         request = parallel_sorting_pb2.Tuple(a=num, b=pivot)
#         logging.debug("{} - request {}".format(threading.currentThread().getName(), str(request)))
#         # get stub and perform RMI
#         stub = connect(SERVERS, None)
#         result = compare(stub, request)
#         logging.debug("{}  - result {}".format(threading.currentThread().getName(), str( result )))
#         if(result.result < 0 or result.result == 0):
#             left_slice.append(num)
#         else:
#             right_slice.append(num)
#         logging.debug("{} - left {}".format(threading.currentThread().getName(), str(left_slice)))
#         logging.debug("{} - right {}".format(threading.currentThread().getName(), str(right_slice)))
#     # left_slice=[x for x in _list if x <= pivot]
#     # right_slice = [x for x in _list if x > pivot]
#     l_exec = executor.submit(parallel_qsort, left_slice, executor)
#     r_exec = executor.submit(parallel_qsort, right_slice, executor)
#     # l_exec.result()
#     # r_exec.result()
#     return (l_exec.result() + [pivot] + r_exec.result())


def connect_to(machine_addr):
    channel = grpc.insecure_channel(machine_addr)
    stub = parallel_sorting_pb2_grpc.ParallelSortingStub(channel)
    return stub

def setup(stub, peer_B):
    # start connection to process A
    status=stub.start_connection(NIL)
    if(status):
        # stub's connect_to not a local method in client
        addr = parallel_sorting_pb2.Address(addr = peer_B)
        stub.connect_to(addr)
    else:
        logging.error("remote_process is busy")



def collect_result(stub):
    logging.debug("#### collect_result ####")
    arr_B = stub.fetch_result_from_peer(NIL)
    peer_B_data = [x.item for x in arr_B]
    # end connection of process A
    stub.end_connection(NIL)
    return peer_B_data
    #raise NotImplementedError("Method not implemented")


def stream_ip_data(ip_arr):
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
    result_b =  collect_result(stub)
    # u_list1 = result_1
    # u_list2 = result_2
    logging.debug("Thread {} - sorted ulist_a {} ulist_b {}".format(threading.currentThread().getName(),result_a, result_b))
    return (result_a, result_b)
    

def converge(u_list, partitions):
    flag = True
    #u_list = list((chunkify(unsorted_list, PARTITIONS)))
    for i in range(1,partitions):
        if (not isEmpty(u_list[i-1]) and not isEmpty(u_list[i])):
            flag = flag and (max(u_list[i-1]) <=  min(u_list[i]))
    return flag

def isEmpty(_list):
    return len(_list) == 0


if __name__ == '__main__':
    logging.basicConfig(filename="logs.log",level=logging.INFO)
    PARTITIONS = 4
    num_of_elements = 100
    try:
        num_of_elements = int(sys.argv[2])
    except:
        pass
    #unsorted_list = [17, 16, 54, 129, 23, 20, 36, 18, 15, 55, 127, 24, 21, 37, 19, 14, 59, 131, 25, 22, 38, 13, 16, 57, 123, 27, 12, 31]
    unsorted_list = [random.randint(1, 100) for x in range(0,num_of_elements)]
    print("unsorted list - {}".format(unsorted_list))
    try:
        PARTITIONS=int(sys.argv[1])
    except Exception as e:
        pass
    logging.info(" {} workers are being used to sort an list of {} items ".format(PARTITIONS, num_of_elements))
    u_list = list(chunkify(unsorted_list, PARTITIONS))
    start = time.time()
    #qs=quicksort(u_list1 + u_list2 + u_list3 + u_list4)
    # flatten list of lists using iter tools
    #qs=quicksort(u_list[0] + u_list[1] + u_list[2] + u_list[3])
    qs=min_max_sort(list(itertools.chain(*u_list)))
    end = time.time() - start
    logging.info("seq sort took {:f} s".format(end))
    machine_lookup = ["localhost:50051", "localhost:50052", 
    "localhost:50053", "localhost:50054", 
    "localhost:50055", "localhost:50056", 
    "localhost:50057", "localhost:50058",
    "localhost:50059", "localhost:50060"]
    start = time.time()
    with ThreadPoolExecutor(thread_name_prefix="worker") as executor:
       # while(not ((max(u_list1) < min(u_list2)) and (max(u_list2) <  min(u_list3)) and (max(u_list3) < min(u_list4)) )):
        #while(not ((max(u_list[0]) < min(u_list[1])) and (max(u_list[1]) <  min(u_list[2])) and (max(u_list[2]) < min(u_list[3])) )):
        while(not converge(u_list, PARTITIONS)):
            # step 1
            #if(not (max(u_list1) < min(u_list2))):

            # sorting even number chunks
            futures= [None for x in range(PARTITIONS)]
            for i in range(PARTITIONS):
                if(i%2 == 0) and i+1 < PARTITIONS :
                    a,b = (i, i+1)
                    if( not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <= min(u_list[b]))):
                        futures[a]=executor.submit(parallel_sort, machine_lookup[a], machine_lookup[b], u_list[a], u_list[b])
           
            for i in range(PARTITIONS):
                if(i%2 ==0) and i+1 < PARTITIONS :
                    a,b = (i, i+1)
                    if( not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <= min(u_list[b]))):
                        u_list[a], u_list[b] = futures[a].result()
            

            # sorting odd number chunks
            for i in range(PARTITIONS):
                if(i%2 !=0 and i+1 < PARTITIONS ):
                    a,b = (i, i+1)
                    if(not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <=  min(u_list[b]))):
                        futures[a] = executor.submit(parallel_sort, machine_lookup[a], machine_lookup[b], u_list[a], u_list[b])

            for i in range(PARTITIONS):
                if(i%2 !=0 and i+1 < PARTITIONS ):
                    a,b = (i, i+1)
                    if( not isEmpty(u_list[a]) and not isEmpty(u_list[b]) and not (max(u_list[a]) <=  min(u_list[b]))):
                        u_list[a], u_list[b] = futures[a].result()

            # if(not (max(u_list[0]) < min(u_list[1]))):
            #     #connect process 1 and process 2
            #     logging.debug("p1 communicating with p2")
            #     # # connect to process_A
            #     # stub = connect_to(machine_lookup[0])
            #     # # setup connection to process_B from process_A
            #     # setup(stub, machine_lookup[1])
            #     # # send data to process A to be forwared to process B
            #     # stub.forward_data_to_peer(stream_ip_data(u_list2))
            #     # # send data to process A and start the algorithm
            #     # result_1 = stub.process_data(stream_ip_data(u_list1))
            #     # result_1 = [x.item for x in result_1]
            #     # result_2 =  collect_result(stub)
            #     # u_list1 = result_1
            #     # u_list2 = result_2
            #     # logging.debug("sorted ulist 1 {} ulist2 {}".format(u_list1, u_list2))
            #     future1=executor.submit(parallel_sort, machine_lookup[0],machine_lookup[1], u_list[0], u_list[1] )
            #     #u_list1, u_list2 = parallel_sort(machine_lookup[0],machine_lookup[1], u_list1, u_list2)
            # # step 2    
            # if(not (max(u_list[2]) <  min(u_list[3]))):
            #     # connect process 3 and process 4
            #     logging.debug("p3 communicating with p4")
            #     future2 = executor.submit(parallel_sort, machine_lookup[2], machine_lookup[3], u_list[2], u_list[3] )
            #     #u_list3, u_list4 = parallel_sort(machine_lookup[2], machine_lookup[3], u_list3, u_list4 )
            #     # # connect to process_A
            #     # stub = connect_to(machine_lookup[2])
            #     # # setup connection to process_B from process_A
            #     # setup(stub, machine_lookup[3])
            #     # # send data to process A to be forwared to process B
            #     # stub.forward_data_to_peer(stream_ip_data(u_list4))
            #     # # send data to process A and start the algorithm
            #     # result_3 = stub.process_data(stream_ip_data(u_list3))
            #     # result_3 = [x.item for x in result_3]
            #     # result_4 =collect_result(stub)
            #     # u_list3 = result_3
            #     # u_list4 = result_4
            #     # logging.debug("sorted ulist 3 {} ulist4 {}".format(u_list3, u_list4))

            # # u_list1, u_list2 = future1.result()
            # # u_list3, u_list4 = future2.result() 
            # u_list[0], u_list[1] = future1.result()
            # u_list[2], u_list[3] = future2.result() 
            # if(not (max(u_list[1]) <  min(u_list[2]))):
            #     # connect process 2 and process 3
            #     logging.debug("p2 communicating with p3")
            #     u_list[1], u_list[2] = parallel_sort(machine_lookup[1], machine_lookup[2], u_list[1], u_list[2] )
            #     # # connect to process_A
            #     # stub = connect_to(machine_lookup[1])
            #     # # setup connection to process_B from process_A
            #     # setup(stub, machine_lookup[2])
            #     # # send data to process A to be forwared to process B
            #     # stub.forward_data_to_peer(stream_ip_data(u_list3))
            #     # # send data to process A and start the algorithm
            #     # result_2 = stub.process_data(stream_ip_data(u_list2))
            #     # result_2 = [x.item for x in result_2]
            #     # result_3 =collect_result(stub)
            #     # u_list2 = result_2
            #     # u_list3 = result_3
            #     #logging.info("sorted ulist  {} ulist2 {}".format(u_list1, u_list2))
    end = time.time()- start
    # pqs = u_list1 + u_list2 + u_list3 + u_list4
    #pqs = u_list[0] + u_list[1] + u_list[2] + u_list[3]
    pqs = list(itertools.chain(*u_list))
    print("seq sorted-list - {} ".format(qs))
    print("parallel sorted-list - {} ".format(pqs))
    logging.info("parallel sorting took - {:f} seconds".format(end))
    
    #assertions
    assert qs==pqs
    assert sum(unsorted_list) == sum(qs)
    assert sum(unsorted_list) == sum(pqs)
    assert quicksort(list(itertools.chain(*u_list))) ==  pqs

        

