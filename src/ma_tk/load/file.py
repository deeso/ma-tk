import zipfile
import os
import io

class _Buffer(io.BytesIO):
    pass

class _File(io.FileIO):
    pass

class FileObj(object):

    def __init__(self, filename, file_descriptor, source="unknown",
                 file_interp=None, location=None, file_type="unknown",
                 inmemory=False, file_interp_klass=None, opener_name=None):
        self.filename = filename
        self.file_type = file_type
        self.file_interp = file_interp
        self.source = source
        self.fd = file_descriptor
        self.location = location
        self.segments_by_offset = None
        self.inmemory = inmemory
        self.file_interp_klass = file_interp_klass
        self.opener_name = opener_name

    def set_interp_klass(self, file_interp_klass):
        self.file_interp_klass = file_interp_klass

    def get_interp_klass(self):
        return self.file_interp_klass

    def get_filename(self):
        return self.filename

    def get_file_descriptor(self):
        return self.fd

    def get_fd(self):
        return self.get_file_descriptor()

    def get_source(self):
        return self.source

    def get_location(self):
        return location 

    def get_file_type(self):
        return self.file_type

    def get_attr(self, name, default_value=None):
        return getattr(self, name, default_value)

    def has_attr(self, name):
        return hasattr(self, name)
        
    def get_file_interpreter(self):
        return self.file_interp

    def set_file_interpreter(self, file_interp, file_type='unknown'):
        self.file_interp = file_interp
        self.file_type = file_type

    def update_file_segments(self, segments_by_offset):
        self.segments_by_offset = segments_by_offset

    def read_preserve_location(self, pos=0, size=None):
        old_pos = self.fd.tell()
        self.fd.seek(pos, os.SEEK_SET)
        data = None

        if size is None:
            data = self.fd.read()
        else:
            data = self.fd.read(size)
        self.fd.seek(old_pos, os.SEEK_SET)
        return data

    def clone(self, create_new_file_interp=False):
        if create_new_file_interp:
            raise Exception("This is not implemented")

        file_info = None
        if self.source is None:
            raise Exception("Attempting to clone from an unknown source")

        if self.source.find("bytes://") > -1:
            file_info = OpenFile.from_bytes(self.read_preserve_location())

        elif self.source.find('zip://') > -1:
            zip_filename, filename = self.source.split('::')

            file_info = OpenFile.from_zip(zip_filename.strip('zip://'), 
                                filename, 
                                self.inmemory)
        else:
            file_info = OpenFile.from_file(self.source.strip('file://'), self.inmemory)

        # FIXME do I really want to copy the file_interp
        # because it might be tied to an uncontrolled resource
        if file_info is not None:
            for k,v in self.__dict__.items():
                if k in ['fd',]:
                    continue
        return file_info


class OpenFile(object):
    @classmethod
    def from_zip(cls, zipname, filename=None, inmemory=False):
        if zipname is None or not os.path.exists(zipname):
            return None, None

        zf = zipfile.ZipFile(zipname)
        names = zf.namelist()
        if len(names) == 0:
            return None
        if filename is None:
            filename = names[0]
        if filename not in names:
            return None
        fd = zf.open(filename)
        if inmemory:
            new_filename = 'zip://{}::{}'.format(zipname, filename)
            result = cls.from_bytes(fd.read(), filename=new_filename)
            fd.close()
            zf.close()
            return result
        setattr(fd, 'name', filename)
        setattr(fd, 'source', 'zip://{}::{}'.format(zipname, filename))
        return FileObj(filename, fd, source=fd.source, inmemory=inmemory)

    @classmethod
    def from_file(cls, filename=None, inmemory=False):
        if filename is None or not os.path.exists(filename):
            return None
        fd = _File(filename, 'rb')
        if inmemory:
            result = cls.from_bytes(fd.read(), filename=filename)
            fd.close()
            return result
        setattr(fd, 'name', filename)
        setattr(fd, 'source', 'file://{}'.format(filename))

        return FileObj(filename, fd, source=fd.source, inmemory=inmemory)

    @classmethod
    def from_bytes(cls, data, filename=None):
        filename = 'data' if filename is None else filename
        if not isinstance(data, bytes):
            return None
        fd = _Buffer(data)
        if fd is not None:
            setattr(fd, 'name', filename)
            setattr(fd, 'source', 'bytes::')
        return FileObj(filename, fd, source=fd.source, inmemory=True)

