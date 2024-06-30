# -*- coding: utf-8 -*-
import re
import sqlparse # 解析SQL语句的库
import inflection # 处理字符串命名法的库
from nltk import pos_tag # 词性标注
from nltk.stem import WordNetLemmatizer # 词性还原
from nltk.corpus import wordnet # 获取单词的词性信息

# 初始化词性还原器
wnler = WordNetLemmatizer()

#############################################################################
# 常量定义
OTHER = 0
FUNCTION = 1
BLANK = 2
KEYWORD = 3
INTERNAL = 4
TABLE = 5
COLUMN = 6
INTEGER = 7
FLOAT = 8
HEX = 9
STRING = 10
WILDCARD = 11
SUBQUERY = 12
DUD = 13

# 常量对应的名称
ttypes = {
    0: "OTHER", 1: "FUNCTION", 2: "BLANK", 3: "KEYWORD", 4: "INTERNAL",
    5: "TABLE", 6: "COLUMN", 7: "INTEGER", 8: "FLOAT", 9: "HEX",
    10: "STRING", 11: "WILDCARD", 12: "SUBQUERY", 13: "DUD",
}

# 正则表达式扫描器，用于解析SQL中的特定模式
scanner = re.Scanner([
    (r"\[[^\]]*\]", lambda scanner, token: token),
    (r"\+", lambda scanner, token: "REGPLU"),
    (r"\*", lambda scanner, token: "REGAST"),
    (r"%", lambda scanner, token: "REGCOL"),
    (r"\^", lambda scanner, token: "REGSTA"),
    (r"\$", lambda scanner, token: "REGEND"),
    (r"\?", lambda scanner, token: "REGQUE"),
    (r"[\.~``;_a-zA-Z0-9\s=:\{\}\-\\]+", lambda scanner, token: "REFRE"),
    (r'.', lambda scanner, token: None),
])

#---------------------子函数1：代码的规则--------------------
def tokenizeRegex(s):
    # 使用正则表达式扫描器对输入字符串进行标记
    results = scanner.scan(s)[0]
    return results

