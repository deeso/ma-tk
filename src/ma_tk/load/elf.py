import os
import io
from elftools.elf.elffile import ELFFile
from .file import OpenFile, FileObj, FileLoader

class OpenELF(OpenFile):

    @classmethod
    def create_segment_lookup(cls, file_info):
        ef = file_info.get_file_interpreter()
        x = {i.header.p_offset: i for i in ef.iter_segments()}
        segments_by_offset = x
        setattr(file_info, 'segments_by_offset', segments_by_offset)

    @classmethod
    def from_zip(cls, zipname, filename=None, inmemory=False):
        if zipname is None or not os.path.exists(zipname):
            return None

        file_info = super().from_zip(zipname, filename, inmemory)
        if file_info is not None:
            file_info.set_file_interpreter(ELFFile(file_info.get_fd()), file_type='elf')
            cls.create_segment_lookup(file_info)
        return file_info

    @classmethod
    def from_file(cls, filename=None, inmemory=False):
        file_info = super().from_file(filename, inmemory)
        if file_info is not None:
            file_info.set_file_interpreter(ELFFile(file_info.get_fd()), file_type='elf')
            cls.create_segment_lookup(file_info)
        return file_info


    @classmethod
    def from_bytes(cls, data, filename=None):
        file_info = super().from_bytes(data, filename)
        if file_info is not None:
            file_info.set_file_interpreter(ELFFile(file_info.get_fd()), file_type='elf')
            cls.create_segment_lookup(file_info)
        return file_info

class ElfFileLoader(FileLoader):


    def load_location(self, location):
        '''
        load the file using the Elf loader class
        returns an IO file descriptor and pyelf file
        '''
        if location.find(b'bytes::') > -1:
            data = self.rfiles_bytes[location]
            file_info = OpenELF.from_bytes(data, fname)
            file_info.location = location
        elif location.find(b'zip::') > -1:
            name = location.strip('zip::')
            file_info = OpenELF.from_zip(self.rfiles_zip, name, inmemory)
            file_info.location = location
        elif location is not None:
            file_info = OpenELF.from_file(self.rfiles_zip, location, inmemory)
            file_info.location = location
        return file_info