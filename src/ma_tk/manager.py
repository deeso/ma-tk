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

    def add_iomap(self, filename, va_start, size, offset=0, flags=0, page_size=4096):
        phy_start = offset
        ibm = IOBacked(io_obj, va_start, size, phy_start, 
                       page_size=page_size, filename=filename, flags=flags)
        
        if self.add_map_to_kb(ibm):
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

    def add_map_to_kb(self, bm):
        name = bm.get_name()
        pc = bm.get_page_cache()
        
        if self.check_presence(bm):
            return False

        self.vaddr_pos = bm.get_va_start()
        self.page_cache = self.page_cache | pc
        for p in pc:
            self.maps_by_page[p] = bm
        self.maps_by_name[name] = bm
        return True

    def remove_map_from_kb(self, bm):
        name = bm.get_name()
        pc = bm.get_page_cache()
        
        if not self.check_presence(bm):
            return True

        self.page_cache = {i for i in self.page_cache if i not in pc}        

        for p in pc:
            del self.maps_by_page[pc]

        del self.maps_by_name[name]
        return True


    

