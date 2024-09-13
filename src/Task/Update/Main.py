# Created: 2024.09.13
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


import io
import os
import re
import json
import asyncio
import subprocess
from zipfile import ZipFile
import aiohttp
#
from Inc.Util.Obj import DeepGetByList
from IncP.Log import Log


async def UrlGetData(aUrl: str, aLogin: str = None, aPassword: str = None):
    if (aLogin and aPassword):
        Auth = aiohttp.BasicAuth(login=aLogin, password=aPassword)

    async with aiohttp.ClientSession(auth=Auth) as session:
        async with session.get(aUrl) as Response:
            if (Response.status == 200):
                Data = await Response.read()
                Res = {'status': Response.status, 'data': Data}
            else:
                Res = {'status': Response.status}
    return Res


class TApp():
    def __init__(self, aConf):
        self.Conf = aConf
        self.Process = None
        self.Chekers = self.GetChekers()

    async def chk_update(self, aConf: dict):
        DirApp = DeepGetByList(self.Conf, ['run', 'dir'])
        File = f'{DirApp}/ver.json'
        if (not os.path.exists(File)):
            Log.Print(1, 'i', f'Err. Download(). File not found {File}')
            return

        with open(File, 'r', encoding='utf8') as F:
            try:
                Data = json.load(F)
                CurVer = DeepGetByList(Data, ['ver', 'release'], '').strip()
            except Exception as E:
                Log.Print(1, 'x', 'Err. Download()', aE=E)

        UrlData = await UrlGetData(aConf['url'], aConf.get('login'), aConf.get('password'))
        if (UrlData['status'] != 200):
            Log.Print(1, 'i', f'Err. Download(). Url {aConf["url"]}, code {UrlData["status"]}')
            return

        try:
            Info = json.loads(UrlData['data'])
        except Exception as E:
            Log.Print(1, 'x', 'Err. Download()', aE=E)

        LastVer = DeepGetByList(Info, ['ver', 'release'], '').strip()
        if (LastVer == CurVer):
            return

        UrlRoot = aConf['url'].rsplit('/', maxsplit=1)[0]
        for xUnpack in Info.get('unpack', []):
            UrlFile = f'{UrlRoot}/{xUnpack[0]}'
            UrlData = await UrlGetData(UrlFile, aConf.get('login'), aConf.get('password'))
            if (UrlData['status'] == 200):
                with ZipFile(io.BytesIO(UrlData['data'])) as HZip:
                    Path = DirApp
                    if (len(xUnpack) == 2):
                        DirApp += xUnpack[1]
                    HZip.extractall(path=Path)
            else:
                Log.Print(1, 'i', f'Err. Download(). Url {UrlFile}, code {UrlData["status"]}')
                return

        with open(File, 'w', encoding='utf8') as F:
            Data = {'ver': Info['ver']}
            json.dump(Data, F)

        if (aConf.get('stop_app')):
            await self.Stop()

    async def chk_run(self, aConf: dict):
        Dir = aConf['dir']
        if (not os.path.isdir(Dir)):
            Log.Print(1, 'e', f'Err. Dir not exists {Dir}')
            return

        if (not self.Process) or (self.Process and self.Process.poll()):
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
                Log.Print(1, 'i', f'Running {Cmd}')
            except Exception as E:
                self.Process = None
                Log.Print(1, 'x', str(E))

    def GetChekers(self) -> dict:
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
                        'timer': 0,
                        'method': getattr(self, xMethod),
                        'conf': Conf
                    }
        return Res

    async def Stop(self):
        if (self.Process):
            self.Process.terminate()
            self.Process.wait()
            await asyncio.sleep(3)
            self.Process = None

    async def Check(self):
        for xKey, xVal in self.Chekers.items():
            xVal['timer'] += 1
            if (xVal['timer'] >= xVal['conf']['sleep']):
                xVal['timer'] = 0
                await xVal['method'](xVal['conf'])


class TUpdate():
    def __init__(self, aConf):
        self.Conf = aConf
        self.Apps: list[TApp] = []

    async def Run(self, _aParam: dict = None):
        for xApp in self.Conf['app']:
            App = TApp(xApp)
            self.Apps.append(App)

        while True:
            for xApp in self.Apps:
                await xApp.Check()
                await asyncio.sleep(1)