#---------------------子函数2：代码的规则--------------------
class SqlangParser():
    @staticmethod
    def sanitizeSql(sql):
        # 规范化SQL语句
        s = sql.strip().lower()
        if not s[-1] == ";":
            s += ';'
        s = re.sub(r'\(', r' ( ', s)
        s = re.sub(r'\)', r' ) ', s)
        words = ['index', 'table', 'day', 'year', 'user', 'text']
        for word in words:
            s = re.sub(r'([^\w])' + word + '$', r'\1' + word + '1', s)
            s = re.sub(r'([^\w])' + word + r'([^\w])', r'\1' + word + '1' + r'\2', s)
        s = s.replace('#', '')
        return s

    def parseStrings(self, tok):
        # 解析字符串
        if isinstance(tok, sqlparse.sql.TokenList):
            for c in tok.tokens:
                self.parseStrings(c)
        elif tok.ttype == STRING:
            if self.regex:
                tok.value = ' '.join(tokenizeRegex(tok.value))
            else:
                tok.value = "CODSTR"

    def renameIdentifiers(self, tok):
        # 重命名标识符
        if isinstance(tok, sqlparse.sql.TokenList):
            for c in tok.tokens:
                self.renameIdentifiers(c)
        elif tok.ttype == COLUMN:
            if str(tok) not in self.idMap["COLUMN"]:
                colname = "col" + str(self.idCount["COLUMN"])
                self.idMap["COLUMN"][str(tok)] = colname
                self.idMapInv[colname] = str(tok)
                self.idCount["COLUMN"] += 1
            tok.value = self.idMap["COLUMN"][str(tok)]
        elif tok.ttype == TABLE:
            if str(tok) not in self.idMap["TABLE"]:
                tabname = "tab" + str(self.idCount["TABLE"])
                self.idMap["TABLE"][str(tok)] = tabname
                self.idMapInv[tabname] = str(tok)
                self.idCount["TABLE"] += 1
            tok.value = self.idMap["TABLE"][str(tok)]
        elif tok.ttype == FLOAT:
            tok.value = "CODFLO"
        elif tok.ttype == INTEGER:
            tok.value = "CODINT"
        elif tok.ttype == HEX:
            tok.value = "CODHEX"

    def __hash__(self):
        # 生成哈希值
        return hash(tuple([str(x) for x in self.tokensWithBlanks]))

    def __init__(self, sql, regex=False, rename=True):
        # 初始化解析器
        self.sql = SqlangParser.sanitizeSql(sql)
        self.idMap = {"COLUMN": {}, "TABLE": {}}
        self.idMapInv = {}
        self.idCount = {"COLUMN": 0, "TABLE": 0}
        self.regex = regex
        self.parseTreeSentinel = False
        self.tableStack = []

        self.parse = sqlparse.parse(self.sql)
        self.parse = [self.parse[0]]

        self.removeWhitespaces(self.parse[0])
        self.identifyLiterals(self.parse[0])
        self.parse[0].ptype = SUBQUERY
        self.identifySubQueries(self.parse[0])
        self.identifyFunctions(self.parse[0])
        self.identifyTables(self.parse[0])

        self.parseStrings(self.parse[0])

        if rename:
            self.renameIdentifiers(self.parse[0])

        self.tokens = SqlangParser.getTokens(self.parse)

    @staticmethod
    def getTokens(parse):
        # 获取解析后的标记
        flatParse = []
        for expr in parse:
            for token in expr.flatten():
                if token.ttype == STRING:
                    flatParse.extend(str(token).split(' '))
                else:
                    flatParse.append(str(token))
        return flatParse

    def removeWhitespaces(self, tok):
        # 移除空白字符
        if isinstance(tok, sqlparse.sql.TokenList):
            tmpChildren = []
            for c in tok.tokens:
                if not c.is_whitespace:
                    tmpChildren.append(c)
            tok.tokens = tmpChildren
            for c in tok.tokens:
                self.removeWhitespaces(c)

    def identifySubQueries(self, tokenList):
        # 识别子查询
        isSubQuery = False
        for tok in tokenList.tokens:
            if isinstance(tok, sqlparse.sql.TokenList):
                subQuery = self.identifySubQueries(tok)
                if (subQuery and isinstance(tok, sqlparse.sql.Parenthesis)):
                    tok.ttype = SUBQUERY
            elif str(tok) == "select":
                isSubQuery = True
        return isSubQuery

    def identifyLiterals(self, tokenList):
        # 识别字面量
        blankTokens = [sqlparse.tokens.Name, sqlparse.tokens.Name.Placeholder]
        blankTokenTypes = [sqlparse.sql.Identifier]
        for tok in tokenList.tokens:
            if isinstance(tok, sqlparse.sql.TokenList):
                tok.ptype = INTERNAL
                self.identifyLiterals(tok)
            elif (tok.ttype == sqlparse.tokens.Keyword or str(tok) == "select"):
                tok.ttype = KEYWORD
            elif (tok.ttype == sqlparse.tokens.Number.Integer or tok.ttype == sqlparse.tokens.Literal.Number.Integer):
                tok.ttype = INTEGER
            elif (tok.ttype == sqlparse.tokens.Number.Hexadecimal or tok.ttype == sqlparse.tokens.Literal.Number.Hexadecimal):
                tok.ttype = HEX
            elif (tok.ttype == sqlparse.tokens.Number.Float or tok.ttype == sqlparse.tokens.Literal.Number.Float):
                tok.ttype = FLOAT
            elif (tok.ttype == sqlparse.tokens.String.Symbol or tok.ttype == sqlparse.tokens.String.Single or tok.ttype == sqlparse.tokens.Literal.String.Single or tok.ttype == sqlparse.tokens.Literal.String.Symbol):
                tok.ttype = STRING
            elif (tok.ttype == sqlparse.tokens.Wildcard):
                tok.ttype = WILDCARD
            elif (tok.ttype in blankTokens or isinstance(tok, blankTokenTypes[0])):
                tok.ttype = COLUMN

    def identifyFunctions(self, tokenList):
        # 识别函数
        for tok in tokenList.tokens:
            if (isinstance(tok, sqlparse.sql.Function)):
                self.parseTreeSentinel = True
            elif (isinstance(tok, sqlparse.sql.Parenthesis)):
                self.parseTreeSentinel = False
            if self.parseTreeSentinel:
                tok.ttype = FUNCTION
            if isinstance(tok, sqlparse.sql.TokenList):
                self.identifyFunctions(tok)

    def identifyTables(self, tokenList):
        # 识别表
        if tokenList.ptype == SUBQUERY:
            self.tableStack.append(False)
        for i in range(len(tokenList.tokens)):
            prevtok = tokenList.tokens[i - 1]
            tok = tokenList.tokens[i]
            if isinstance(tok, sqlparse.sql.Identifier):
                if str(prevtok) in ["from", "join", "desc", "update"]:
                    tok.ttype = TABLE
                    if self.tableStack[-1] is not False:
                        self.tableStack[-1].append(str(tok))
                    else:
                        self.tableStack[-1] = [str(tok)]
            elif (isinstance(tok, sqlparse.sql.IdentifierList)):
                self.identifyTables(tok)
            elif (isinstance(tok, sqlparse.sql.TokenList)):
                self.identifyTables(tok)
        if tokenList.ptype == SUBQUERY:
            tokenList.tables = self.tableStack.pop()

#---------------------子函数3：代码的规则--------------------
def partofspeech(word):
    # 获取单词的词性
    try:
        pos = pos_tag([word])[0][1]
    except:
        pos = ""
    if pos.startswith('N'):
        return wordnet.NOUN
    elif pos.startswith('V'):
        return wordnet.VERB
    elif pos.startswith('J'):
        return wordnet.ADJ
    elif pos.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

#---------------------子函数4：代码的规则--------------------
def lemmatize_word(word, pos=None):
    # 词性还原
    if not pos:
        pos = partofspeech(word)
    return wnler.lemmatize(word, pos=pos)

#---------------------子函数5：代码的规则--------------------
def keyword_similarity(word, columnName):
    # 计算关键词相似性
    return lemmatize_word(word).lower() in [lemmatize_word(w).lower() for w in inflection.underscore(columnName).split("_")]

#---------------------子函数6：代码的规则--------------------
def add_sqldf_keywords():
    # 添加SQL关键字
    import pandasql
    kwlist = pandasql.__all__
    for kw in kwlist:
        if isinstance(kw, str):
            sqlparse.keywords.KEYWORDS[kw.upper()] = 'DML'
            sqlparse.keywords.KEYWORDS_COMMON[kw.upper()] = 'DML'
        elif isinstance(kw, tuple):
            kw, _ = kw
            sqlparse.keywords.KEYWORDS[kw.upper()] = 'DML'
            sqlparse.keywords.KEYWORDS_COMMON[kw.upper()] = 'DML'
