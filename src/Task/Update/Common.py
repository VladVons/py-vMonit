# Created: 2024.09.20
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


import os
import io
import re
import subprocess
import tarfile
from zipfile import ZipFile
#
from Inc.Misc.FS import DirRemove
from Inc.Misc.Template import TDictRepl
from Inc.Var.Dict import DeepGetByList, DeepGet
from IncP.Log import Log


def HasComment(aData: list[str]) -> list[str]:
    return [x for x in aData if not x.startswith('-')]

def RemoveFiles(aDir: str, aFiles: list[str]):
    for xFile in aFiles:
        Path = f'{aDir}/{xFile}'
        if (os.path.exists(Path)):
            if os.path.isfile(Path):
                os.remove(Path)
            elif os.path.isdir(Path):
                DirRemove(Path)

def UnpackData(aData: str, aExt: str, aDirDst: str):
    Data = io.BytesIO(aData)
    if (aExt == 'gz'):
        with tarfile.open(fileobj=Data, mode='r:gz') as HTar:
            HTar.extractall(path=aDirDst)
    elif (aExt == 'zip'):
        with ZipFile(Data) as HZip:
            HZip.extractall(path=aDirDst)

def SysExec(aCmd: str):
    Cmd = re.split(r'\s+', aCmd)
    try:
        Res = subprocess.run(Cmd, capture_output=True, text=True, check=True)
        return Res
    except FileNotFoundError as E:
        Log.Print(1, 'i', f'Err. SysExec(). {E.strerror} {E.filename}')
    except subprocess.CalledProcessError as _E:
        Log.Print(1, 'i', f'Err. SysExec(). {aCmd}')


class TDictReplEx(TDictRepl):
    def _VarTpl(self):
        self.ReVar = re.compile(r'(\$[a-zA-Z.]+)')

    def _Get(self, aFind: str) -> str:
        aFind = aFind[1:]
        Res = DeepGet(self.UserData, aFind)
        assert(Res), f'Macros not found {aFind}'
        return Res


class TCheckBase():
    def __init__(self, aParent, aSect: str):
        self.Parent = aParent
        self.Sect = aSect
        self.Conf = aParent.Conf['checker'][aSect]
        self.Inited = False

        if (not 'sleep' in self.Conf):
            self.Conf['sleep'] = DeepGetByList(aParent.Conf, ['common', 'sleep'], 60)
        self.Timer = -self.Conf.get('delay', 2)

    async def _Init(self):
        pass

    async def _Check(self):
        raise NotImplementedError()

    async def Check(self):
        if (self.Timer == 0) or (self.Timer >= self.Conf['sleep']):
            if (not self.Inited):
                self.Inited = True
                await self._Init()

            self.Timer = 0
            await self._Check()
        self.Timer += 1
        pass
