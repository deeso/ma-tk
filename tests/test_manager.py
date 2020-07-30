import os
import unittest
from ma_tk.manager import Manager

import tempfile

BUFFER_VA = 0x14000
FILE_VA = 0x24000

class TestManager(unittest.TestCase):
    TMP_FILE = None
    TMP_FILE_NAME = None
    TMP_FILE_SZ = 0
    def setUp(self):
        # setup our tmp file
        self.TMP_FILE = tempfile.NamedTemporaryFile()
        self.TMP_FILE_NAME = self.TMP_FILE.name
        fd = self.TMP_FILE
        fd.seek(0)
        fd.write(b'\xab\xab\xcd\xcd'*4096)
        fd.seek(0, os.SEEK_END)
        self.TMP_FILE_SZ = fd.tell()
        fd.seek(0)

    def tearDown(self):
        # setup our tmp file
        self.TMP_FILE.close()


    def test_create(self):
        mgr = Manager()
        self.assertTrue(True)

    def test_load_buffer(self):
        mgr = Manager()
        self.assertTrue(True)

        data = b'\xab\xab\xcd\xcd'*4096
        mgr.add_buffermap(data, BUFFER_VA, len(data), offset=0, flags=7)
        self.assertTrue(mgr.get_vaddr_pos() == BUFFER_VA)

    def test_get_backend(self):
        mgr = Manager()
        self.assertTrue(True)

        data = b'\xab\xab\xcd\xcd'*4096
        mgr.add_buffermap(data, BUFFER_VA, len(data), offset=0, flags=7)
        self.assertTrue(mgr.get_vaddr_pos() == BUFFER_VA)
        bm = mgr.get_map(BUFFER_VA)
        self.assertTrue(bm is not None)
        self.assertTrue(bm.has(BUFFER_VA))
        self.assertTrue(bm.translate_vaddr_to_offset(BUFFER_VA) == 0)
        self.assertTrue(len(bm.get_page_cache()) > 2)
        self.assertTrue(BUFFER_VA in bm.get_page_cache())
        self.assertTrue(bm.calc_page(BUFFER_VA+4098) in bm.get_page_cache())
        self.assertTrue(bm.translate_vaddr_to_offset(BUFFER_VA+8) == 8)


    def test_load_buffer(self):
        mgr = Manager()
        self.assertTrue(True)

        data = b'\xab\xab\xcd\xcd'*4096
        mgr.add_buffermap(data, BUFFER_VA, len(data), offset=0, flags=7)
        self.assertTrue(mgr.get_vaddr_pos() == BUFFER_VA)
        data = mgr.read_word()
        self.assertTrue(43947 == data)
        mgr.seek(offset=-2)
        data = mgr.read(2)
        self.assertTrue(b'\xab\xab' == data)
        data = mgr.read(4)
        self.assertTrue(b'\xcd\xcd\xab\xab' == data)
        mgr.seek(offset=-4)
        data = mgr.read_dword()
        self.assertTrue(0xababcdcd == data)
        data = mgr.read_qword()
        self.assertTrue(0xababcdcdababcdcd == data)

    def test_load_file(self):
        mgr = Manager()
        self.assertTrue(True)

        mgr.add_iomap(self.TMP_FILE_NAME, FILE_VA, self.TMP_FILE_SZ, offset=0, flags=0, page_size=4096)
        self.assertTrue(mgr.get_vaddr_pos() == FILE_VA)
        data = mgr.read_word()
        print(mgr.get_vaddr_pos(), hex(data))
        self.assertTrue(43947 == data)
        mgr.seek(offset=-2)
        data = mgr.read(2)
        self.assertTrue(b'\xab\xab' == data)
        data = mgr.read(4)
        self.assertTrue(b'\xcd\xcd\xab\xab' == data)
        mgr.seek(offset=-4)
        data = mgr.read_dword()
        self.assertTrue(0xababcdcd == data)
        data = mgr.read_qword()
        self.assertTrue(0xababcdcdababcdcd == data)
        del mgr

if __name__ == '__main__':
    unittest.main()