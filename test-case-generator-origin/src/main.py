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


def mutate(constraint, or_cons):
    while True:
        idx = random.randint(0, len(constraint) - 1)
        if (constraint[idx] in or_cons):
            continue
        if constraint[idx].find('>') != -1:
            constraint[idx] = constraint[idx].replace('>', '<')
            return constraint
        if constraint[idx].find('<') != -1:
            constraint[idx] = constraint[idx].replace('<', '>')
            return constraint
        if constraint[idx].find('>=') != -1:
            constraint[idx] = constraint[idx].replace('>=', '<=')
            return constraint
        if constraint[idx].find('<=') != -1:
            constraint[idx] = constraint[idx].replace('<=', '>=')
            return constraint
        if constraint[idx].find('==') != -1:
            constraint[idx] = constraint[idx].replace('==', '!=')
            return constraint
        if constraint[idx].find('!=') != -1:
            constraint[idx] = constraint[idx].replace('!=', '==')
            return constraint


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

    # 获取正例和负例个数
    pos_num = params['p']
    neg_num = params['n']

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

    # 读取原始文件，解析出输入和约束
    time_start = time.time()
    input, constraint = analyze_code("originFile.c")
    input, pos_constraint, or_cons = revised(input, constraint)

    neg_constraint = mutate(pos_constraint.copy(), or_cons)
    pos_matrix = gen_matrix(input, pos_constraint)
    neg_matrix = gen_matrix(input, neg_constraint)
    pos_bubble_input, pos_bubble_matrix = matrix_split(pos_matrix, input, pos_constraint)
    neg_bubble_input, neg_bubble_matrix = matrix_split(neg_matrix, input, neg_constraint)
    pos_n = len(pos_bubble_matrix)
    neg_n = len(neg_bubble_matrix)
    pos_part_num = math.ceil(5 * pos_num ** (1 / pos_n))
    neg_part_num = math.ceil(5 * neg_num ** (1 / neg_n))
    pos_bubbles = list()
    pos_results = list()
    neg_bubbles = list()
    neg_results = list()

    pool = getPool()

    time_init = time.time()
    print("文件解析及初始化完成（{:.3f}s）...".format(time_init - time_start))

    # solute
    for i in range(len(pos_bubble_matrix)):
        pos_result = pool.apply_async(task, (pos_bubble_matrix, pos_constraint, pos_bubble_input, i, pos_part_num),
                                      error_callback=print_error)
        pos_results.append(pos_result)
    for i in range(len(neg_bubble_matrix)):
        neg_result = pool.apply_async(task, (neg_bubble_matrix, neg_constraint, neg_bubble_input, i, neg_part_num),
                                      error_callback=print_error)
        neg_results.append(neg_result)

    pool.close()
    pool.join()

    for result in pos_results:
        pos_bubbles.append(result.get())
    for result in neg_results:
        neg_bubbles.append(result.get())

    time_solute = time.time()
    print("约束求解完成（{:.3f}s）...".format(time_solute - time_init))

    # merge and generate
    pool = getPool()
    pos_count = generator(pos_bubbles, positive_case, pos_num, pool)
    neg_count = generator(neg_bubbles, negative_case, neg_num, pool)
    pool.close()
    pool.join()

    count = pos_count + neg_count
    time_gen = time.time()
    print("生成测试用例完成（{:.3f}s）...".format(time_gen - time_solute))
    print(
        "总计用时：{:.3f}s\n测试用例个数：{}，正测试用例:{}个，负测试用例:{}个，正测试用例比例:{:.3f}%\n平均速度:{:.3f}个/s".format(
            time_gen - time_start, count, pos_count, neg_count, pos_count / count * 100,
            count / (time_gen - time_start)))
