from pycparser import parse_file
import random
import numpy as np


def analyze_constraint(arg, constraint):
    if arg == None:
        return
    arg_left, arg_right, arg_op = analyze_constraint_helper(arg)
    analyze_constraint(arg_left, constraint)
    constraint.append(arg_op)
    constraint.append(' ')
    analyze_constraint(arg_right, constraint)


def analyze_constraint_helper(arg):
    if arg.__class__.__name__ == 'Constant':
        return None, None, arg.value
    if arg.__class__.__name__ == 'ID':
        return None, None, arg.name
    if arg.__class__.__name__ == 'UnaryOp':
        _, _, n = analyze_constraint_helper(arg.expr)
        return None, None, '-' + n
    if arg.__class__.__name__ == 'BinaryOp':
        return arg.left, arg.right, arg.op
    if arg.__class__.__name__ == 'ArrayRef':
        _, _, n = analyze_constraint_helper(arg.name)
        _, _, f = analyze_constraint_helper(arg.subscript)
        return None, None, n + '[' + f + ']'
    if arg.__class__.__name__ == 'StructRef':
        f = arg.field.name
        _, _, n = analyze_constraint_helper(arg.name)
        return None, None, n + '.' + f
    if arg.__class__.__name__ == 'FuncCall':
        n = arg.name.name
        n = n + '('
        for a in arg.args.exprs:
            _, _, op = analyze_constraint_helper(a)
            n = n + op + ','
        n = n[:-1]
        n = n + ')'
        return None, None, n


def analyze_structure(arg, struct):
    body = dict()
    for arg in arg.type:
        l = len(arg.name)
        n = [arg.name]
        t = list()
        arg = arg.type
        _n, _t = analyze_declaration(arg, struct, n, t, l)
        for i in range(len(_n)):
            body[_n[i]] = _t[i]
    return body

def analyze_declaration(arg, struct, n, t, l):
        if arg.__class__.__name__ == 'FuncDecl':  # 如果参数的类名为'FuncDecl'，则返回空值
            return None, None
        if arg.__class__.__name__ == 'IdentifierType':  # 如果参数的类名为'IdentifierType'
            t.append(arg.names[0])  # 将参数的名称添加到t列表中
            return n, t
        if arg.__class__.__name__ == 'TypeDecl':  # 如果参数的类名为'TypeDecl'
            _n = list()
            for i in n:
                _n.append(i + arg.declname[l:])  # 将参数的名称添加到_n列表中
            n = _n
            n, t = analyze_declaration(arg.type, struct, n, t, l)  # 递归调用分析声明函数
            return n, t
        if arg.__class__.__name__ == 'Struct':  # 如果参数的类名为'Struct'
            struct_name = arg.name
            _n = list()
            for i in n:
                for j in range(len(struct[struct_name])):
                    _n.append(i + '.' + list(struct[struct_name].keys())[j])  # 将结构体中的成员名称添加到_n列表中
                    t.append(list(struct[struct_name].values())[j])  # 将结构体中的成员类型添加到t列表中
            n = _n
            return n, t
        if arg.__class__.__name__ == 'ArrayDecl':  # 如果参数的类名为'ArrayDecl'
            num = arg.dim.value  # 获取数组的维度值
            arg = arg.type
            _n, _t = analyze_declaration(arg, struct, n, t, l)  # 递归调用分析声明函数
            n_temp = list()
            for i in range(int(num)):
                for j in n:
                    curr = j + '[' + str(i) + ']'  # 为数组添加索引
                    for k in range(len(_n)):
                        n_temp.append(curr + _n[k][l:])  # 将数组成员的名称添加到n_temp列表中
                        t.append(_t[k])  # 将数组成员的类型添加到t列表中
            n = n_temp
            return n, t
        if arg.__class__.__name__ == 'PtrDecl':  # 如果参数的类名为'PtrDecl'
            arg = arg.type
            _n, _t = analyze_declaration(arg, struct, n, t, l)  # 递归调用分析声明函数
            t_temp = list()
            for k in _t:
                t_temp.append(k + '_ptr')  # 将指针类型的名称添加到t_temp列表中
            n = _n
            t = t_temp
            return n, t
