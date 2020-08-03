from .memory import MemoryObject
from threading import RLock
import os


class IOBacked(MemoryObject):

    def __init__(self, io_obj, va_start: int, size: int, 
                 phy_start: int = 0, page_size: int = 4096, 
                 filename: str = None, flags: int = 0):

        # NOTES file seeking
        # os.SEEK_CUR seek from current location
        # os.SEEK_SET seek from the beginning of file abs(pos)
        # os.SEEK_END seek from the end of the file

        # FIXME couple of ambiguities here
        # 1) Mapping File to a Virtual Addr space that is larger than the file
        # size
        # 2) Starting the physical address at an offset in the file can result
        # in a file size that is less than the VA space 
        # 3) if the position in file falls out of sync with the physical address
        # reading the space will happen incorrectly

        # note io_obj is a ma_tk.file.FileObj

        super().__init__(va_start, phy_start, size, page_size, flags) 
        self.va_end = va_start + size
        self.filename = filename if filename else 'anonymous'
        self.name = "{:016x}-{:016x}:file:{}".format(va_start, va_start + size, self.filename)   
        self.io_obj = io_obj
        self._abs_start = self.io_obj.get_fd().tell() 
        self.pos = self.io_obj.get_fd().tell()
        self.io_lock = RLock()
    
    def _read(self, size, pos=None):
        # TODO try except finally needed here
        data = b''
        # self.io_lock.acquire()
        pos = self.pos if pos is None else pos
        if pos != self.pos:
            self._seek(phy_addr=pos)
        try:
            data = self.io_obj.get_fd().read(size)
            self.pos = pos+len(data)
        except:
            raise
        # finally:
        #     self.io_lock.release()
        return data

    def _seek(self, addr=None, offset=None, phy_addr=None):
        r = False
        diff = None
        if offset is not None:
            if self._abs_start + offset < self._abs_start + self.size:
                self.io_obj.get_fd().seek(offset, os.SEEK_CUR)
                self.pos = self.io_obj.tell()
                r = True
        elif vaddr is not None and \
           self.va_start <= vaddr and \
           vaddr < self.va_start + self.size:
            diff = vaddr - self.va_start
            self.io_obj.get_fd().seek(diff)
            self.pos = self.io_obj.get_fd().tell()
            r = True
        elif phy_addr is not None and self.phy_start <= phy_addr and \
           phy_addr < self.phy_start + self.size:
            diff = phy_addr - self.phy_start
            self.io_obj.get_fd().seek(diff)
            self.pos = self.io_obj.get_fd().tell()
            r = True
        return r    