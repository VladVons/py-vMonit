# Created: 2024.09.20
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


import re
#
from Inc.Util.Obj import DeepGet
from .Common import TCheckBase


class TChkWatchFile(TCheckBase):
    def __init__(self, aParent):
        super().__init__(aParent, 'watch_file')

    async def _Check(self):
        for xFile in self.Conf['files']:
            Match = re.search(r"\{% (.*?) %\}", xFile)
            if (Match):
                Val = DeepGet(self.Conf, Match.group(1))