class FileLoader(object):
    FILE_LOADERS = {}

    @classmethod
    def is_zip(cls, filename):
        if not os.path.exists(filename):
            return None

        try:
            zipfile.ZipFile(filename).namelist()
            return True
        except:
            return False

    @classmethod
    def zip_names(cls, filename):
        if is_zip(filename):
            return zipfile.ZipFile(zipname).namelist()
        return None

    @classmethod
    def create_fileloader(cls, required_files_location_list: list=None,
                 required_files_location: dict=None,
                 required_files_bytes: dict=None,
                 required_files_dir: str=None,
                 required_files_zip: str=None,
                 name='global'):
        loader = cls.FILE_LOADERS(name, None)
        if loader is None:
            loader = FileLoader(
                 required_files_location_list=required_files_location_list,
                 required_files_location=required_files_location,
                 required_files_bytes=required_files_bytes,
                 required_files_dir=required_files_dir,
                 required_files_zip=required_files_zip,
                 name=name)
        else:
            loader.update(required_files_location_list=required_files_location_list,
                 required_files_location=required_files_location,
                 required_files_bytes=required_files_bytes,
                 required_files_dir=required_files_dir,
                 required_files_zip=required_files_zip)
        return loader

    def update(required_files_location_list: list=None,
               required_files_location: dict=None,
               required_files_bytes: dict=None,
               required_files_dir: str=None,
               required_files_zip: str=None):

        rfiles_location = {} if required_files_location is None \
                                  else required_files_location.copy()

        if required_files_location_list is not None:
            for f in required_files_location_list:
                if f not in self.rfiles_location:
                    self.rfiles_location[f] = f

        rfiles_bytes = {} if required_files_bytes is None \
                               else required_files_bytes
        # tell the memory loader that we have the file
        # but its already in memory
        self.rfiles_location.update(rfiles_bytes)
        self.rfiles_location.update({k: None for k in rfiles_bytes})
        
        if required_files_zip is not None and self.is_zip(required_files_zip):
            self.rfiles_zip = required_files_zip
            self.rfiles_zip_names = self.zip_names()

        if required_files_dir is not None:
            # FIXME non-path recursion here :(
            files = [os.path.join(required_files_dir, i) for i in os.listdir('.')]
            self.rfiles_location.update({k:k for k in files})


    def __init__(self,
                 required_files_location_list: list=None,
                 required_files_location: dict=None,
                 required_files_bytes: dict=None,
                 required_files_dir: str=None,
                 required_files_zip: str=None,
                 name='global'):
        '''
        create a file loader in the static FILE_LOADERS dict, if one already exists,
        nothing really happens 
        '''
        if name not in self.FILE_LOADERS:
            self.FILE_LOADERS[name] = self

        self.required_files_to_elf = {}
        self.required_files_to_location = {}
        self.rfiles_bytes = {}
        self.rfiles_location = {}
        self.loaded_rfiles = {}

        self.rfiles_zip = None
        self.update(required_files_location_list=required_files_location_list,
                 required_files_location=required_files_location,
                 required_files_bytes=required_files_bytes,
                 required_files_dir=required_files_dir,
                 required_files_zip=required_files_zip)


    def load_file(self, filename):
        '''
        1) resolve the required file,
        2) load the file if found,
        3) map the sections by p_offset from the segment header
        None if any of this stuff fails.
        '''
        if filename in self.loaded_rfiles:
            return self.loaded_rfiles[filename]

        location = self.where_is_file(filename)
        if location is None:
            return None
        
        file_info = self.load_location(location)
        if file_info is None:
            self.required_files_to_elf[filename] = None
            return None

        return file_info

    def get_required_file(self, filename):
        '''
        list of required files by the core file,
        based on the NT_FILES note
        '''
        if filename in self.required_files_to_elf:
            return self.required_files_to_elf[filename]
        result = self.load_file(filename)
        self.required_files_to_elf[filename] = result
        return self.required_files_to_elf[filename]

    def load_location(self, location):
        '''
        load the file using the Elf loader class
        returns an IO file descriptor and pyelf file
        '''
        if location.find(b'bytes::') > -1:
            data = self.rfiles_bytes[location]
            file_info = OpenFile.from_bytes(data, fname)
            file_info.location = location
        elif location.find(b'zip::') > -1:
            name = location.strip('zip::')
            file_info = OpenFile.from_zip(self.rfiles_zip, name, inmemory)
            file_info.location = location
        elif location is not None:
            file_info = OpenFile.from_file(self.rfiles_zip, location, inmemory)
            file_info.location = location
        return file_info

    def where_is_file(self, filename):
        '''
        The ELF file we want to load can be in several places:
            1a) provided directory (a directory)
            1b) list of files passed in during initialization
            2) in memory as a byte array ('bytes::')
            3) in a zip file ('zip::')
            4) on the local system

            at initialization, this dictionary maps known
            elfs for resolution in all cases except local system
        '''
        location = None
        if filename in self.required_files_to_location:
            return self.required_files_to_location[filename]

        # tell where the file is.
        # checks in memory bytes, mapping of filename to a location.
        if filename in self.rfiles_location:
            location = self.rfiles_location.get(filename)
            location = b'bytes::' if location is None else location

        # try just the filename if its in a path
        if location is None and os.path.split(filename) > 0:
            just_fn = os.path.split(filename)
            location = self.where_is_file(filename)

        # check the zip names list
        if location is None and self.rfiles_zip_names is not None:
            for n in self.rfiles_zip_names:
                if n.find(filename) > -1:
                    location = b'zip::' + n
                    break

        # check local file system
        if location is None:
            if os.path.exists(filename):
                location = filename
        self.required_files_to_location[filename] = location
        return location