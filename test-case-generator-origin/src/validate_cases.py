from pathlib import Path

import matplotlib.pyplot as plt
from sympy.parsing.sympy_parser import parse_expr


def open_file(path,c_files):
    lines=[]
    for file in c_files:
        lines.append([])
        f = open('./case/'+path+'/' + file.name, 'r')
        item_list = f.read().split("\n")
        for item in item_list:
            if item is "":
                continue
            lines[-1].append(float(item.split("=")[1]))
    return lines

def validate_positive_cases(c_files, constraints, symbol):
    output = open_file('positive',c_files)
    var_dict = {}
    result_flag = 1
    unequal_constraints = []
    equal_constraints = []
    gaussian_output = []
    pop_constraints = []
    gaussian_constraints = []  
    for i in range(len(constraints)):  
        constraints[i] = constraints[i].replace("[", "_")
        constraints[i] = constraints[i].replace("].", "_")
        constraints[i] = constraints[i].replace(".", "_")
        constraints[i] = constraints[i].replace("]", "")
        if constraints[i].find("==") != -1:
            equal_constraints.append(constraints[i].split("=="))
            pop_constraints.append(i)
        elif constraints[i].find("!=") != -1:
            unequal_constraints.append(constraints[i].split("!="))
            pop_constraints.append(i)
        elif constraints[i].find("GAUSSIAN") != -1:
            con = constraints[i]
            pop_constraints.append(i)
            con_segment = con.split(",")
            var_name = con_segment[0].split("(")[1]
            mu = float(con_segment[1])
            sigma = float(con_segment[2].split(")")[0])
            gaussian_constraints.append([var_name, mu, sigma])
            gaussian_output.append([])
    for i in range(len(pop_constraints)):
        del constraints[pop_constraints.pop()]

    for i in range(len(symbol)):
        symbol[i] = symbol[i].replace("[", "_")
        symbol[i] = symbol[i].replace("].", "_")
        symbol[i] = symbol[i].replace(".", "_")
        symbol[i] = symbol[i].replace("]", "")

    for case_idx in range(len(output)):
        if len(output[case_idx]) is not len(symbol):
            raise ValueError("第" + str(case_idx) + "个样例的输入数据数量与变量数量不同，请检查")
        for i in range(len(symbol)):
            var_dict[symbol[i]] = output[case_idx][i]
        for i in range(len(constraints)):
            expr = parse_expr(constraints[i], var_dict)
            if not (isinstance(expr, bool) or expr.is_Boolean): 
                raise ValueError("第" + str(i) + "个不等式约束中有不在符号表中的变量")
            if not expr:
                print("第" + str(case_idx) + "个样例的不符合第" + str(i) + "个不等式约束")
                result_flag = 0
        for i in range(len(equal_constraints)):
            expr = parse_expr(equal_constraints[i][0], var_dict) - parse_expr(equal_constraints[i][1], var_dict)
            if not (isinstance(expr, float) or isinstance(expr, int) or expr.is_Number):
                raise ValueError("第" + str(i) + "个等式约束中有不在符号表中的变量")
            if abs(expr) > 0.001:
                print("第" + str(case_idx) + "个样例的不符合第" + str(i) + "个等式约束")
                result_flag = 0
        for i in range(len(unequal_constraints)):
            expr = parse_expr(unequal_constraints[i][0], var_dict) - parse_expr(unequal_constraints[i][1], var_dict)
            if not (isinstance(expr, float) or isinstance(expr, int) or expr.is_Number):
                raise ValueError("第" + str(i) + "个不等于约束中有不在符号表中的变量")
            if abs(expr) < 0.001:
                print("第" + str(case_idx) + "个样例的不符合第" + str(i) + "个不等于约束")
                result_flag = 0
        for i in range(len(gaussian_constraints)):
            gaussian_output[i].append(var_dict[gaussian_constraints[i][0]])
    if result_flag:
        print("通过！")
    for i in range(len(gaussian_constraints)):
        plt.hist(gaussian_output[i], color='blue',bins=50)
        plt.show()


def validate_negative_cases(c_files, constraints, symbol):
    output = open_file('negative',c_files)
    var_dict = {}
    result_flag = 1
    unequal_constraints = []
    equal_constraints = []
    pop_constraints = []
    for i in range(len(constraints)): 
        constraints[i] = constraints[i].replace("[", "_")
        constraints[i] = constraints[i].replace("].", "_")
        constraints[i] = constraints[i].replace(".", "_")
        constraints[i] = constraints[i].replace("]", "")
        if constraints[i].find("==") != -1:
            equal_constraints.append(constraints[i].split("=="))
            pop_constraints.append(i)
        elif constraints[i].find("!=") != -1:
            unequal_constraints.append(constraints[i].split("!="))
            pop_constraints.append(i)
        elif constraints[i].find("GAUSSIAN") != -1:
            pop_constraints.append(i)
    for i in range(len(pop_constraints)):
        del constraints[pop_constraints.pop()]

    for i in range(len(symbol)):
        symbol[i] = symbol[i].replace("[", "_")
        symbol[i] = symbol[i].replace("].", "_")
        symbol[i] = symbol[i].replace(".", "_")
        symbol[i] = symbol[i].replace("]", "")

 
    for case_idx in range(len(output)):
        case_pass_flag = 1
        if len(output[case_idx]) is not len(symbol):
            raise ValueError("第" + str(case_idx) + "个样例的输入数据数量与变量数量不同，请检查")
        for i in range(len(symbol)):
            var_dict[symbol[i]] = output[case_idx][i]
        for i in range(len(constraints)):
            expr = parse_expr(constraints[i], var_dict)
            if not (isinstance(expr, bool) or expr.is_Boolean):
                raise ValueError("第" + str(i) + "个不等式约束中有不在符号表中的变量")
            if not expr:
                case_pass_flag = 0
        for i in range(len(equal_constraints)):
            expr = parse_expr(equal_constraints[i][0], var_dict) - parse_expr(equal_constraints[i][1], var_dict)
            if not (isinstance(expr, float) or isinstance(expr, int) or expr.is_Number):
                raise ValueError("第" + str(i) + "个等式约束中有不在符号表中的变量")
            if abs(expr) > 0.001:
                case_pass_flag = 0
        for i in range(len(unequal_constraints)):
            expr = parse_expr(unequal_constraints[i][0], var_dict) - parse_expr(unequal_constraints[i][1], var_dict)
            if not (isinstance(expr, float) or isinstance(expr, int) or expr.is_Number):
                raise ValueError("第" + str(i) + "个不等于约束中有不在符号表中的变量")
            if abs(expr) < 0.001:
                case_pass_flag = 0
        if case_pass_flag:
            print("第" + str(case_idx) + "个样例符合所有约束")
            result_flag = 0
    if result_flag:
        print("全部存在问题！")



if __name__ == "__main__":
    print('正在初始化...')
    constraints_IO = open("./case/constraints.txt")
    constraints = constraints_IO.read().split("\n")
    constraints.pop()
    case0_file_IO = open("./case/positive/case0.txt")
    case0_file = case0_file_IO.read().split("\n")
    symbol = []
    for con in case0_file:
        symbol.append(con.split("=")[0])
    symbol.pop() 
    print('验证正测试用例中...')
    validate_positive_cases(Path("./case/positive").glob('case*.txt'), constraints.copy(), symbol)
    print('验证负测试用例中...')
    validate_negative_cases(Path("./case/negative").glob('case*.txt'), constraints.copy(), symbol)
