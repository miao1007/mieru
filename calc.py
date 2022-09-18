import glob
import os
import re
import subprocess
import sys
from curses.ascii import NUL

dir_path = os.path.dirname(os.path.realpath(__file__))

book = sys.argv[1]


def putCountToMap(word, my_dict_white):
    if (word in my_dict_white):
        my_dict_white[word] += 1
    else:
        my_dict_white[word] = 1


conflict = set()


def removeCountToMap(word, my_dict_white):
    if (word in my_dict_white):
        if (my_dict_white[word] >= 0):
            conflict.add(word)
            my_dict_white[word] = NUL


def mapToTxt(map, file):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, 'w') as file:
        if isinstance(map, dict):
            sort = sorted(map.items(), key=lambda x: x[1])
            for k in sort:
                file.write("%s, %s\n" % (k[0], k[1]))
        else:
            for k in map:
                file.write("%s\n" % (k))


def sumMapValues(map):
    i = 0
    for key in map:
        i += map[key]
    return i


def parseText(word, whiteList, keepUnique):
    if (word in whiteList and keepUnique):
        return True
    elif (len(word) > 1 and word[-1] == 's' and word[:-1] in whiteList) \
            or (word[-2:] == 'ed' and word[:-2] in whiteList) \
            or (word[-2:] == 'es' and word[:-2] in whiteList):
        # runs -> run
        # watches/watched -> watch
        return True
    elif (word[-2:] == 'ed' and word[:-1] in whiteList) \
            or (word[-2:] == 'es' and word[:-1] in whiteList):
        # likes/liked -> like
        return True
    elif ((word[:-3] + 'f') in whiteList and word[-3:] == 'ves') \
            or ((word[:-3] + 'y') in whiteList and word[-3:] == 'ies') \
            or (word[:-4] in whiteList and word[-4:] == 'lled') \
            or (len(word) > 5 and word[:-5] in whiteList and word[-5:] == 'lling'):
        # knif -> knives
        # story -> stories
        # travel -> travelled
        # travel -> travelling
        return True
    else:
        return False


whiteList = {}
blackList = {}
# 白名单文件夹，已经掌握的单词，需要手动维护
for csv in glob.glob(dir_path + "/white/*"):
    with open(csv, 'r') as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
        for word in lines:
            s = re.search('^([a-z]+)(?:\s)', word)
            if (s is None):
                word = word
            else:
                word = s.group(1)
            if (word in whiteList):
                whiteList[word] += 1
            else:
                whiteList[word] = 1

# 自己整理的csv
spliter = re.compile(",\s?")

for csv in sorted(glob.glob(dir_path + "/ods/*/*")):
    with open(csv, 'r') as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
        for word in lines:
            s = spliter.split(word)
            if (len(s) >= 2):
                word = s[0].lower()
                if (s[1] == 'y'):
                    word = s[0]
                    putCountToMap(word, whiteList)
                if (s[1] == 'n'):
                    putCountToMap(word, blackList)
                    removeCountToMap(word, whiteList)


def removeInflection(invertedIndex):
    disjoint = set(invertedIndex.keys())
    for key in invertedIndex:
        key = key.lower()
        if parseText(key, invertedIndex, False):
            disjoint.discard(key)
    return disjoint


print('-----------------------------------------------')
print('======== All vocabulary list for now  =========')
print('-----------------------------------------------')
print('status    \tdiscrete\tredundant')
print('-----------------------------------------------')
print('white    \t' + str(len(removeInflection(whiteList))) + "    \t" + str(len(whiteList)))
print('black    \t' + str(len(removeInflection(blackList))) + "    \t" + str(len(blackList)))
print('-----------------------------------------------')

# 带分析的书
my_dict_black = {}
my_dict_white = {}
my_dict_unexplorered = {}

s = 'iconv -f utf-8 -t utf-8 -c ' + book + '''| tr "[:upper:]" "[:lower:]" \
  | perl -CS -p -e 's/[\p{Han}]/ /g' \
  | perl -CS -p -e 's/[[:punct:]]/ /g' \
  | sed 's/[[～＝＋×∗►　	]/ /g' \
  | sed -r 's/[^[:space:]]*[0-9][^[:space:]]* ?//g' \
  | sed -r 's/[^[:space:]]*[A|B|C|D][^[:space:]]* ?//g' \
  | tr ' ' '\n' \
  | egrep '[a-zA-z]{4,100}' \
  | sort
'''
print(s)
p = subprocess.check_output(["sh", '-c', s, book])

texts = p.decode("utf-8").splitlines()
print('book text count: ' + str(len(texts)))
for word in texts:
    word = word.lower()
    if parseText(word, whiteList, True):
        putCountToMap(word, my_dict_white)
    elif parseText(word, blackList, True):
        putCountToMap(word, my_dict_black)
        removeCountToMap(word, my_dict_white)
    else:
        putCountToMap(word, my_dict_unexplorered)

all = len(my_dict_unexplorered) + len(my_dict_black) + len(my_dict_white)

print('-----------------------------------------------')
print('=======  Book vocabulary list for now  ========')
print('-----------------------------------------------')
print('status    \tcount\tdistict\tweighted')
print('-----------------------------------------------')
print('unexplored\t' + str(len(my_dict_unexplorered))
      + '\t' + format((len(my_dict_unexplorered)) * 100 / all, '.2f') + "%"
      + '\t' + format(sumMapValues(my_dict_unexplorered) * 100 / len(texts), '.2f') + "%")
print('black     \t' + str(len(my_dict_black))
      + '\t' + format((len(my_dict_black)) * 100 / all, '.2f') + "%"
      + '\t' + format(sumMapValues(my_dict_black) * 100 / len(texts), '.2f') + "%")
print('white     \t' + str(len(my_dict_white))
      + '\t' + format((len(my_dict_white)) * 100 / all, '.2f') + "%"
      + '\t' + format(sumMapValues(my_dict_white) * 100 / len(texts), '.2f') + "%")
print('-----------------------------------------------')
print('all       \t' + str(all))

mapToTxt(conflict, 'out/conflict.csv')

# 输出当前整理的词频
mapToTxt(whiteList, 'out/whiteList.csv')
mapToTxt(blackList, 'out/blackList.csv')

# 输出不认识的单词与频率
out = book.rsplit(".", 1)[0]
mapToTxt(my_dict_unexplorered, 'out/' + out + '/unknown.csv')
mapToTxt(my_dict_black, 'out/' + out + '/black.csv')
mapToTxt(my_dict_white, 'out/' + out + '/white.csv')
