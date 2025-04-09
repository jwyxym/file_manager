from os.path import join, exists, isdir, dirname
from os import listdir, mkdir
from shutil import copy
from tqdm import tqdm
from subprocess import run, DEVNULL
from time import sleep
from sys import argv

# 批注符号
# -path 进入目录
# -copy 复制目录下的文件（配合-copyto使用）
# -copyto 复制的目标目录
# -cmd 使用命令（在path下）
# -ccmd 使用命令（静默模式）
# -path.. 上一层目录（进入上一层目录）
# -copyto.. 上一层目录（进入上一层粘贴的目录）
# -final 最后执行的内容
# break 清空目标/来源，可以单独清空目标或来源

PATH = ''
COPYTO = ''
FINAL = ['', '']

def commands(key, line):
    def _copyto(l):
        global COPYTO
        COPYTO = join(COPYTO, l)
    def _copy(l):
        global PATH, COPYTO
        if COPYTO == '':
            return
        if not exists(COPYTO):
            mkdir(COPYTO)
        if '*' in l:
            l = l.split('*')
            for i in listdir(PATH):
                if not isdir(join(PATH, i)) and all(element in i for element in l):
                    copy(join(PATH, i), join(COPYTO, i))
        else:
            if exists(join(PATH, l)):
                copy(join(PATH, l), join(COPYTO, l))
    def _path(l):
        global PATH
        PATH = join(PATH, l)
    def _parent_path(_):
        global PATH
        PATH = dirname(PATH)
    def _parent_copy(_):
        global COPYTO
        COPYTO = dirname(COPYTO)
    def _ccmd(l):
        global PATH
        run(l.split(' '),
            stdout = DEVNULL,
            stderr = DEVNULL,
            shell = True,
            cwd = (None if PATH == '' else PATH)
        )
    def _cmd(l):
        global PATH
        run(l.split(' '),
            shell = True,
            cwd = (None if PATH == '' else PATH)
        )
    def _break(l):
        global PATH, COPYTO
        if l.endswith('copyto'):
            COPYTO = ''
        elif l.endswith('path'):
            PATH = ''
        else:
            PATH, COPYTO = '', ''
    def _final(l):
        global FINAL
        FINAL = l.split(maxsplit = 1)

    COMMAND_LIST = {
        '-copyto' : _copyto,
        '-copy' : _copy,
        '-path' : _path,
        '-ccmd' : _ccmd,
        '-cmd' : _cmd,
        '-final' : _final,
        '-path..' : _parent_path,
        '-copyto..' : _parent_copy,
        'break' : _break
    }
    if not key in COMMAND_LIST:
        return
    return COMMAND_LIST[key](line)


if __name__ == '__main__' and len(argv) >= 2:
    f = None
    with open (argv[1], 'r', encoding = 'utf-8') as file:
        f = file.readlines()

    with tqdm(total = len(f) - 1, unit_scale = True, desc = '启动中', position = 0, leave = True) as pbar:
        for i in range(len(f)):                
            line = f[i]
            pbar.update(1)
            line = line.rstrip('\n')
            line = line.split(maxsplit = 1)
            sleep(0.1)
            if len(line) == 0 or line[0].startswith('#'):
                continue
            commands(line[0], line[1] if len(line) > 1 else '')
    commands(FINAL[0], FINAL[1] if len(FINAL) > 1 else '')
