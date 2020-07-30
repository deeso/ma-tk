from .store.io import IOBacked
from .store.bfr import BufferBacked
from . import util
from .store.base_manager import BaseManager

class Manager(BaseManager):

    def __init__(self, **kargs):
        super().__init__(**kargs) 
        
    def calc_page(self, vaddr):
        return self.page_mask & vaddr

    def does_map_exist(self, bm):
        if len(bm.get_page_cache() & self.page_cache) > 0:
            return True
        return False

    def add_iomap(self, filename, va_start, size, offset=0, phy_start=0, flags=0, page_size=4096):
        '''
        opens the file and seeks to the relevant offset.
        the offset is then used as the physical start of this data segment 
        '''
        # FIXME couple of ambiguities here
        # 1) Mapping File to a Virtual Addr space that is larger than the file
        # size
        # 2) Starting the physical address at an offset in the file can result
        # in a file size that is less than the VA space 
        # 3) if the position in file falls out of sync with the physical address
        # reading the space will happen incorrectly
        io_obj = open(filename, 'rb')
        io_obj.seek(offset)
        ibm = IOBacked(io_obj, va_start, size, 
                       phy_start=phy_start, page_size=page_size, 
                       filename=filename, flags=flags)
        
        if not self.add_map_to_kb(ibm):
            del ibm
            io_obj.close()
            return None
        return ibm

    def add_buffermap(self, bytes_obj, va_start, size=None, filename=None, offset=0, flags=0, page_size=4096):
        phy_start = offset
        size = size if size else len(bytes_obj)
        bbm = BufferBacked(bytes_obj, va_start, len(bytes_obj), phy_start=offset, 
                            page_size=page_size, filename=filename, flags=flags)
        
        if not self.add_map_to_kb(bbm):
            del bbm
            return None
        return bbm

    def add_null_buffermap(self, va_start, size, filename=None, offset=0, flags=0, page_size=4096):
        bytes_obj = b'\x00' * size
        phy_start = offset
        bbm = BufferBacked(bytes_obj, va_start, len(size), phy_start=offset, 
                            page_size=flags, filename=filename, flags=flags)
        
        if not self.add_map_to_kb(bbm):
            del bbm
            io_obj.close()
            return None
        return bbm



    

