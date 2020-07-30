from .. import util

class BaseManager(object):

    def __init__(self, **kargs):
        self.maps = []
        self.maps_by_name = {}
        self.maps_by_page = {}

        self.vaddr_pos = 0
        self.page_cache = set()
        self.page_size = kargs.get('page_size', 4096)
        self.page_mask = util.get_page_mask(self.page_size)

    def get_map(self, vaddr):
        if not self.check_presence(vaddr=vaddr):
            return None
        return self.maps_by_page[self.calc_page(vaddr)]

    def get_vaddr_pos(self):
        return self.vaddr_pos

    def check_presence(self, bm=None, name=None, vaddr=None):
        page = self.calc_page(vaddr) if vaddr else None
        if page and \
           (page in self.page_cache or page in self.maps_by_page):
           return True

        if name and \
           (name in self.maps_by_name):
           return True

        if bm is not None:
            name = bm.get_name()
            pc = bm.get_page_cache()

            return len(pc & self.page_cache) > 0 or \
                   name in self.maps_by_name
        return False

    def get_page(self, vaddr):
        return self.calc_page(vaddr)

    def get_page_cache(self):
        return self.page_cache
    
    def translate_vaddr_to_offset(self, vaddr):
        bm = self.get_map(vaddr)
        if bm is None:
            return None
        return bm, bm.translate_vaddr_to_offset(vaddr)

    def translate_vaddr_to_paddr(self, vaddr):
        bm = self.get_map(vaddr)
        if bm is None:
            return None

        return bm, bm.translate_vaddr_to_paddr(vaddr)

    def seek(self, addr=None, offset=None):
        bm = None
        r = False
        if addr is not None:
            bm = self.get_map(addr)
        elif offset is not None:
            bm = self.get_map(self.vaddr_pos+offset)
        if bm is not None:
            r = bm.seek(offset=offset)
            if r:
                self.vaddr_pos = bm.get_current_vaddr()
        return r

    def check_vaddr(self, vaddr):
        return self.check_presence(vaddr)

    def read(self, size, addr=None, offset=None):
        # FIXME data does not read across memory boundaries
        addr = self.vaddr_pos if addr is None and offset is None else addr
        if not addr is None:
            return self.read_at_vaddr(addr, size)
        elif offset is not None:
            vaddr = offset + self.vaddr_pos
            bm = self.get_map(offset + self.vaddr_pos)
            if bm is None:
                return None
            data = bm.read_at_vaddr(vaddr, size)
            self.vaddr_pos = bm.get_current_vaddr()
            return data
        return None


    def read_at_vaddr(self, vaddr: int, size: int = 1):
        # TODO does this read cross a boundary?
        # FIXME
        bm = self.get_map(vaddr)
        if bm is None:
            return None
        data = bm.read_at_vaddr(vaddr, size)
        self.vaddr_pos = bm.get_current_vaddr()
        return data

    def vaddr_in_range(self, vaddr):
        return self.check_presence(vaddr)

    def can_read(self, vaddr, len_):
        if not self.check_presence(vaddr) or not self.check_presence(offset+len_):
            return False 
        return True

    def get_vaddr(self):
        return self.vaddr_pos

    def name (self):
        return self.name


    ######################## Read word operations
    def read_word(self, addr=None, littleendian = True):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None        
        data = bm.read_word(addr=addr, littleendian=littleendian)
        self.vaddr_pos = bm.get_current_vaddr()
        return data


    ######################## Read dword operations
    def read_dword(self, addr=None, littleendian = True):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None        
        data = self.read_dword(addr=addr, littleendian=littleendian)
        self.vaddr_pos = bm.get_current_vaddr()
        return data

    ######################## Read qword operations
    def read_qword(self, addr=None, littleendian = True):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None        
        data = self.read_dword(addr=addr, littleendian=littleendian)
        self.vaddr_pos = bm.get_current_vaddr()
        return data

    ######################## Read ctype structure operations
    def read_cstruct(self, cstruct_klass, addr=None):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None
        data = self.read_cstruct(cstruct_klass, addr)
        self.vaddr_pos = bm.get_current_vaddr()
        return data


    def dump(self, filename=None, dump_path=None, block_size=512):
        # TODO dump all the files
        pass
        # if filename is None:
        #     filename = os.path.join(self.name, '.bin')

        # if dump_path is None:
        #     dump_path = 'memory-dump-' + str(uuid.uuid4())

        # if not os.path.exists(dump_path):
        #     os.makedirs(path, exist_ok=True)

        # f = open(os.path.join(dump_path, filename), 'wb')
        # offset = 0
        # while offset < self.size:
        #     data = self.read(size, offset)
        #     if data is None or len(data) == b'':
        #         break
        #     f.write(data)
        #     offset += len(data)
        # f.flush()
        # f.close()
        # return offset