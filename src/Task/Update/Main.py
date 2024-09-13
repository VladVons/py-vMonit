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
from Inc.Util.Obj import DeepGetByList, Iif
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

    async def Update(self):
        Conf = self.Conf.get('download')
        if (not Conf):
            return

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

        UrlData = await UrlGetData(Conf['url'], Conf.get('login'), Conf.get('password'))
        if (UrlData['status'] != 200):
            Log.Print(1, 'i', f'Err. Download(). Url {Conf["url"]}, code {UrlData["status"]}')
            return

        try:
            Info = json.loads(UrlData['data'])
        except Exception as E:
            Log.Print(1, 'x', 'Err. Download()', aE=E)

        LastVer = DeepGetByList(Info, ['ver', 'release'], '').strip()
        if (LastVer == CurVer):
            return

        UrlRoot = Conf['url'].rsplit('/', maxsplit=1)[0]
        for xUnpack in Info.get('unpack', []):
            UrlFile = f'{UrlRoot}/{xUnpack[0]}'
            UrlData = await UrlGetData(UrlFile, Conf.get('login'), Conf.get('password'))
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

        if (self.Process) and (Conf.get('stop_app')):
            self.Process.terminate()
            self.Process.wait()


    def Run(self):
        Conf = self.Conf.get('run')
        if (not Conf):
            return

        Dir = Conf['dir']
        if (not os.path.isdir(Dir)):
            Log.Print(1, 'e', f'Err. Dir not exists {Dir}')
            return

        Cmd = re.split(r'\s+', Conf['cmd'])
        Cmd[0] = f'{Dir}/{Cmd[0]}'
        try:
            self.Process = subprocess.Popen(
                Cmd,
                cwd=Dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as E:
            self.Process = None
            Log.Print(1, 'x', str(E))

    async def Check(self):
        await self.Update()
        self.Run()


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
                await asyncio.sleep(self.Conf.get('sleep', 60))
