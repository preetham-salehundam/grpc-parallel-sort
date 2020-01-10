## References

[GRPC python ref guide](https://grpc.io/docs/tutorials/basic/python/)

## Scripts
### BASH

``` for i in {2..10}; do python parallel_sorting_client.py $i $(($i*100)); done;```

``` for i in {2..10}; do python parallel_sorting_client.py $i 100; done;```

## Algo

![flow chart](https://github.com/preetham-salehundam/grpc-parallel-sort/blob/master/misc/Screen%20Shot%202020-01-10%20at%2010.17.42%20AM.png)

## Architecture

![arch](https://github.com/preetham-salehundam/grpc-parallel-sort/blob/master/misc/Screen%20Shot%202020-01-10%20at%2010.23.02%20AM.png)


