# Created: 2024.09.20
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details

import os
import re
import asyncio
import subprocess
#
from IncP.Log import Log
from .Common import TCheckBase


class TChkRun(TCheckBase):
    def __init__(self, aParent):
        super().__init__(aParent, 'run')
        self.Process = None

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
        DirApp = self.Conf['dir']
        if (not os.path.isdir(DirApp)):
            Log.Print(1, 'e', f'Err. chk_run(). {DirApp}. Dir not exists')
            return

        if ('cmd' in self.Conf) and (not self.IsRun()):
            Cmd = re.split(r'\s+', self.Conf['cmd'])
            Cmd[0] = f'{DirApp}/{Cmd[0]}'
            try:
                self.Process = subprocess.Popen(
                    Cmd,
                    cwd=DirApp,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                Log.Print(1, 'i', f'chk_run(). Running {Cmd}. pid {self.Process.pid}')
            except Exception as E:
                self.Process = None
                Log.Print(1, 'x', str(E))
