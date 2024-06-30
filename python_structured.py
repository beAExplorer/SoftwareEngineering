# -*- coding: utf-8 -*-
import re  # 导入正则表达式模块
import ast  # 导入抽象语法树模块
import sys  # 导入系统模块
import token  # 导入token模块
import tokenize  # 导入tokenize模块

from nltk import wordpunct_tokenize  # 从nltk中导入wordpunct_tokenize
from io import StringIO  # 从io模块中导入StringIO

# 骆驼命名法处理模块
import inflection

# 词性还原模块
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer

wnler = WordNetLemmatizer()

# 词干提取模块
from nltk.corpus import wordnet

#############################################################################

# 定义变量赋值模式的正则表达式
PATTERN_VAR_EQUAL = re.compile("(\s*[_a-zA-Z][_a-zA-Z0-9]*\s*)(,\s*[_a-zA-Z][_a-zA-Z0-9]*\s*)*=")
# 定义for循环中的变量模式的正则表达式
PATTERN_VAR_FOR = re.compile("for\s+[_a-zA-Z][_a-zA-Z0-9]*\s*(,\s*[_a-zA-Z][_a-zA-Z0-9]*)*\s+in")


def repair_program_io(code):
    # 定义模式，用于匹配Jupyter Notebook中的输入输出
    pattern_case1_in = re.compile("In ?\[\d+]: ?")  # Jupyter输入标记
    pattern_case1_out = re.compile("Out ?\[\d+]: ?")  # Jupyter输出标记
    pattern_case1_cont = re.compile("( )+\.+: ?")  # Jupyter续行标记

    # 定义模式，用于匹配Python交互式解释器中的输入
    pattern_case2_in = re.compile(">>> ?")  # Python解释器输入标记
    pattern_case2_cont = re.compile("\.\.\. ?")  # Python解释器续行标记

    # 将所有模式放入一个列表
    patterns = [pattern_case1_in, pattern_case1_out, pattern_case1_cont,
                pattern_case2_in, pattern_case2_cont]

    # 将代码按行分割
    lines = code.split("\n")
    # 初始化每行的标记，初始值为0
    lines_flags = [0 for _ in range(len(lines))]

    # 用于存储修复后的代码
    code_list = []

    # 匹配每一行的模式
    for line_idx in range(len(lines)):
        line = lines[line_idx]
        for pattern_idx in range(len(patterns)):
            if re.match(patterns[pattern_idx], line):
                lines_flags[line_idx] = pattern_idx + 1
                break
    lines_flags_string = "".join(map(str, lines_flags))

    bool_repaired = False

    # 修复代码
    if lines_flags.count(0) == len(lines_flags):  # 如果没有需要修复的行
        repaired_code = code
        code_list = [code]
        bool_repaired = True

    # 如果符合特定模式
    elif re.match(re.compile("(0*1+3*2*0*)+"), lines_flags_string) or \
            re.match(re.compile("(0*4+5*0*)+"), lines_flags_string):
        repaired_code = ""
        pre_idx = 0
        sub_block = ""
        if lines_flags[0] == 0:
            flag = 0
            while (flag == 0):
                repaired_code += lines[pre_idx] + "\n"
                pre_idx += 1
                flag = lines_flags[pre_idx]
            sub_block = repaired_code
            code_list.append(sub_block.strip())
            sub_block = ""  # 清空子块

        for idx in range(pre_idx, len(lines_flags)):
            if lines_flags[idx] != 0:
                repaired_code += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

                # 清空子块记录
                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] == 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

            else:
                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] != 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += lines[idx] + "\n"

        # 避免遗漏最后一个子块
        if len(sub_block.strip()):
            code_list.append(sub_block.strip())

        if len(repaired_code.strip()) != 0:
            bool_repaired = True

    # 如果不符合特定模式，删除Out标记后的0标记行
    if not bool_repaired:
        repaired_code = ""
        sub_block = ""
        bool_after_Out = False
        for idx in range(len(lines_flags)):
            if lines_flags[idx] != 0:
                if lines_flags[idx] == 2:
                    bool_after_Out = True
                else:
                    bool_after_Out = False
                repaired_code += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] == 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

            else:
                if not bool_after_Out:
                    repaired_code += lines[idx] + "\n"

                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] != 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += lines[idx] + "\n"

    return repaired_code, code_list


def get_vars(ast_root):
    # 获取抽象语法树中的所有变量
    return sorted(
        {node.id for node in ast.walk(ast_root) if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load)})


