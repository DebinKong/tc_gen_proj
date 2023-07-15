import os
import multiprocessing as mp

count = 0

def task(path, temp):
    with open(path, 'w') as f:
        for line in temp:
            f.write(line)

def backtrace(output_path, bubbles, index, temp, num, pool):
    global count
    if count == num:
        return
    if (index == len(bubbles)):
        pool.apply_async(task, (output_path+'/case'+str(count)+'.txt', temp.copy()), error_callback=print_error)
        count = count + 1
        return
    for content in bubbles[index]:
        temp.append(content)
        backtrace(output_path, bubbles, index+1, temp, num, pool)
        temp.pop()

def generat_testcase(bubbles, out_path, num, pool):
    global count
    count = 0
    backtrace(out_path, bubbles, 0, [], num, pool)
    return count

def print_error(value):
    print('error:', value)