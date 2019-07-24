import random, time, sys, sorting

def quicksort(_list):
    if len(_list) <= 1:
        return _list
    pivot = random.choice(_list)
    _list.remove(pivot)
    return quicksort([x for x in _list if x < pivot]) \
           + [pivot] \
           + quicksort([x for x in _list if x >= pivot])


def min_max_sort(_list):
    p = 0
    q = len(_list)-1
    while(p<q):
        minimize(_list, p, q)
        #print("after min- {}".format(_list))
        maximize(_list, p, q)
        #print("after max- {}".format(_list))
        p +=1
        q -=1
    return _list
    

def minimize(_list, p, q):
    #set the first element of array to min
    _min = _list[p]
    for i in range(p,q+1):
        #print(i)
        try:
            #temp = 0
            if(_list[i] < _min):
                temp = _min
                _min = _list[i]
                _list[i] = temp
        except Exception as e:
            print(e)
            print(i)
        _list[p] = _min

def maximize(_list, p, q):
    _max = _list[q]
    for i in range(p,q+1):
        try:
            temp = 0
            if(_list[i] > _max):
                temp = _list[i]
                _list[i] = _list[q]
                _list[q] = temp
        except Exception as e:
            print(i)
        _max = _list[q]

if __name__ == '__main__':
    #arr = [random.randint(1,100) for x in range(10)]
    print(sys.executable)
    arr = [random.randint(1,100) for x in range(100)]
    #arr = [78, 70, 65, 59, 41, 98, 30, 22, 40]
    print("array {}".format(arr))
    start = time.time()
    print("quicksort {} took {:f} seconds".format(quicksort(list(arr)), time.time()-start))
    start = time.time()
    print("min_max_Sort {}  took {:f} seconds".format( min_max_sort(list(arr)), time.time()-start))
    #assert quicksort(arr) == min_max_sort(arr)
    start = time.time()
    print("min_heap_sort {}  took {:f} seconds".format( sorting.maxheap(list(arr)), time.time()-start))