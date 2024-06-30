import pickle  # 导入pickle模块，用于序列化和反序列化Python对象

def get_vocab(corpus1, corpus2):
    """
    获取两个语料库中的词汇表。
    
    参数:
    corpus1: 第一个语料库
    corpus2: 第二个语料库
    
    返回:
    word_vocab: 两个语料库中所有词汇的集合
    """
    word_vocab = set()  # 初始化一个空的集合，用于存储词汇
    for corpus in [corpus1, corpus2]:  # 遍历两个语料库
        for i in range(len(corpus)):  # 遍历每个语料库中的每一条数据
            # 更新词汇集合，添加当前数据中的所有词汇
            word_vocab.update(corpus[i][1][0])
            word_vocab.update(corpus[i][1][1])
            word_vocab.update(corpus[i][2][0])
            word_vocab.update(corpus[i][3])
    print(len(word_vocab))  # 打印词汇集合的大小
    return word_vocab  # 返回词汇集合

def load_pickle(filename):
    """
    从pickle文件中加载数据。
    
    参数:
    filename: pickle文件的路径
    
    返回:
    data: 从pickle文件中加载的数据
    """
    with open(filename, 'rb') as f:  # 以二进制读模式打开文件
        data = pickle.load(f)  # 使用pickle加载数据
    return data  # 返回加载的数据

def vocab_processing(filepath1, filepath2, save_path):
    """
    处理词汇表，并将结果保存到文件中。
    
    参数:
    filepath1: 包含要排除词汇的文件路径
    filepath2: 包含语料库数据的文件路径
    save_path: 保存结果文件的路径
    """
    with open(filepath1, 'r') as f:  # 以读模式打开第一个文件
        total_data1 = set(eval(f.read()))  # 读取文件内容，并将其转换为集合
    with open(filepath2, 'r') as f:  # 以读模式打开第二个文件
        total_data2 = eval(f.read())  # 读取文件内容，并将其转换为Python对象

    word_set = get_vocab(total_data2, total_data2)  # 获取语料库中的词汇集合

    excluded_words = total_data1.intersection(word_set)  # 获取需要排除的词汇集合
    word_set = word_set - excluded_words  # 从词汇集合中移除需要排除的词汇

    print(len(total_data1))  # 打印需要排除的词汇集合的大小
    print(len(word_set))  # 打印处理后的词汇集合的大小

    with open(save_path, 'w') as f:  # 以写模式打开保存结果的文件
        f.write(str(word_set))  # 将词汇集合写入文件

if __name__ == "__main__":
    # 定义文件路径
    python_hnn = './data/python_hnn_data_teacher.txt'
    python_staqc = './data/staqc/python_staqc_data.txt'
    python_word_dict = './data/word_dict/python_word_vocab_dict.txt'

    sql_hnn = './data/sql_hnn_data_teacher.txt'
    sql_staqc = './data/staqc/sql_staqc_data.txt'
    sql_word_dict = './data/word_dict/sql_word_vocab_dict.txt'

    new_sql_staqc = './ulabel_data/staqc/sql_staqc_unlabled_data.txt'
    new_sql_large = './ulabel_data/large_corpus/multiple/sql_large_multiple_unlable.txt'
    large_word_dict_sql = './ulabel_data/sql_word_dict.txt'

    # 调用词汇处理函数，处理SQL词汇
    vocab_processing(sql_word_dict, new_sql_large, large_word_dict_sql)
