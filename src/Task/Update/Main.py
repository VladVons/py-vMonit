# Created: 2024.09.13
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


import asyncio
#
from Inc.Util.Obj import DeepGetByList
from IncP.Log import Log
from . ChkUpdateUrl import TChkUpdateUrl
from . ChkRun import TChkRun
from . ChkWatchFile import TChkWatchFile


ChkTable = {
    'update': TChkUpdateUrl,
    'run': TChkRun,
    'watch_file': TChkWatchFile
}


class TApp():
    def __init__(self, aConf):
        self.Conf = aConf
        self.FileVer = 'ver.json'

        Descr = DeepGetByList(aConf, ['common', 'descr'])
        if (Descr):
            Log.Print(1, 'i', f'Add app {Descr}')

        self.Checkers = self._Init()

    def _Init(self) -> dict:
        Res = {}
        for xKey, xVal in self.Conf['checker'].items():
            if (not xKey.startswith('-')) or (not xVal.get('enabled', True)):
                assert(xKey in ChkTable), f'Checker {xKey} not supported'
                Class = ChkTable[xKey](self)
                Res[xKey] = Class
        return Res

    async def CheckAll(self):
        for xClass in self.Checkers.values():
            await xClass.Check()

class TUpdate():
    def __init__(self, aConf):
        self.Conf = aConf
        self.Apps: list[TApp] = []

    async def Run(self, _aParam: dict = None):
        for xApp in self.Conf['app']:
            if (DeepGetByList(xApp, ['common', 'enabled'], True)):
                App = TApp(xApp)
                self.Apps.append(App)

        while True:
            for xApp in self.Apps:
                await xApp.CheckAll()
                await asyncio.sleep(1)
