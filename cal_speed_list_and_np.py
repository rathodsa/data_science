import time
import numpy as np

size_of_vec = 1000000

def pure_python_verion():
    python_time = time.time()
    my_list1 = range(size_of_vec)
    my_list2 = range(size_of_vec)
    my_sum = [my_list1[i] + my_list2[i] for i in range(int(size_of_vec))]
    return time.time() - python_time

def numpy_version():
    python_time = time.time()
    my_list1 = np.arange(size_of_vec)
    my_list2 = np.arange(size_of_vec)
    my_np_sum = my_list1 + my_list2
    return time.time() - python_time

python_time_taken = pure_python_verion()
print(f"time taken by the python version is : {python_time_taken}")

nump_time_taken = numpy_version()
print(f"time taken by the numpy is : {nump_time_taken}")

