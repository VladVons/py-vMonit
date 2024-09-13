# Created: 2024.09.13
# Author: Vladimir Vons <VladVons@gmail.com>
# License: GNU, see LICENSE for more details


from .Main import TUpdate

def Main(aConf) -> tuple:
    Obj = TUpdate(aConf)
    return (Obj, Obj.Run())
