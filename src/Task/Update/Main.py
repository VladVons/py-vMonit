# Created: 2024.09.13
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


import io
import os
import sys
import re
import json
import asyncio
import subprocess
import tarfile
from zipfile import ZipFile
#
from Inc.Misc.aiohttpClient import UrlGetData
from Inc.Util.Obj import DeepGetByList
from IncP.Log import Log


class TApp():
    def __init__(self, aConf):
        self.Conf = aConf
        self.Process = None
        self.Chekers = self._GetChekers()

    @staticmethod
    def SysExec(aCmd: str):
        Cmd = re.split(r'\s+', aCmd)
        try:
            Res = subprocess.run(Cmd, capture_output=True, text=True, check=True)
            return Res
        except FileNotFoundError as E:
            Log.Print(1, 'i', f'Err. SysExec(). {E.strerror} {E.filename}')
        except subprocess.CalledProcessError as _E:
            Log.Print(1, 'i', f'Err. SysExec(). {aCmd}')

    def _GetChekers(self) -> dict:
        Res = {}
        Prefix = 'chk_'
        for xMethod in dir(self):
            if (xMethod.startswith(Prefix)):
                Name = xMethod.replace(Prefix, '')
                Conf = self.Conf.get(Name)
                if (Conf):
                    if (not 'sleep' in Conf):
                        Conf['sleep'] = self.Conf.get('sleep', 60)

                    Res[Name] = {
                        'timer': -Conf.get('delay', 2),
                        'method': getattr(self, xMethod),
                        'conf': Conf
                    }
        return Res

    @staticmethod
    def _UnpackData(aData: str, aExt: str, aDirDst: str):
        Data = io.BytesIO(aData)
        if (aExt == 'gz'):
            with tarfile.open(fileobj=Data, mode='r:gz') as HTar:
                HTar.extractall(path=aDirDst)
        elif (aExt == 'zip'):
            with ZipFile(Data) as HZip:
                HZip.extractall(path=aDirDst)

    async def _Unpack(self, aConf: dict, aFiles: list[str]) -> bool:
        Res = True

        UrlRoot = aConf['url'].rsplit('/', maxsplit=1)[0]
        for xUnpack in aFiles:
            UrlFile = f'{UrlRoot}/{xUnpack[0]}'
            UrlData = await UrlGetData(UrlFile, aConf.get('login'), aConf.get('password'))
            if (UrlData['status'] == 200):
                DirApp = DeepGetByList(self.Conf, ['run', 'dir'])
                if (len(xUnpack) == 2):
                    DirApp += xUnpack[1]
                Ext = xUnpack[0].rsplit('.', maxsplit=1)[-1].lower()

                try:
                    self._UnpackData(UrlData['data'], Ext, DirApp)
                except Exception as E:
                    Log.Print(1, 'x', 'Err. Unzip', aE=E)
                    Res = False
            else:
                Log.Print(1, 'i', f'Err. Download(). Url {UrlFile}, code {UrlData["status"]}')
                Res = False
        return Res

    def _PyPkg(self, aPyPkg: list[str]) -> bool:
        def Normalize(aVal: str) -> str:
            return aVal.replace('_', '-').lower().strip()

        Res = True
        Data = self.SysExec(f'{sys.executable} -m pip freeze')
        if (Data):
            Installed = [Normalize(xPkg.split('==')[0]) for xPkg in Data.stdout.splitlines()]
            for xPkg in aPyPkg:
                xPkg = Normalize(xPkg)
                if (xPkg not in Installed):
                    Data = self.SysExec(f'{sys.executable} -m pip install {xPkg}')
                    if (not Data):
                        Res = False
        else:
            Res = False

        return Res

    async def chk_update(self, aConf: dict):
        DirApp = DeepGetByList(self.Conf, ['run', 'dir'])
        if (not DirApp):
            Descr = DeepGetByList(self.Conf, ['info', 'descr'], '')
            Log.Print(1, 'i', f'Err. `run/dir` is undefined. {Descr}')
            return

        File = f'{DirApp}/ver.json'
        if (os.path.exists(File)):
            #Log.Print(1, 'i', f'Err. Download(). File not found {File}')

            with open(File, 'r', encoding='utf8') as F:
                try:
                    Data = json.load(F)
                    CurVer = DeepGetByList(Data, ['ver', 'release'], '').strip()
                except Exception as E:
                    Log.Print(1, 'x', 'Err. Download()', aE=E)
        else:
            CurVer = '0.0.0'

        UrlData = await UrlGetData(aConf['url'], aConf.get('login'), aConf.get('password'))
        if (UrlData['status'] != 200):
            Log.Print(1, 'i', f'Err. Download(). Url {aConf["url"]}, code {UrlData["status"]}')
            return

        try:
            Info = json.loads(UrlData['data'])
        except Exception as E:
            Log.Print(1, 'x', 'Err. Download(). Json format', aE=E)
            return

        LastVer = DeepGetByList(Info, ['ver', 'release'], '').strip()
        if (LastVer <= CurVer):
            return

        if (not await self._Unpack(aConf, Info.get('unpack', []))):
            return

        if (not self._PyPkg(Info.get('py_pkg', []))):
            return

        with open(File, 'w', encoding='utf8') as F:
            Data = {'ver': Info['ver']}
            json.dump(Data, F)
        Log.Print(1, 'i', f'chk_update(). Updated to {LastVer}')

        Action = aConf.get('action', '').lower()
        if (Action == 'stop'):
            Main = getattr(sys.modules['__main__'], '__file__')
            Path = os.path.dirname(Main)
            if (DirApp == Path):
                sys.exit()
            else:
                await self.Stop()

    async def chk_run(self, aConf: dict):
        Dir = aConf['dir']
        if (not os.path.isdir(Dir)):
            Log.Print(1, 'e', f'Err. Dir not exists {Dir}')
            return

        if ('cmd' in aConf) and (not self.IsRun()):
            Cmd = re.split(r'\s+', aConf['cmd'])
            Cmd[0] = f'{Dir}/{Cmd[0]}'
            try:
                self.Process = subprocess.Popen(
                    Cmd,
                    cwd=Dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                Log.Print(1, 'i', f'Running {Cmd}. pid {self.Process.pid}')
            except Exception as E:
                self.Process = None
                Log.Print(1, 'x', str(E))

    def IsRun(self):
        return (self.Process is not None) and (not self.Process.poll())

    async def Stop(self):
        if (self.Process):
            self.Process.terminate()
            self.Process.wait()

            Log.Print(1, 'i', f'Stop {self.Process.args}')
            self.Process = None
            await asyncio.sleep(3)

    async def Check(self):
        for _xKey, xVal in self.Chekers.items():
            if (xVal['timer'] == -1) or (xVal['timer'] >= xVal['conf']['sleep']):
                xVal['timer'] = 0
                await xVal['method'](xVal['conf'])
            xVal['timer'] += 1

class TUpdate():
    def __init__(self, aConf):
        self.Conf = aConf
        self.Apps: list[TApp] = []

    async def Run(self, _aParam: dict = None):
        for xApp in self.Conf['app']:
            if (DeepGetByList(xApp, ['info', 'enabled'], True)):
                Descr = DeepGetByList(xApp, ['info', 'descr'])
                if (Descr):
                    Log.Print(1, 'i', f'Add app {Descr}')
                App = TApp(xApp)
                self.Apps.append(App)

        while True:
            for xApp in self.Apps:
                await xApp.Check()
                await asyncio.sleep(1)
