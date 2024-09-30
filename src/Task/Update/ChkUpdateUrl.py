# Created: 2024.09.20
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


import os
import sys
import json
import asyncio
#
from Inc.Misc.aiohttpClient import UrlGetData
from Inc.Misc.FS import WriteFileTyped
from Inc.Var.Dict import DeepGetByList
from Inc.Var.Obj import Iif
from IncP.Log import Log
from .Common import HasComment, RemoveFiles, SysExec, UnpackData, TCheckBase


class TChkUpdateUrl(TCheckBase):
    def __init__(self, aParent):
        super().__init__(aParent, 'update')

        self.DirApp = DeepGetByList(aParent.Conf, ['checker', 'run', 'dir'])
        self.DirApp = os.path.expanduser(self.DirApp)
        self.FileVer = 'ver.json'

    def _PyPkg(self, aPyPkg: list[str]) -> bool:
        def Normalize(aVal: str) -> str:
            return aVal.replace('_', '-').lower().strip()

        Res = True
        Data = SysExec(f'{sys.executable} -m pip freeze')
        if (Data):
            Installed = [Normalize(xPkg.split('==')[0]) for xPkg in Data.stdout.splitlines()]
            for xPkg in aPyPkg:
                xPkg = Normalize(xPkg)
                if (xPkg not in Installed):
                    Data = SysExec(f'{sys.executable} -m pip install {xPkg}')
                    if (not Data):
                        Res = False
        else:
            Res = False

        return Res

    async def _Unpack(self, aConf: dict, aFiles: list[str]) -> bool:
        Res = True
        for xFile in aFiles:
            UrlFile = f'{aConf["url"]}/{xFile}'
            UrlData = await UrlGetData(UrlFile, aConf.get('login'), aConf.get('password'))
            if (UrlData['status'] == 200):
                Ext = xFile.rsplit('.', maxsplit=1)[-1].lower()
                try:
                    UnpackData(UrlData['data'], Ext, self.DirApp)
                except Exception as E:
                    Log.Print(1, 'x', 'Err. Unzip', aE=E)
                    Res = False
            else:
                Log.Print(1, 'i', f'Err. Download(). Url {UrlFile}, code {UrlData["status"]}')
                Res = False
        return Res

    async def _Check(self):
        async def _GetRomoteVer(aUrl) -> dict:
            Data = await UrlGetData(aUrl, self.Conf.get('login'), self.Conf.get('password'))
            if (Data['status'] != 200):
                Log.Print(1, 'i', f'Err. chk_update(). {self.DirApp}. Url {aUrl}, code {Data["status"]}')
                return

            try:
                return json.loads(Data['data'])
            except Exception as E:
                Log.Print(1, 'x', f'Err. chk_update(). {self.DirApp}. Json format', aE=E)

        def _GetLocalVer(aFile: str) -> str:
            Res = ''
            if (os.path.exists(aFile)):
                with open(aFile, 'r', encoding='utf8') as F:
                    try:
                        Data = json.load(F)
                        Res = DeepGetByList(Data, ['ver', 'release'], '').strip()
                    except Exception as E:
                        Log.Print(1, 'x', f'Err. chk_update(). {self.DirApp}. Json format', aE=E)
            else:
                Log.Print(1, 'i', f'Err. chk_update(). File not exists {aFile}')
            return Res

        if (not self.DirApp):
            Descr = DeepGetByList(self.Parent.Conf, ['common', 'descr'], '')
            Log.Print(1, 'i', f'Err. chk_update(). `run/dir` is undefined. {Descr}')
            return

        if (not os.path.isdir(self.DirApp)):
            if (self.Conf.get('create_dir', False)):
                os.makedirs(self.DirApp)
            else:
                Log.Print(1, 'i', f'Err. chk_update(). {self.DirApp}. Dir not exists')
                return

        Url = f'{self.Conf["url"]}/{self.FileVer}'
        RemoteVer = await _GetRomoteVer(Url)
        if (not RemoteVer):
            return
        RemoteVerNo = DeepGetByList(RemoteVer, ['ver', 'release'], '').strip()

        File = f'{self.DirApp}/{self.FileVer}'
        LocalVerNo = _GetLocalVer(File)
        if (RemoteVerNo == LocalVerNo):
            return

        Items = HasComment(RemoteVer.get('unpack', []))
        if (not await self._Unpack(self.Conf, Items)):
            return

        Items = HasComment(RemoteVer.get('py_pkg', []))
        if (not self._PyPkg(Items)):
            return

        Items = HasComment(RemoteVer.get('remove', []))
        RemoveFiles(self.DirApp, Items)

        Data = {'ver': RemoteVer['ver']}
        WriteFileTyped(File, Data)
        Log.Print(1, 'i', f'chk_update(). {self.DirApp}. Updated to {RemoteVerNo}')

        Action = Iif(RemoteVer.get('action'), RemoteVer.get('action'), self.Conf.get('action'))
        if (Action == 'stop'):
            Main = getattr(sys.modules['__main__'], '__file__')
            Path = os.path.dirname(Main)
            if (self.DirApp == Path):
                Log.Print(1, 'i', f'Exit {Main}')
                sys.exit()
            else:
                await self.Parent.Checkers['run'].Stop()
        elif (Action == 'reboot'):
            Delay = 5
            Log.Print(1, 'i', f'chk_update(). {self.DirApp}. Reboot system in {Delay} seconds')
            asyncio.sleep(Delay)
            await self.Parent.Checkers['run'].Stop()
            asyncio.sleep(Delay)
            os.system('reboot')
        else:
            Log.Print(1, 'i', f'chk_update(). {self.DirApp}. Unknown action {Action}')

