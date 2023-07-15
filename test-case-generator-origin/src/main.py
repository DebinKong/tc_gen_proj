import argparse
import shutil

from find_solution import *
from gen_matrix import *
from gen_test_case import *

def print_error(value):
    print('error:', value)

def convert(output, symbol):
    contents = set()
    for i in range(len(output)):
        re = ""
        for j in range(len(output[i])):
            re = re + symbol[j] + '=' + str(output[i][j]) + '\n'
        contents.add(re)
    return contents

def task(bubble_matrix, constraint, bubble_input, idx, number=1):
    output = get_test_cases(bubble_matrix[idx].astype(int).copy(), constraint.copy(), bubble_input[idx].copy(),
                            number)
    c = convert(output, bubble_input[idx].copy())
    return c

def revised(input, constraint):
    _del = set()
    or_cons = list()
    for c in constraint:
        if '_LENGTH' in c:
            _del.add(c)
            upper = 999
            lower = 0
            field = None
            while '_LENGTH' in c:
                idx = c.find('_LENGTH')
                c = c[idx+8:]
                idx = c.find(')')
                field = c[:idx]
                c = c[idx+2:]
                idx = c.find('&&')
                if c[0] == '<':
                    if c[1] == ' ':
                        upper = int(c[1: idx]) - 1
                    if c[1] == '=':
                        upper = int(c[3: idx])
                if c[0] == '>':
                    if c[1] == ' ':
                        lower = int(c[1: idx]) + 1
                    if c[1] == '=':
                        lower = int(c[3: idx])
                c = c[idx+3:]
            num = random.randint(lower, upper)
            t = input.pop(field)
            idx = t.find('_ptr')
            t = t[: idx]
            for i in range(num):
                input[field+'['+str(i)+']'] = t
        else:
            if '||' in c:
                _del.add(c)
                _c = ''.join(c)
                temp = list()
                while '||' in _c:
                    idx = _c.find('||')
                    temp.append(_c[:idx])
                    _c = _c[idx+2:]
                temp.append(_c)
                index = random.randint(0, len(temp)-1)
                constraint.append(temp[index])
                or_cons.append(temp[index])
            if '&&' in c and c not in _del:
                _del.add(c)
                _c = ''.join(c)
                while '&&' in _c:
                    idx = _c.find('&&')
                    constraint.append(_c[:idx])
                    if c in or_cons:
                        or_cons.append(_c[:idx])
                    _c = _c[idx+2:]
                constraint.append(_c)
                if c in or_cons:
                    or_cons.remove(c)
                    or_cons.append(_c)
    for c in _del:
        constraint.remove(c)
    return input, constraint, or_cons
import random

def mutate_constraint(constraint, or_constraints):
    while True:
        index = random.randint(0, len(constraint) - 1)
        if constraint[index] in or_constraints:
            continue
        if '>' in constraint[index]:
            constraint[index] = constraint[index].replace('>', '<')
            break
        if '<' in constraint[index]:
            constraint[index] = constraint[index].replace('<', '>')
            break
        if '>=' in constraint[index]:
            constraint[index] = constraint[index].replace('>=', '<=')
            break
        if '<=' in constraint[index]:
            constraint[index] = constraint[index].replace('<=', '>=')
            break
        if '==' in constraint[index]:
            constraint[index] = constraint[index].replace('==', '!=')
            break
        if '!=' in constraint[index]:
            constraint[index] = constraint[index].replace('!=', '==')
    return constraint

import math

def process_data(bubble_matrix, constraint, bubble_input, part_num, pool):
    n = len(bubble_matrix)
    results = list()
    for i in range(len(bubble_matrix)):
        result = pool.apply_async(task, (bubble_matrix, constraint, bubble_input, i, part_num),
                                  error_callback=print_error)
        results.append(result)
    return results

# 获得初始化参数
def get_init_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=2000, help='生成正例个数，默认2000个')
    parser.add_argument('-n', type=int, default=2000, help='生成负例个数，默认2000个')
    return vars(parser.parse_args())

# 获取线程池
def getPool():
    # 线程池默认使用cpu核数
    return mp.Pool(int(mp.cpu_count()))

# 程序入口
if __name__ == "__main__":
    params = get_init_params()

    # 获取正例和负例数
    pos_total_num = params['p']
    neg_total_num = params['n']

    test_case_result_folder = './test_case_result'
    positive_case = test_case_result_folder + "/positive_case"
    negative_case = test_case_result_folder + "/negative_case"

    # 删除上一次生成的测试用例，以便重新生成
    if os.path.exists(test_case_result_folder):
        shutil.rmtree(test_case_result_folder)
    os.mkdir(test_case_result_folder)
    os.mkdir(positive_case)
    os.mkdir(negative_case)

    print("清理测试用例文件夹，准备解析原始文件")

    # 读取原始文件，解析出输入变量和约束
    time_start = time.time()
    input_var, constraint = analyze_code("origin_file.c")
    # 对原始约束进行化简，拆分&&、|｜约束，生成正例约束
    input_var, pos_constraint, or_constraint = revised(input_var, constraint.copy())
    # 正例约束写入文件，供验证程序使用
    with open(test_case_result_folder+'/constraints', 'w') as f:
        for line in pos_constraint:
            f.write(line + '\n')
    # 随机从正例约束中选择一条取非，生成负例约束
    neg_constraint = mutate_constraint(pos_constraint.copy(), or_constraint)
    # 生成约束-变量关联矩阵
    pos_incidence_matrix = generate_matrix(input_var, pos_constraint)
    neg_incicende_matrix = generate_matrix(input_var, neg_constraint)
    # 拆分关联矩阵
    pos_split_input, pos_split_matrix = split_matrix(pos_incidence_matrix, input_var)
    neg_split_input, neg_split_matrix = split_matrix(neg_incicende_matrix, input_var)

    time_init = time.time()
    print("文件解析及初始化完成（{:.3f}s）...".format(time_init - time_start))

    # 多线程求解正例约束
    pool = getPool()
    pos_n = len(pos_split_matrix)
    pos_part_num = math.ceil(5 * pos_total_num ** (1 / pos_n))
    pos_results = process_data(pos_split_matrix, pos_constraint, pos_split_input, pos_part_num, pool)
    # 多线程求解负例约束
    neg_n = len(neg_split_matrix)
    neg_part_num = math.ceil(5 * neg_total_num ** (1 / neg_n))
    neg_results = process_data(neg_split_matrix, neg_constraint, neg_split_input, neg_part_num, pool)

    pool.close()
    pool.join()
    pos_split_case = list()
    neg_split_case = list()
    for result in pos_results:
        pos_split_case.append(result.get())
    for result in neg_results:
        neg_split_case.append(result.get())

    time_solute = time.time()
    print("约束求解完成（{:.3f}s）...".format(time_solute - time_init))

    # merge and generate
    pool = getPool()
    pos_count = generator(pos_split_case, positive_case, pos_total_num, pool)
    neg_count = generator(neg_split_case, negative_case, neg_total_num, pool)
    pool.close()
    pool.join()

    count = pos_count + neg_count
    time_gen = time.time()
    print("生成测试用例完成（{:.3f}s）...".format(time_gen - time_solute))
    print(
        "总计用时：{:.3f}s\n测试用例个数：{}，正测试用例:{}个，负测试用例:{}个，正测试用例比例:{:.3f}%\n平均速度:{:.3f}个/s".format(
            time_gen - time_start, count, pos_count, neg_count, pos_count / count * 100,
            count / (time_gen - time_start)))