# 分析原始文件
def analyze_code(path):
    structures = dict()
    constraint_lines = list()
    input_variables = dict()
    ast_result = parse_file(path)
    for argument in ast_result:
        if argument.__class__.__name__ == 'Typedef':
            body = analyze_structure(argument.type, structures)
            structures[argument.name] = body
        if argument.__class__.__name__ == 'Decl':
            name_length = len(argument.name)
            names = [argument.name]
            types = list()
            argument = argument.type
            analyzed_names, analyzed_types = analyze_declaration(argument, structures, names, types, name_length)
            if analyzed_names is not None:
                for i in range(len(analyzed_names)):
                    input_variables[analyzed_names[i]] = analyzed_types[i]
        if argument.__class__.__name__ == 'FuncDef':
            argument = argument.body
            for block_item in argument.block_items:
                constraints = list()
                analyze_constraint(block_item, constraints)
                constraint_line = " " + "".join(constraints)
                constraint_lines.append(constraint_line)
    return input_variables, constraint_lines

# 生成关联矩阵
import numpy as np


def generate_matrix(input_variables, constraint):
    # 创建一个全零矩阵，行数为约束条件的数量加1，列数为输入变量的数量
    matrix = np.zeros((len(constraint) + 1, len(input_variables)))

    # 遍历每个约束条件
    for i in range(len(constraint)):
        j = 0
        n = ''

        # 判断约束条件中是否包含'GAUSSIAN'
        if 'GAUSSIAN' in constraint[i]:
            # 找到','的索引位置
            idx = constraint[i].find(',')
            # 提取出'GAUSSIAN'后面的参数n
            n = constraint[i][10:idx]

        # 遍历输入变量
        for variable in input_variables:
            # 如果约束条件中包含当前变量，则在矩阵对应位置置为1
            if ' ' + variable + ' ' in constraint[i]:
                matrix[i, j] = 1
            # 如果约束条件中包含'GAUSSIAN'并且变量等于n，则在矩阵对应位置置为1
            if 'GAUSSIAN' in constraint[i] and variable == n:
                matrix[i, j] = 1
            j += 1

    j = 0
    # 遍历输入变量
    for variable in input_variables:
        # 如果变量的类型为'double'，则在矩阵最后一行对应位置置为1
        if input_variables[variable] == 'double':
            matrix[-1, j] = 1
        j += 1

    return matrix


def find_root(root, num):
    if root[int(num)] != num:
        root[int(num)] = find_root(root, int(root[num]))
    return root[int(num)]


def merge_roots(root, num1, num2):
    link(root, find_root(root, num1), find_root(root, num2))


def link(root, num1, num2):
    if num1 < num2:
        root[int(num2)] = num1
    else:
        root[int(num1)] = num2


# 分离矩阵
def split_matrix(matrix, input_variables):
    roots = np.zeros(len(input_variables))  # 初始化并查集的根节点数组
    for i in range(len(input_variables)):
        roots[i] = i

    for i in range(matrix.shape[0] - 1):
        for j in range(matrix.shape[1]):
            for k in range(j + 1, matrix.shape[1]):
                if matrix[i, j] + matrix[i, k] == 2:  # 如果两列都为1，则合并它们的根节点
                    merge_roots(roots, j, k)

    bubble_input = dict()  # 保存每个冒泡的输入变量
    bubble_matrix = dict()  # 保存每个冒泡的矩阵

    for i in range(roots.shape[0]):
        if bubble_input.get(find_root(roots, i)) is None:  # 如果根节点对应的冒泡不存在，则创建新的冒泡
            temp_matrix = list()  # 临时保存冒泡的矩阵
            temp_input = dict()  # 临时保存冒泡的输入变量
            temp_matrix.append(matrix[:, i])  # 将当前列加入冒泡的矩阵
            variable_name = list(input_variables.keys())[i]  # 获取变量名
            temp_input[variable_name] = input_variables[variable_name]  # 将变量名和值加入冒泡的输入变量
            bubble_input[roots[i]] = temp_input  # 将冒泡的输入变量保存到字典中
            bubble_matrix[roots[i]] = temp_matrix  # 将冒泡的矩阵保存到字典中
        else:  # 如果根节点对应的冒泡存在，则将当前列加入冒泡的矩阵
            bubble_matrix[int(find_root(roots, i))].append(matrix[:, i])
            variable_name = list(input_variables.keys())[i]
            bubble_input[int(find_root(roots, i))][variable_name] = input_variables[variable_name]

    for i in bubble_matrix:
        bubble_matrix[i].append(np.zeros(len(bubble_matrix[i][0])))
        bubble_matrix[i] = np.array(bubble_matrix[i]).T

    bubble_matrix = list(bubble_matrix.values())
    bubble_input = list(bubble_input.values())

    modified_bubble_input = list()
    for b in bubble_input:
        modified_bubble_input.append(list(b.keys()))

    return modified_bubble_input, bubble_matrix
