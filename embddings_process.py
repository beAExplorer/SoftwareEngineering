import pickle  # 用于序列化和反序列化Python对象
import numpy as np  # 用于数值计算
from gensim.models import KeyedVectors  # 用于加载词向量模型

# 将词向量文件保存为二进制文件，以提高加载速度
def trans_bin(path1, path2):
    # 从文本格式加载词向量
    wv_from_text = KeyedVectors.load_word2vec_format(path1, binary=False)
    # 初始化相似度矩阵并保存为二进制文件
    wv_from_text.init_sims(replace=True)
    wv_from_text.save(path2)

# 构建新的词典和词向量矩阵
def get_new_dict(type_vec_path, type_word_path, final_vec_path, final_word_path):
    # 加载词向量模型
    model = KeyedVectors.load(type_vec_path, mmap='r')

    # 加载词汇表
    with open(type_word_path, 'r') as f:
        total_word = eval(f.read())

    # 初始化词典和词向量矩阵
    word_dict = ['PAD', 'SOS', 'EOS', 'UNK']  # 特殊标记，其中0 PAD_ID, 1 SOS_ID, 2 EOS_ID, 3 UNK_ID
    fail_word = []  # 未能找到词向量的词汇
    rng = np.random.RandomState(None)  # 随机数生成器

    # 特殊标记的词向量
    pad_embedding = np.zeros(shape=(1, 300)).squeeze()  # PAD的词向量全为0
    unk_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()  # UNK的词向量随机初始化
    sos_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()  # SOS的词向量随机初始化
    eos_embedding = rng.uniform(-0.25, 0.25, size=(1, 300)).squeeze()  # EOS的词向量随机初始化
    word_vectors = [pad_embedding, sos_embedding, eos_embedding, unk_embedding]

    # 加载每个词的词向量
    for word in total_word:
        try:
            word_vectors.append(model.wv[word])  # 加载词向量
            word_dict.append(word)
        except:
            fail_word.append(word)  # 记录未找到的词

    # 转换为numpy数组
    word_vectors = np.array(word_vectors)
    # 构建词典，词汇 -> 索引
    word_dict = dict(map(reversed, enumerate(word_dict)))

    # 保存词向量和词典
    with open(final_vec_path, 'wb') as file:
        pickle.dump(word_vectors, file)

    with open(final_word_path, 'wb') as file:
        pickle.dump(word_dict, file)

    print("完成")

# 获取词在词典中的位置索引
def get_index(type, text, word_dict):
    location = []
    if type == 'code':  # 处理代码类型文本
        location.append(1)  # 1 表示 SOS_ID
        len_c = len(text)
        if len_c + 1 < 350:
            if len_c == 1 and text[0] == '-1000':
                location.append(2)  # 2 表示 EOS_ID
            else:
                for i in range(0, len_c):
                    index = word_dict.get(text[i], word_dict['UNK'])  # 获取词的索引，未找到则使用 UNK
                    location.append(index)
                location.append(2)  # 2 表示 EOS_ID
        else:
            for i in range(0, 348):
                index = word_dict.get(text[i], word_dict['UNK'])  # 获取词的索引，未找到则使用 UNK
                location.append(index)
            location.append(2)  # 2 表示 EOS_ID
    else:  # 处理非代码类型文本
        if len(text) == 0:
            location.append(0)  # 0 表示 PAD_ID
        elif text[0] == '-10000':
            location.append(0)  # 0 表示 PAD_ID
        else:
            for i in range(0, len(text)):
                index = word_dict.get(text[i], word_dict['UNK'])  # 获取词的索引，未找到则使用 UNK
                location.append(index)

    return location

# 序列化训练、测试、验证语料
# 查询：25 上下文：100 代码：350
def serialization(word_dict_path, type_path, final_type_path):
    # 加载词典
    with open(word_dict_path, 'rb') as f:
        word_dict = pickle.load(f)

    # 加载语料
    with open(type_path, 'r') as f:
        corpus = eval(f.read())

    total_data = []

    for i in range(len(corpus)):
        qid = corpus[i][0]

        # 获取各部分的索引列表
        Si_word_list = get_index('text', corpus[i][1][0], word_dict)
        Si1_word_list = get_index('text', corpus[i][1][1], word_dict)
        tokenized_code = get_index('code', corpus[i][2][0], word_dict)
        query_word_list = get_index('text', corpus[i][3], word_dict)
        block_length = 4
        label = 0

        # 将各部分的索引列表扩展到固定长度
        Si_word_list = Si_word_list[:100] if len(Si_word_list) > 100 else Si_word_list + [0] * (100 - len(Si_word_list))
        Si1_word_list = Si1_word_list[:100] if len(Si1_word_list) > 100 else Si1_word_list + [0] * (100 - len(Si1_word_list))
        tokenized_code = tokenized_code[:350] + [0] * (350 - len(tokenized_code))
        query_word_list = query_word_list[:25] if len(query_word_list) > 25 else query_word_list + [0] * (25 - len(query_word_list))

        # 组织数据
        one_data = [qid, [Si_word_list, Si1_word_list], [tokenized_code], query_word_list, block_length, label]
        total_data.append(one_data)

    # 保存序列化数据
    with open(final_type_path, 'wb') as file:
        pickle.dump(total_data, file)

