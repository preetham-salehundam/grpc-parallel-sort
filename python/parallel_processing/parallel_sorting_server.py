from concurrent import futures
import time,sys
import math
import logging

import grpc, random

import parallel_sorting_pb2
import parallel_sorting_pb2_grpc

from utils import min_max_sort
#import route_guide_resources

PORT = 50051
NIL = parallel_sorting_pb2.NIL()

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# def quicksort(_list):
#     if len(_list) <= 1:
#         return _list
#     pivot = random.choice(_list)
#     _list.remove(pivot)
#     return quicksort([x for x in _list if x < pivot]) \
#            + [pivot] \
#            + quicksort([x for x in _list if x >= pivot])


def stream_data(data):
    for x in data:
        yield x

class ParallelSortingServicer(parallel_sorting_pb2_grpc.ParallelSortingServicer):
    def __init__(self):
        self.busy = False
        self.internal_array =[]
        self.stub = None
        self.result_from_peer = []

    def start_connection(self, _ , context):
        """
        start connection after establishing a channel
        """
        logging.debug("#### start conn #####")
        if(not self.busy):
            self.busy = True
            logging.debug("#### conn established successfully #####")
            return parallel_sorting_pb2.Status(status=self.busy)
        else:
            logging.debug("#### server busy #####")
            return parallel_sorting_pb2.Status(status=False)

    def connect_to(self, machine_addr, context):
        """
        connect to a peer machine
        """
        logging.debug("#### trying to connect to {}  #####".format(machine_addr))
        channel = grpc.insecure_channel(machine_addr.addr)
        self.stub = parallel_sorting_pb2_grpc.ParallelSortingStub(channel)
        return parallel_sorting_pb2.Status(status=self.stub is not None)

    def  end_connection(self, _, context):
        logging.debug("#### end conn #####")
        if(self.busy):
            self.busy = False
            logging.debug("#### conn ended successfully #####")
        else:
            logging.debug("#### active conn doesnt exist #####")
        return parallel_sorting_pb2.Status(status=not self.busy)

    def compare(self, data, context):
        result= data.a - data.b
        return parallel_sorting_pb2.Result(result=result)

    # forward init data from process A to process B
    def forward_data_to_peer(self, data, context):
        # init initial array in process B with data
        data = [parallel_sorting_pb2.Data(item=x.item) for x in data]
        self.stub.input_data(stream_data(data))
        return NIL

    def input_data(self, data, context):
        # sets internal array data initially
        self.internal_array = [x.item for x in data]
        logging.debug("i_Arr {}".format(self.internal_array))
        return NIL

    def fetch_result_from_peer(self, _ , context):
        result= self.stub.get_partial_sorted_data(NIL)
        result = [parallel_sorting_pb2.Data(item=x.item) for x in result]
        for item in result:
            yield item
    
    def remove_duplicate(self, data , context):
        index = self.internal_array.index(data.b)
        self.internal_array.pop(index)
        return NIL

    def process_data(self, data_a, context):
        logging.debug("#### process_data ####")
        self.internal_array = [x.item for x in data_a]
        min_B = self.stub.get_min(NIL).result
        max_A = max(self.internal_array)
        while(not max_A <= min_B):
            # swap max and min
            logging.debug(" min {}, max {}".format(min_B, max_A))
            data = parallel_sorting_pb2.Tuple(a=max_A, b=min_B)
            # if(max_A == min_B):
            #     self.stub.remove_duplicate(data)
            #     min_B = data.b
            #     index = self.internal_array.index(max_A)
            #     self.internal_array.insert(index+1, min_B)
            # else:
            min_B = self.stub.swap(data).result
            index = self.internal_array.index(max_A)
            self.internal_array[index] = min_B
            logging.debug("after swapping in process A {}".format(self.internal_array))
            min_B = self.stub.get_min(NIL).result
            max_A = max(self.internal_array)
        # internal sort    
        self.internal_array = min_max_sort(self.internal_array)
        # remote sort the array on other process
        self.stub.remote_sort(NIL)
        for item in self.internal_array:
            yield parallel_sorting_pb2.Data(item=item)  
        #pass

    def get_min(self,_, context):
        logging.debug("#### get_min ####")
        logging.debug(" min - {}".format(min(self.internal_array)))
        result = min(self.internal_array)
        return parallel_sorting_pb2.Result(result = result)
        #pass
    
    def get_max(self,_, context):
        logging.debug("#### get_max ####")
        logging.debug(" max - {}".format(max(self.internal_array)))
        return parallel_sorting_pb2.Result(result = max(self.internal_array))
        #pass
    
    def swap(self, data,  context):
        logging.debug("#### swap ####")
        logging.debug(" {} swapped with {}".format(data.a, data.b))
        #TODO: swap a with b in the internal array
        try: 
            index = self.internal_array.index(data.b)
            self.internal_array[index] = data.a
            logging.debug("after-swap in process B {}".format(self.internal_array))
        except Exception as error:
            logging.error("Error - {}".format(error.message))
        return parallel_sorting_pb2.Result(result=data.b)
        #pass

    def remote_sort(self, _ , context):
        logging.debug("#### remote_sort ####")
        self.internal_array = min_max_sort(self.internal_array)
        logging.debug("sorted array {}".format(str(self.internal_array)))
        data = [parallel_sorting_pb2.Data(item=x) for x in self.internal_array]
        for item in data:
            yield item
        #pass

    def check_if_busy(self, _ , context):
        logging.debug("#### check_if_busy ####")
        return parallel_sorting_pb2.Status(status=self.busy)

    def get_partial_sorted_data(self, _ , context):
        logging.debug("##### returning partial sorted data")
        logging.debug("returning partial sorted array {}".format(str(self.internal_array)))
        data = [parallel_sorting_pb2.Data(item=x) for x in min_max_sort(self.internal_array)]
        for item in data:
            yield item

def serve(port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    parallel_sorting_pb2_grpc.add_ParallelSortingServicer_to_server(
        ParallelSortingServicer(), server)
    server.add_insecure_port('[::]:{}'.format(port))
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        PORT=sys.argv[1]
    except Exception as e:
        pass
    serve(port=PORT)

