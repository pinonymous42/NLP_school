import MeCab
import pandas as pd
from add_list import add_list
from composite import composite

pd.set_option('display.unicode.east_asian_width', True)

#感情値辞書の読み込み(名詞)
pndic_1 = pd.read_csv('http://www.cl.ecei.tohoku.ac.jp/resources/sent_lex/pn.csv.m3.120408.trim', names=['word_pn_oth'])
pndic_2 = pndic_1['word_pn_oth'].str.split('\t', expand=True)
pndic_3 = pndic_2[(pndic_2[1] == 'p') | (pndic_2[1] == 'e') | (pndic_2[1] == 'n')]
pndic_4 = pndic_3.drop(pndic_3.columns[2], axis=1) #不要カラムの削除
pndic_4[1] = pndic_4[1].replace({'p':1, 'e':0, 'n':-1})
keys = pndic_4[0].tolist()#辞書の作成
values = pndic_4[1].tolist()
dic_noun = dict(zip(keys, values))

#感情値辞書の読み込み(用言)
pndic_1 = pd.read_csv(r"http://www.cl.ecei.tohoku.ac.jp/resources/sent_lex/wago.121808.pn",
                      names=["judge_type_word"])
pndic_2 = pndic_1["judge_type_word"].str.split('\t', expand=True)
pndic_2[0] = pndic_2[0].str.replace(r"\（.*\）", "", regex=True)
df_temp = pndic_2[1].str.split(" ", expand=True)
pndic_3 = pd.concat([df_temp, pndic_2[0]], axis=1)
pndic_4 = pndic_3[pndic_3[3].isnull()]
pndic_5 = pndic_4[0]
pndic_6 = pndic_5.drop_duplicates(keep='first')
pndic_6.columns = ["word", "judge"]
pndic_6["judge"] = pndic_6["judge"].replace({"ポジ":1, "ネガ":-1})
keys = pndic_6["word"].tolist()
values = pndic_6["judge"].tolist()
dic_declinable = dict(zip(keys, values))

dic = add_list(dic_noun, dic_declinable)

# print(dic_noun)


# text = 'クソまずい'

def parse(text):
    #文分割
    EOS = ['。', '.', '！？', '！', '？', '!?', '!', '?', '、']
    for eos in EOS:
        if (eos in text):
            lines = text.split(eos)
            break
    else:
        lines = text.split()

    #mecabを用いて形態素解析
    mecab = MeCab.Tagger("-Ochasen")
    word_list = []
    for l in lines:
        temp = []
        for v in mecab.parse(l).splitlines():
            if len(v.split()) >= 3:
                if v.split()[3][:2] in ['名詞', '動詞','副詞', '助詞']:
                    temp.append(v.split()[2])
                elif v.split()[3][:3] in ['形容詞', '助動詞', '感動詞', '接続詞', '連体詞', '代名詞']:
                    temp.append(v.split()[2])
                elif v.split()[3][:4] in ['形容動詞']:
                    temp.append(v.split()[2])
        word_list.append(temp)
    # 空の要素を削除
    word_list = [x for x in word_list if x != []]

    score = 0
    skip_flag = 0
    for x in word_list:
        for i in range(len(x)):
            if (skip_flag == 1):
                skip_flag = 0
                continue
            try:
                if (x[i].isdecimal()):
                    if (x[i + 1] == '％' or x[i + 1] == '点'):
                        if (int(x[i]) < 50):
                            score += -1
                        elif (50 <= int(x[i]) and int(x[i]) < 80):
                            score += 0
                        else:
                            score += 1
                    continue
                if (dic[x[i]] == 'reverse'):
                    j = i - 1
                    if (j >= 0 and dic[x[j]] == 'conjecture'):
                        continue
                    while (j >= 0 and dic[x[j]] == 0):
                        j -= 1
                    if (j < 0):
                        continue
                    score -= dic[x[j]]
                    score += dic[x[j]] * (-1)
                elif (dic[x[i]] == 'reset'):
                    score = 0
                elif (dic[x[i]] == 'conjecture'):
                    continue
                elif (dic[x[i]] == 'polarity'):
                    j = i - 1
                    while (j >= 0 and composite(x[j], x[i])):
                        j -= 1
                    if (j < 0):
                        score += 1
                        continue
                    score += composite(x[j], x[i])
                elif (type(dic[x[i]]) is float):
                    j = i + 1
                    while (j < len(x) and (dic[x[j]] == 0)):
                        j += 1
                    if (j >= len(x)):
                        continue
                    if (dic[x[j]] == 'polarity'):
                        k = j - 1
                        while (k >= 0 and composite(x[k], x[j]) == 0):
                            k -= 1
                        if (k < 0):
                            score += 1
                            continue
                        score += composite(x[k], x[j]) * dic[x[i]]
                        continue
                    score += dic[x[j]] * dic[x[i]]
                    i = j + 1
                    skip_flag = 1
                else:
                    score += dic[x[i]]
            except:
                continue

    if (score < 0):
        print(f'n({score})')
    elif (score == 0):
        print(f'e({score})')
    else:
        print(f'p({score})')

parse('美味しい')