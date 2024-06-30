# 导入所需的库
import pickle  # 用于序列化和反序列化Python对象
import multiprocessing  # 用于并行处理
from python_structured import *  # 导入自定义的Python解析模块
from sqlang_structured import *  # 导入自定义的SQL解析模块

# 定义多进程处理Python查询解析的函数
def multipro_python_query(data_list):
    return [python_query_parse(line) for line in data_list]

# 定义多进程处理Python代码解析的函数
def multipro_python_code(data_list):
    return [python_code_parse(line) for line in data_list]

# 定义多进程处理Python上下文解析的函数
def multipro_python_context(data_list):
    result = []
    for line in data_list:
        if line == '-10000':
            result.append(['-10000'])  # 特殊标记处理
        else:
            result.append(python_context_parse(line))
    return result

# 定义多进程处理SQL查询解析的函数
def multipro_sqlang_query(data_list):
    return [sqlang_query_parse(line) for line in data_list]

# 定义多进程处理SQL代码解析的函数
def multipro_sqlang_code(data_list):
    return [sqlang_code_parse(line) for line in data_list]

# 定义多进程处理SQL上下文解析的函数
def multipro_sqlang_context(data_list):
    result = []
    for line in data_list:
        if line == '-10000':
            result.append(['-10000'])  # 特殊标记处理
        else:
            result.append(sqlang_context_parse(line))
    return result

# 定义数据解析函数
def parse(data_list, split_num, context_func, query_func, code_func):
    # 创建一个多进程池
    pool = multiprocessing.Pool()
    
    # 将数据列表按指定的分割数进行分割
    split_list = [data_list[i:i + split_num] for i in range(0, len(data_list), split_num)]
    
    # 使用多进程池处理上下文解析函数
    results = pool.map(context_func, split_list)
    context_data = [item for sublist in results for item in sublist]
    print(f'context条数：{len(context_data)}')

    # 使用多进程池处理查询解析函数
    results = pool.map(query_func, split_list)
    query_data = [item for sublist in results for item in sublist]
    print(f'query条数：{len(query_data)}')

    # 使用多进程池处理代码解析函数
    results = pool.map(code_func, split_list)
    code_data = [item for sublist in results for item in sublist]
    print(f'code条数：{len(code_data)}')

    # 关闭多进程池
    pool.close()
    pool.join()

    # 返回解析结果
    return context_data, query_data, code_data

# 定义主函数
def main(lang_type, split_num, source_path, save_path, context_func, query_func, code_func):
    # 读取源数据文件
    with open(source_path, 'rb') as f:
        corpus_lis = pickle.load(f)

    # 解析数据
    context_data, query_data, code_data = parse(corpus_lis, split_num, context_func, query_func, code_func)
    qids = [item[0] for item in corpus_lis]

    # 组织最终数据
    total_data = [[qids[i], context_data[i], code_data[i], query_data[i]] for i in range(len(qids))]

    # 保存解析后的数据
    with open(save_path, 'wb') as f:
        pickle.dump(total_data, f)

# 主程序入口
if __name__ == '__main__':
    # 定义Python STAQC数据的路径和保存路径
    staqc_python_path = './ulabel_data/python_staqc_qid2index_blocks_unlabeled.txt'
    staqc_python_save = '../hnn_process/ulabel_data/staqc/python_staqc_unlabled_data.pkl'

    # 定义SQL STAQC数据的路径和保存路径
    staqc_sql_path = './ulabel_data/sql_staqc_qid2index_blocks_unlabeled.txt'
    staqc_sql_save = './ulabel_data/staqc/sql_staqc_unlabled_data.pkl'

    # 处理Python STAQC数据
    main(python_type, split_num, staqc_python_path, staqc_python_save, multipro_python_context, multipro_python_query, multipro_python_code)
    
    # 处理SQL STAQC数据
    main(sqlang_type, split_num, staqc_sql_path, staqc_sql_save, multipro_sqlang_context, multipro_sqlang_query, multipro_sqlang_code)

    # 定义大规模Python数据的路径和保存路径
    large_python_path = './ulabel_data/large_corpus/multiple/python_large_multiple.pickle'
    large_python_save = '../hnn_process/ulabel_data/large_corpus/multiple/python_large_multiple_unlable.pkl'

    # 定义大规模SQL数据的路径和保存路径
    large_sql_path = './ulabel_data/large_corpus/multiple/sql_large_multiple.pickle'
    large_sql_save = './ulabel_data/large_corpus/multiple/sql_large_multiple_unlable.pkl'

    # 处理大规模Python数据
    main(python_type, split_num, large_python_path, large_python_save, multipro_python_context, multipro_python_query, multipro_python_code)
    
    # 处理大规模SQL数据
    main(sqlang_type, split_num, large_sql_path, large_sql_save, multipro_sqlang_context, multipro_sqlang_query, multipro_sqlang_code)
