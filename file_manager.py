from os.path import join, exists, isdir, isfile, dirname, relpath, basename
from os import listdir, mkdir, remove, walk
from shutil import copy, rmtree
from tqdm import tqdm
from subprocess import run, DEVNULL
from time import sleep
from aiohttp import ClientSession, TCPConnector
from asyncio import run as async_run
from sys import argv
from pathlib import Path
from sqlite3 import connect, OperationalError
from zipfile import ZipFile, ZIP_DEFLATED


# 批注符号
# -path 进入目录
# -copy 复制目录下的文件（配合-copyto使用）
# -del 删除目录下的指定文件
# -copydel 删除-copyto目录下的指定文件
# -deltree 删除目录下的指定目录
# -copydeltree 删除-copyto目录下的指定目录
# -copyto 复制的目标目录
# -sqlite 复制目录下的cdb（整合到-copyto目录下的cards.cdb中）
# -cmd 使用命令（在path下）
# -ccmd 使用命令（静默模式）
# -path.. 上一层目录（进入上一层目录）
# -copyto.. 上一层目录（进入上一层粘贴的目录）
# -download 在目录下下载
# -zip 压缩文件 第一个参数是压缩包的名称（不带后缀） 后续的参数是目录下的文件
# -final 最后执行的内容
# break 清空目标/来源，可以单独清空目标或来源

def chk_path(path):
    return str(Path.cwd()) == path

PATH = str(Path.cwd())
COPYTO = ''
FINAL = ['', '']
CDB = 'cards.cdb'

