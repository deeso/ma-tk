import zipfile
import os
import io

from ..store.io import IOBacked
from ..store.bfr import BufferBacked

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
    
    def seek(self, offset, whence=os.SEEK_CUR):
        self.get_fd().seek(offset, whence)
        return self.tell()

    def tell(self):
        return self.get_fd().tell()

    def read(self, offset, size):
        fd = self.get_fd()
        filename = self.get_filename()
        
        # ef = elf_info.get_file_interpreter()
        if fd is None:
            self.info("Invalid file descriptor for {}".format(filename))
            return None
        pos = fd.tell()
        fd.seek(offset, os.SEEK_SET)
        data = fd.read(size)
        fd.seek(pos, os.SEEK_SET)
        return data

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

    def set_file_opener(self, file_opener_klass):
        self.FILE_OPENER = file_opener_klass

    @classmethod
    def create_fileloader(cls, required_files_location_list: list=None,
                 required_files_location: dict=None,
                 required_files_bytes: dict=None,
                 required_files_dir: str=None,
                 required_files_zip: str=None,
                 namespace='global'):
        loader = cls.FILE_LOADERS.get(namespace, None)
        if loader is None:
            loader = FileLoader(
                 required_files_location_list=required_files_location_list,
                 required_files_location=required_files_location,
                 required_files_bytes=required_files_bytes,
                 required_files_dir=required_files_dir,
                 required_files_zip=required_files_zip,
                 namespace=namespace)
        else:
            loader.update(
                required_files_location_list=required_files_location_list,
                required_files_location=required_files_location,
                required_files_bytes=required_files_bytes,
                required_files_dir=required_files_dir,
                required_files_zip=required_files_zip)
        return loader

    def update(self, 
               required_files_location_list: list=None,
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
                 namespace='global'):
        '''
        create a file loader in the static FILE_LOADERS dict, if one already exists,
        nothing really happens 
        '''
        self.FILE_OPENER = OpenFile
        if namespace not in self.FILE_LOADERS:
            self.FILE_LOADERS[namespace] = self

        self.namespace = namespace
        self.loaded_filename_to_objs = {}
        self.required_files_to_location = {}
        self.rfiles_bytes = {}
        self.rfiles_location = {}
        self.loaded_rfiles = {}
        self.rfiles_zip_names = []

        self.rfiles_zip = None
        self.update(required_files_location_list=required_files_location_list,
                 required_files_location=required_files_location,
                 required_files_bytes=required_files_bytes,
                 required_files_dir=required_files_dir,
                 required_files_zip=required_files_zip)

    def load_file_from_zip(self, zipname, filename=None, inmemory=False, add_all=False):
        file_obj = self.FILE_OPENER.from_zip(zipname, filename, inmemory)
        if file_obj is not None:
            self.add_file_to_namespace(file_obj, add_all=add_all)
        return file_obj

    def is_file_loaded(self, filename, namespace=None, namespaces=None, search_all=False):
        if search_all:
            return self.is_file_loaded(filename, namespaces=list(self.FILE_LOADERS))
        if namespace is None and namespaces is None and\
          filename in self.loaded_rfiles:
            return self.namespace
        elif namespace is not None and \
            filename in self.FILE_LOADERS[namespace].loaded_rfiles:
            return namespace 
        elif namespaces is not None:
            for namespace in namespaces:
                 loader = self.FILE_LOADERS[namespace]
                 if loader.is_file_loaded(filename, namespace=namespace):
                    return namespace            
        return None

    @classmethod
    def global_load_file(self, filename, namespace=None, namespaces=None, add_all=False, inmemory=False):
        if namespace is None and namespaces is None:
            namespace = 'global'

        if namespace not in cls.FILE_LOADERS:
            fl = cls.create_fileloader(namespace=namespace)
        fl.load_file(filename, namespace=namespace, namespaces=namespaces, add_all=add_all,inmemory=False)

    def add_file_to_namespace(self, file_obj, namespace=None, namespaces=None, add_all=False):
        if add_all:
            namespaces = [k for k in self.FILE_LOADERS]
        if namespace is None:
            namespace = self.namespace
        if namespaces is None:
            namespaces = []

        if len(namespaces) == 0 or namespace not in namespaces:
            namespaces.append(namespace)

        filename = file_obj.get_filename()
        for namespace in namespaces:
            self.FILE_LOADERS[namespace].loaded_rfiles[filename] = file_obj



    def load_file(self, filename, namespace=None, 
                  namespaces=None, add_all=False, reload=False, inmemory=False):
        '''
        1) resolve the required file,
        2) load the file if found,
        3) map the sections by p_offset from the segment header
        None if any of this stuff fails.
        '''
        # FIXME when reloading the file, do we reload it for all namespaces or
        # only the namespace specified in the arguments
        if not reload:
            _namespace = self.is_file_loaded(filename, namespace, 
                                             namespaces, search_all=add_all)

        if _namespace is not None and not reload:
            return self.FILE_LOADERS[_namespace].loaded_rfiles[filename]

        if namespaces is None:
            namespaces = []

        if namespace is not None and not add_all:
            namespaces.append(namespace)
        elif add_all:
            namespaces = list(self.FILE_LOADERS.keys())
        
        if len(namespaces) == 0:
            namespaces.append(self.namespace)

        location = self.where_is_file(filename)
        if location is None:
            return None
        
        file_info = self.load_location(location, inmemory=inmemory)

        for namespace in namespaces:
            self.FILE_LOADERS[namespace].loaded_rfiles[filename] = file_info
        return file_info

    def get_required_file(self, filename):
        '''
        list of required files by the core file,
        based on the NT_FILES note
        '''
        if filename in self.loaded_filename_to_objs:
            return self.loaded_filename_to_objs[filename]
        result = self.load_file(filename)
        self.loaded_filename_to_objs[filename] = result
        return self.loaded_filename_to_objs[filename]

    def load_location(self, location, inmemory=False):
        '''
        load the file using the Elf loader class
        returns an IO file descriptor and pyelf file
        '''
        if location is None:
            return None
        elif isinstance(location, bytes):
            self.load_location_bytes(location, inmemory=inmemory)
        if location.find('bytes::') > -1:
            data = self.rfiles_bytes[location]
            file_info = self.FILE_OPENER.from_bytes(data, fname)
            file_info.location = location
        elif location.find('zip::') > -1:
            name = location.strip('zip::')
            file_info = self.FILE_OPENER.from_zip(self.rfiles_zip, name, inmemory)
            file_info.location = location
        elif location is not None:
            file_info = self.FILE_OPENER.from_file(location, inmemory)
            file_info.location = location
        return file_info

    def load_location_bytes(self, location, inmemory=False):
        '''
        load the file using the Elf loader class
        returns an IO file descriptor and pyelf file
        '''

        if location.find(b'bytes::') > -1:
            data = self.rfiles_bytes[location]
            file_info = self.FILE_OPENER.from_bytes(data, fname)
            file_info.location = location
        elif location.find(b'zip::') > -1:
            name = location.strip(b'zip::')
            file_info = self.FILE_OPENER.from_zip(self.rfiles_zip, name, inmemory)
            file_info.location = location
        elif location is not None:
            file_info = self.FILE_OPENER.from_file(self.rfiles_zip, location, inmemory)
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
        if location is None and len(os.path.split(filename)) > 1:
            just_fn = os.path.split(filename)[-1]
            if filename != just_fn:
                location = self.where_is_file(just_fn)

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

    def load_file_to_memory(self, filename, size, offset, 
                            va_start, page_size=4096, flags=0, 
                            inmemory=True):
        file_info = self.load_file(file_name, inmemory=inmemory)
        ibm = None
        if file_info is not None and inmemory:
            bytes_obj = file_info.read(offset, size)
            phy_start = 0
            size = size if size else len(bytes_obj)
            ibm = BufferBacked(bytes_obj, va_start, len(bytes_obj), 
                               phy_start=phy_start, page_size=page_size, 
                               filename=file_info.get_filename(), flags=flags)
        elif file_info is not None:
            # should create a new ma_tk.load.FileObj to alleviate unsafe reads/writes
            io_obj = file_info.clone()
            phy_start = offset
            ibm = IOBacked(io_obj, va_start, size, 
                       phy_start=phy_start, page_size=page_size, 
                       filename=file_info.get_filename(), flags=flags)
        return ibm
