import pickle  # 用于序列化和反序列化Python对象
from collections import Counter  # 用于计数

# 加载pickle文件
def load_pickle(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f, encoding='iso-8859-1')  # 以iso-8859-1编码方式加载数据
    return data

# 根据qid将数据分为单个和多个类别
def split_data(total_data, qids):
    result = Counter(qids)  # 统计每个qid出现的次数
    total_data_single = []  # 存储单个qid的数据
    total_data_multiple = []  # 存储多个qid的数据
    for data in total_data:
        if result[data[0][0]] == 1:
            total_data_single.append(data)  # 如果qid只出现一次，归为单个类别
        else:
            total_data_multiple.append(data)  # 如果qid出现多次，归为多个类别
    return total_data_single, total_data_multiple

# 处理staqc数据，将其分为单个和多个类别，并保存到指定路径
def data_staqc_processing(filepath, save_single_path, save_multiple_path):
    with open(filepath, 'r') as f:
        total_data = eval(f.read())  # 读取文件并解析为Python对象
    qids = [data[0][0] for data in total_data]  # 提取所有qid
    total_data_single, total_data_multiple = split_data(total_data, qids)  # 分割数据

    with open(save_single_path, "w") as f:
        f.write(str(total_data_single))  # 保存单个类别的数据
    with open(save_multiple_path, "w") as f:
        f.write(str(total_data_multiple))  # 保存多个类别的数据

# 处理大规模数据，将其分为单个和多个类别，并保存到指定路径
def data_large_processing(filepath, save_single_path, save_multiple_path):
    total_data = load_pickle(filepath)  # 加载pickle文件
    qids = [data[0][0] for data in total_data]  # 提取所有qid
    total_data_single, total_data_multiple = split_data(total_data, qids)  # 分割数据

    with open(save_single_path, 'wb') as f:
        pickle.dump(total_data_single, f)  # 保存单个类别的数据
    with open(save_multiple_path, 'wb') as f:
        pickle.dump(total_data_multiple, f)  # 保存多个类别的数据

# 将单个未标记的数据转换为带标签的数据
def single_unlabeled_to_labeled(input_path, output_path):
    total_data = load_pickle(input_path)  # 加载pickle文件
    labels = [[data[0], 1] for data in total_data]  # 给每条数据添加标签1
    total_data_sort = sorted(labels, key=lambda x: (x[0], x[1]))  # 按qid和标签排序
    with open(output_path, "w") as f:
        f.write(str(total_data_sort))  # 保存带标签的数据

if __name__ == "__main__":
    # staqc Python 数据处理
    staqc_python_path = './ulabel_data/python_staqc_qid2index_blocks_unlabeled.txt'
    staqc_python_single_save = './ulabel_data/staqc/single/python_staqc_single.txt'
    staqc_python_multiple_save = './ulabel_data/staqc/multiple/python_staqc_multiple.txt'
    data_staqc_processing(staqc_python_path, staqc_python_single_save, staqc_python_multiple_save)

    # staqc SQL 数据处理
    staqc_sql_path = './ulabel_data/sql_staqc_qid2index_blocks_unlabeled.txt'
    staqc_sql_single_save = './ulabel_data/staqc/single/sql_staqc_single.txt'
    staqc_sql_multiple_save = './ulabel_data/staqc/multiple/sql_staqc_multiple.txt'
    data_staqc_processing(staqc_sql_path, staqc_sql_single_save, staqc_sql_multiple_save)

    # 大规模 Python 数据处理
    large_python_path = './ulabel_data/python_codedb_qid2index_blocks_unlabeled.pickle'
    large_python_single_save = './ulabel_data/large_corpus/single/python_large_single.pickle'
    large_python_multiple_save = './ulabel_data/large_corpus/multiple/python_large_multiple.pickle'
    data_large_processing(large_python_path, large_python_single_save, large_python_multiple_save)

    # 大规模 SQL 数据处理
    large_sql_path = './ulabel_data/sql_codedb_qid2index_blocks_unlabeled.pickle'
    large_sql_single_save = './ulabel_data/large_corpus/single/sql_large_single.pickle'
    large_sql_multiple_save = './ulabel_data/large_corpus/multiple/sql_large_multiple.pickle'
    data_large_processing(large_sql_path, large_sql_single_save, large_sql_multiple_save)

    # 将单个未标记的数据转换为带标签的数据
    large_sql_single_label_save = './ulabel_data/large_corpus/single/sql_large_single_label.txt'
    large_python_single_label_save = './ulabel_data/large_corpus/single/python_large_single_label.txt'
    single_unlabeled_to_labeled(large_sql_single_save, large_sql_single_label_save)
    single_unlabeled_to_labeled(large_python_single_save, large_python_single_label_save)
