# SoftwareEngineering
2023软件工程，完美编程规范。
# 词汇处理脚本

## 简介

这个项目包含用于处理两个语料库词汇表的Python脚本。该脚本读取包含需要排除的词汇的文件，并从两个语料库文件中提取所有词汇，排除指定词汇后，生成一个新的词汇表并保存到指定文件。

## 文件结构

```
.
├── data
│   ├── python_hnn_data_teacher.txt
│   ├── staqc
│   │   ├── python_staqc_data.txt
│   │   ├── sql_staqc_data.txt
│   └── word_dict
│       ├── python_word_vocab_dict.txt
│       └── sql_word_vocab_dict.txt
├── ulabel_data
│   ├── large_corpus
│   │   └── multiple
│   │       └── sql_large_multiple_unlable.txt
│   ├── sql_word_dict.txt
│   └── staqc
│       └── sql_staqc_unlabled_data.txt
├── script.py
└── README.md
```

## 脚本功能

### 函数

- `get_vocab(corpus1, corpus2)`
  - 功能：从两个语料库中提取所有词汇，返回一个包含所有词汇的集合。
  - 参数：
    - `corpus1`: 第一个语料库
    - `corpus2`: 第二个语料库
  - 返回值：包含两个语料库中所有词汇的集合。

- `load_pickle(filename)`
  - 功能：从指定的pickle文件中加载数据。
  - 参数：
    - `filename`: pickle文件的路径
  - 返回值：从pickle文件中加载的数据。

- `vocab_processing(filepath1, filepath2, save_path)`
  - 功能：处理词汇表，排除指定词汇，并将结果保存到文件中。
  - 参数：
    - `filepath1`: 包含要排除词汇的文件路径
    - `filepath2`: 包含语料库数据的文件路径
    - `save_path`: 保存结果文件的路径

### 主程序

在主程序中，定义了多个文件路径，并调用`vocab_processing`函数处理SQL语料库中的词汇。

## 使用方法

1. 将所需的文件放置在相应的目录中，如`data`和`ulabel_data`。
2. 运行脚本：
   ```bash
   python script.py
   ```
3. 处理后的词汇表将保存到指定的路径中。


## 依赖项

- Python 3.x
- `pickle`模块（标准库）

## 注意事项

- 请确保文件路径和文件内容格式正确，以免出现读取错误。
- 处理的词汇表较大时，可能需要较长的处理时间。

## 许可证

此项目遵循MIT许可证。