# 主程序入口
if __name__ == '__main__':
    # 词向量文件路径
    ps_path_bin = '../hnn_process/embeddings/10_10/python_struc2vec.bin'
    sql_path_bin = '../hnn_process/embeddings/10_8_embeddings/sql_struc2vec.bin'

    # ==========================最初基于Staqc的词典和词向量==========================

    python_word_path = '../hnn_process/data/word_dict/python_word_vocab_dict.txt'
    python_word_vec_path = '../hnn_process/embeddings/python/python_word_vocab_final.pkl'
    python_word_dict_path = '../hnn_process/embeddings/python/python_word_dict_final.pkl'

    sql_word_path = '../hnn_process/data/word_dict/sql_word_vocab_dict.txt'
    sql_word_vec_path = '../hnn_process/embeddings/sql/sql_word_vocab_final.pkl'
    sql_word_dict_path = '../hnn_process/embeddings/sql/sql_word_dict_final.pkl'

    # get_new_dict(ps_path_bin, python_word_path, python_word_vec_path, python_word_dict_path)
    # get_new_dict(sql_path_bin, sql_word_path, sql_word_vec_path, sql_word_dict_path)

    # =======================================最后打标签的语料========================================

    # sql 待处理语料地址
    new_sql_staqc = '../hnn_process/ulabel_data/staqc/sql_staqc_unlabled_data.txt'
    new_sql_large = '../hnn_process/ulabel_data/large_corpus/multiple/sql_large_multiple_unlable.txt'
    large_word_dict_sql = '../hnn_process/ulabel_data/sql_word_dict.txt'

    # sql最后的词典和对应的词向量
    sql_final_word_vec_path = '../hnn_process/ulabel_data/large_corpus/sql_word_vocab_final.pkl'
    sqlfinal_word_dict_path = '../hnn_process/ulabel_data/large_corpus/sql_word_dict_final.pkl'

    # get_new_dict(sql_path_bin, final_word_dict_sql, sql_final_word_vec_path, sql_final_word_dict_path)
    # get_new_dict_append(sql_path_bin, sql_word_dict_path, sql_word_vec_path, large_word_dict_sql, sql_final_word_vec_path,sql_final_word_dict_path)

    staqc_sql_f = '../hnn_process/ulabel_data/staqc/seri_sql_staqc_unlabled_data.pkl'
    large_sql_f = '../hnn_process/ulabel_data/large_corpus/multiple/seri_ql_large_multiple_unlable.pkl'
    # Serialization(sql_final_word_dict_path, new_sql_staqc, staqc_sql_f)
    # Serialization(sql_final_word_dict_path, new_sql_large, large_sql_f)

    # python
    new_python_staqc = '../hnn_process/ulabel_data/staqc/python_staqc_unlabled_data.txt'
    new_python_large = '../hnn_process/ulabel_data/large_corpus/multiple/python_large_multiple_unlable.txt'
    final_word_dict_python = '../hnn_process/ulabel_data/python_word_dict.txt'
    large_word_dict_python = '../hnn_process/ulabel_data/python_word_dict.txt'

    # python最后的词典和对应的词向量
    python_final_word_vec_path = '../hnn_process/ulabel_data/large_corpus/python_word_vocab_final.pkl'
    python_final_word_dict_path = '../hnn_process/ulabel_data/large_corpus/python_word_dict_final.pkl'

    # get_new_dict(ps_path_bin, final_word_dict_python, python_final_word_vec_path, python_final_word_dict_path)
    # get_new_dict_append(ps_path_bin, python_word_dict_path, python_word_vec_path, large_word_dict_python, python_final_word_vec_path,python_final_word_dict_path)

    # 处理成打标签的形式
    staqc_python_f = '../hnn_process/ulabel_data/staqc/seri_python_staqc_unlabled_data.pkl'
    large_python_f = '../hnn_process/ulabel_data/large_corpus/multiple/seri_python_large_multiple_unlable.pkl'
    # Serialization(python_final_word_dict_path, new_python_staqc, staqc_python_f)
    serialization(python_final_word_dict_path, new_python_large, large_python_f)

    print('序列化完毕')
    # test2(test_python1,test_python2,python_final_word_dict_path,python_final_word_vec_path)
