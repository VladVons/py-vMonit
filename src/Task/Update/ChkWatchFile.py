# Created: 2024.09.20
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details

import os
#
from IncP.Log import Log
from .Common import TCheckBase, TDictReplEx, HasComment


class TChkWatchFile(TCheckBase):
    def __init__(self, aParent):
        super().__init__(aParent, 'watch_file')
        self.Files = {}

    async def _Init(self):
        DictRepl = TDictReplEx()
        DictRepl.UserData = self.Parent.Conf

        self.Files = {}
        for xFile in HasComment(self.Conf['files']):
            File = DictRepl.Parse(xFile)
            assert(os.path.exists(File)), f'File not exists {File}'
            self.Files[File] = 0

    async def _Check(self):
        for xFile, xLastTime in self.Files.items():
            CurTime = os.path.getmtime(xFile)
            Dif = CurTime - xLastTime
            if (Dif == 0):
                Action = self.Conf.get('action')
                if (Action == 'stop'):
                    Log.Print(1, 'i', f'Triger {self.Sect}. Action {Action}. File {xFile}')
                    await self.Parent.Checkers['run'].Stop()
            self.Files[xFile] = CurTime