def commands(key, line):
    def _del(l):
        global PATH
        if exists(join(PATH, l)) and not isdir(join(PATH, l)):
            remove(join(PATH, l))
    def _copydel(l):
        global COPYTO
        if COPYTO == '':
            return
        if exists(join(COPYTO, l)) and not isdir(join(COPYTO, l)):
            remove(join(COPYTO, l))
    def _deltree(l):
        global PATH
        if exists(join(PATH, l)) and isdir(join(PATH, l)):
            rmtree(join(PATH, l))
    def _copydeltree(l):
        global COPYTO
        if COPYTO == '':
            return
        if exists(join(COPYTO, l)) and isdir(join(COPYTO, l)):
            rmtree(join(COPYTO, l))
    def _copyto(l):
        global COPYTO
        COPYTO = join(COPYTO, l)
        if not exists(COPYTO):
            mkdir(COPYTO)
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
    def _sqlite(l):
        if COPYTO == '':
            return
        if not exists(COPYTO):
            mkdir(COPYTO)

        def sqlite(_from, _to):
            rows = ()
            try:
                conn = connect(_from)
                cursor = conn.cursor()
                cursor.execute("select * from datas,texts where datas.id=texts.id")
                rows = cursor.fetchall()
            except OperationalError as e:
                pass
            finally:
                conn.close()

            if len(rows) > 0:
                if not exists(_to):
                    try:
                        conn = connect(_to)
                        cursor = conn.cursor()
                        cursor.execute("CREATE TABLE texts(id integer primary key,name text,desc text,str1 text,str2 text,str3 text,str4 text,str5 text,str6 text,str7 text,str8 text,str9 text,str10 text,str11 text,str12 text,str13 text,str14 text,str15 text,str16 text);")
                        cursor.execute("CREATE TABLE datas(id integer primary key,ot integer,alias integer,setcode integer,type integer,atk integer,def integer,level integer,race integer,attribute integer,category integer);")
                        conn.commit()
                    finally:
                        conn.close()

                for row in rows:
                    try:
                        conn = connect(_to)
                        cursor = conn.cursor()
                        cursor.execute(f"INSERT OR REPLACE INTO datas VALUES({row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]}, {row[8]}, {row[9]}, {row[10]});")
                        query = """
                            INSERT OR REPLACE INTO texts VALUES(
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?, ?, ?, ?, ?
                            )
                        """
                        values = (
                            row[11], row[12], row[13], row[14], row[15],
                            row[16], row[17], row[18], row[19], row[20],
                            row[21], row[22], row[23], row[24], row[25],
                            row[26], row[27], row[28], row[29]
                        )
                        cursor.execute(query, values)
                        conn.commit()
                    finally:
                        conn.close()

        if '*' in l:
            l = l.split('*')
            for i in listdir(PATH):
                if not isdir(join(PATH, i)) and all(element in i for element in l):
                    sqlite(join(PATH, i), join(COPYTO, CDB))
        else:
            if exists(join(PATH, l)):
                sqlite(join(PATH, l), join(COPYTO, CDB))

    def _path(l):
        global PATH
        PATH = join(PATH, l)
        if not exists(PATH):
            mkdir(PATH)
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
    def _download(l):
        DOWNLOADED = []
        async def download(url, path):
            if exists(path): return
            async with ClientSession(connector = TCPConnector(ssl = False)) as session:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            with open(path, 'wb') as f:
                                while True:
                                    chunk = await response.content.read(1024)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                except Exception as e:
                    try:
                        remove(path)
                    except Exception:
                        pass

        def to_name(name):
            illegal_chars = {'?', '\\', '|', '/', '*', ':', '<', '>', '"'}
            cleaned_name = ''.join(char for char in name if char not in illegal_chars)
            return cleaned_name
        
        try:
            endswith = None
            startchk = []
            incluchk = []
            paras = l.split(' ')
            for p in paras:
                if p.startswith('startchk='):
                    startchk.extend(p[len('startchk=') : ].split('|'))
                elif p.startswith('incluchk='):
                    incluchk.extend(p[len('incluchk=') : ].split('|'))
                elif p.startswith('endswith='):
                    endswith = p[len('incluchk=') : ]
            if (any(paras[0].startswith(x) for x in ['C:', 'D:', 'E:', './', '/']) and paras[0].endswith('.txt')) or exists(join(PATH, paras[0])):
                with open (join(PATH, paras[0]), 'r', encoding = 'utf-8') as f:
                    for i in f.readlines():
                        if (len(startchk) > 0 and not any(i.startswith(x) for x in startchk)) or (len(incluchk) > 0 and not any(x in i for x in incluchk)) or i.startswith('#'):
                            continue
                        i = i.rstrip('\n')
                        name = to_name(i.rsplit('/', 1)[-1])
                        if (endswith and not i.endswith(endswith)):
                            name += f'.{endswith}'
                        async_run(download(i, join(PATH, name)))
                        DOWNLOADED.append(name)
            elif paras[0].startswith('http'):
                paras[0] = paras[0].rstrip('\n')
                name = to_name(paras[0].rsplit('/', 1)[-1])
                if (endswith and not i.endswith(endswith)):
                    name += f'.{endswith}'
                path = join(PATH, name)
                async_run(download(paras[0], path))
                DOWNLOADED.append(name)
        finally:
            if 'del=true' in l and not chk_path(PATH):
                for root, dirs, files in walk(PATH, topdown = True, onerror = None, followlinks = False):
                    for file in files:
                        if not file in DOWNLOADED and not file in l:
                            remove(join(root, file))
    def _zip(l):
        global PATH, COPYTO
        line = l.split(' ')
        name = f'{line[0]}{'' if '.' in line[0] else '.zip'}'
        if len(line) <= 1:
            return
        with ZipFile(join(COPYTO, name), 'w', ZIP_DEFLATED, compresslevel = 9) as zipf:
            for r, d, f in walk(join(PATH)):
                for path in f:
                    if len([x for x in line[1 : ] if x.replace('*', '') in path]) > 0:
                        arcname = basename(join(PATH, path))
                        zipf.write(join(PATH, path), arcname)
                for path in d:
                    if path in line[1 : ] :
                        for root, dirs, files in walk(join(PATH, path)):
                            for file in files:
                                file_path = join(root, file)
                                arcname = relpath(file_path, dirname(join(PATH, path)))
                                zipf.write(file_path, arcname)
                break
    COMMAND_LIST = {
        '-copyto' : _copyto,
        '-copy' : _copy,
        '-sqlite' : _sqlite,
        '-path' : _path,
        '-ccmd' : _ccmd,
        '-cmd' : _cmd,
        '-final' : _final,
        '-path..' : _parent_path,
        '-copyto..' : _parent_copy,
        '-copydel' : _copydel,
        '-del' : _del,
        '-copydeltree' : _copydeltree,
        '-deltree' : _deltree,
        '-download' : _download,
        '-zip' : _zip,
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