def get_vars_heuristics(code):
    # 使用启发式方法获取变量名
    varnames = set()
    code_lines = [_ for _ in code.split("\n") if len(_.strip())]

    # 最佳努力解析
    start = 0
    end = len(code_lines) - 1
    bool_success = False
    while not bool_success:
        try:
            root = ast.parse("\n".join(code_lines[start:end]))
        except:
            end -= 1
        else:
            bool_success = True
    varnames = varnames.union(set(get_vars(root)))

    # 处理剩余代码行
    for line in code_lines[end:]:
        line = line.strip()
        try:
            root = ast.parse(line)
        except:
            # 匹配变量赋值模式
            pattern_var_equal_matched = re.match(PATTERN_VAR_EQUAL, line)
            if pattern_var_equal_matched:
                match = pattern_var_equal_matched.group()[:-1]  # 去除等号
                varnames = varnames.union(set([_.strip() for _ in match.split(",")]))

            # 匹配for循环中的变量模式
            pattern_var_for_matched = re.search(PATTERN_VAR_FOR, line)
            if pattern_var_for_matched:
                match = pattern_var_for_matched.group()[3:-2]  # 去除for和in
                varnames = varnames.union(set([_.strip() for _ in match.split(",")]))

        else:
            varnames = varnames.union(get_vars(root))

    return varnames


def PythonParser(code):
    bool_failed_var = False
    bool_failed_token = False

    try:
        root = ast.parse(code)
        varnames = set(get_vars(root))
    except:
        repaired_code, _ = repair_program_io(code)
        try:
            root = ast.parse(repaired_code)
            varnames = set(get_vars(root))
        except:
            bool_failed_var = True
            varnames = get_vars_heuristics(code)

    tokenized_code = []

    def first_trial(_code):

        if len(_code) == 0:
            return True
        try:
            g = tokenize.generate_tokens(StringIO(_code).readline)
            term = next(g)
        except:
            return False
        else:
            return True

    bool_first_success = first_trial(code)
    while not bool_first_success:
        code = code[1:]
        bool_first_success = first_trial(code)
    g = tokenize.generate_tokens(StringIO(code).readline)
    term = next(g)

    bool_finished = False
    while not bool_finished:
        term_type = term[0]
        lineno = term[2][0] - 1
        posno = term[3][1] - 1
        if token.tok_name[term_type] in {"NUMBER", "STRING", "NEWLINE"}:
            tokenized_code.append(token.tok_name[term_type])
        elif not token.tok_name[term_type] in {"COMMENT", "ENDMARKER"} and len(term[1].strip()):
            candidate = term[1].strip()
            if candidate in varnames:
                tokenized_code.append("_VAR_")
            elif candidate in {"==", "!=", "<=", ">=", ">", "<"}:
                tokenized_code.append("_COMPARE_")
            elif candidate in {"True", "False"}:
                tokenized_code.append("_BOOL_")
            elif candidate == "=":
                tokenized_code.append("_EQUAL_")
            else:
                tokenized_code.append(candidate)
        try:
            term = next(g)
        except:
            bool_finished = True
        else:
            if term[0] == token.ENDMARKER:
                bool_finished = True

    return tokenized_code, bool_failed_var


def FunctionParser(code):
    bool_failed_var = False
    bool_failed_token = False

    # 修复代码
    try:
        root = ast.parse(code)
        varnames = set(get_vars(root))
    except:
        repaired_code, _ = repair_program_io(code)
        try:
            root = ast.parse(repaired_code)
            varnames = set(get_vars(root))
        except:
            bool_failed_var = True
            varnames = get_vars_heuristics(code)

    tokenized_code = []
    try:
        g = tokenize.generate_tokens(StringIO(code).readline)
        term = next(g)
    except:
        bool_failed_token = True
    else:
        bool_finished = False
        while not bool_finished:
            term_type = term[0]
            lineno = term[2][0] - 1
            posno = term[3][1] - 1
            if token.tok_name[term_type] in {"NUMBER", "STRING", "NEWLINE"}:
                tokenized_code.append(token.tok_name[term_type])
            elif not token.tok_name[term_type] in {"COMMENT", "ENDMARKER"} and len(term[1].strip()):
                candidate = term[1].strip()
                if candidate in varnames:
                    tokenized_code.append("_VAR_")
                elif candidate in {"==", "!=", "<=", ">=", ">", "<"}:
                    tokenized_code.append("_COMPARE_")
                elif candidate in {"True", "False"}:
                    tokenized_code.append("_BOOL_")
                elif candidate == "=":
                    tokenized_code.append("_EQUAL_")
                else:
                    tokenized_code.append(candidate)
            try:
                term = next(g)
            except:
                bool_finished = True
            else:
                if term[0] == token.ENDMARKER:
                    bool_finished = True

    return tokenized_code, bool_failed_var, bool_failed_token
