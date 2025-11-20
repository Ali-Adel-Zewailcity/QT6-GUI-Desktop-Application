'''
Classes
-------

    - File:
        Handle Files most common operations.

    - Directory
        Handle Folders most common operations
'''
import os
import time
import re

# Global Variables
win_filename_convention = r'[:*?\\/<>|"]'

class File:
    """
    File
    ==========
    
    Handle Files most common operations.

    Attributes
    ----------
        path (str): Path of the File
        name (str): Name of the file without it's extension
        ext (str): File Extension (Format type)

    Methods
    -------
        isfile() -> bool:
            returns True if the path belongs to an existing file,
            else (Folder or non-existant File) it returns False

        exist() -> bool:
            returns True if file exists in the system else returns False

        size() -> int:
            returns the size of the file in bytes

        isvalid(valid_types: list | tuple | set) -> bool:
            Check if the File format is supported by passing an iterable contains the supported types
        
        dir() -> str:
            Returns File Directory
        
        validate_name() -> None:
            Modifying the instance's file name for the following reasons:
                - if there is another file within the same folder that has the same name
                - the file name doesn't met the system naming convention
        
        remove() -> bool:
            Remove the File from the main system if existed
            
            **only delete Files**
            
            **Note** file will be permanently deleted and can't be restored
            
            **Restriction:** The file will only be deleted if it is located within the application's 
            current working directory or one of its subdirectories.

        __abs__() -> str:
            Get the Absolute Path of the File from the Main System Directory
            Windows Home Directory (C:/.....)
            MacOS Home Directory (home/.....)
        
        __str__() -> str:
            Returns File Path
    """
    
    def __init__(self, path: str):
        self.path = path
        self.name, self.ext = os.path.splitext(os.path.basename(path))
    
    def __abs__(self) -> str:
        '''
        Get the Absolute Path of the File from the Main System Directory
        (Partition Drive in windows)
        '''
        return os.path.abspath(self.path)
    
    def __str__(self) -> str:
        '''Returns File Path'''
        return str(self.path)
    
    def exist(self) -> bool:
        '''Check if File exists in the system'''
        return os.path.exists(self.path)
    
    def isfile(self) -> bool:
        '''Check if the path belongs to a File'''
        return os.path.isfile(self.path)

    def size(self) -> int:
        '''Get the size of the File'''
        return os.path.getsize(self.path)

    def isvalid(self, valid_types: list | tuple | set) -> bool:
        '''
        Check if the File format is supported by passing an iterable contains the supported types
        
        Parameters
        ----------
        valid_types : list | tuple | set, obligated
            an iterable that contains the supported file formats with `.` prefix
        '''
        assert isinstance(valid_types, (list, tuple, set)), "valid_types must be a list, tuple, or set"
        return self.ext in valid_types
    
    def dir(self) -> str:
        '''Returns File Directory'''
        return os.path.dirname(self.path)

    def validate_name(self) -> None:
        '''
        Modifying the instance's file name for the following reasons:
            - if there is another file within the same folder that has the same name
            - the file name doesn't met the system naming convention
        '''
        basedir = Directory(os.path.dirname(self.__abs__()))
        files_indir = basedir.list_dir()
        file_name = self.name + self.ext
        global win_filename_convention
        file_name = re.sub(win_filename_convention, '', file_name)
        c = 1
        while file_name in files_indir:
            file_name = self.name + f'({c})' + self.ext
            file_name = re.sub(win_filename_convention, '', file_name)
            c += 1
        self.path = os.path.join(basedir.path, file_name)
        self.name, self.ext = os.path.splitext(file_name)
        return None
    
    def remove(self) -> dict:
        '''
        Remove the File from the main system if existed
        
        **only delete Files**
        
        **Note** file will be permanently deleted and can't be restored
        
        **Restriction:** The file will only be deleted if it is located within the application's 
        current working directory or one of its subdirectories.
        '''
        now = time.ctime()
        if self.isfile():
            # The next three Lines is to apply the restrictions
            current = os.getcwd()
            join = os.path.join(current, self.__abs__())
            if join.startswith(current):
                try:
                    now = time.ctime()
                    os.remove(self.path)
                    return {'File': self.path, 'Process': 'Remove', 'State': 1, 'Error': None, 'Datetime': now}
                except Exception as e:
                    return {'File': self.path, 'Process': 'Remove', 'State': 0, 'Error': e, 'Datetime': now}
            else:
                return {'File': self.path, 'Process': 'Remove', 'State': 0, 'Error': 'Restrictions', 'Datetime': now}
        else:
            return {'File': self.path,
                    'Process': 'Remove',
                    'State': 0,
                    'Error': 'Object is not a File or doesn\'t exist',
                    'Datetime': now}


class Directory:
    '''
    Directory
    =========
    
    Handle Folders most common operations
    
    Attributes
    ----------
        path (str): Path of the Directory
    
    Methods
    -------
        isdir() -> bool:
            returns True if the path belongs to an existing directory,
            else (File or non-existant Folder) it returns False

        exist() -> bool:
            returns True if Folder exists in the system else returns False
        
        make() -> bool:
            Creates a sanitized directory from the instance's path if it does not already exist.

            - Ensures the absolute intended path is within the current working directory (security check).
            - If the path already exists and is a directory, returns True.
            - If not, it:
                - Sanitizes the folder name by removing invalid Windows filename characters.
                - Constructs the sanitized path.

            Returns:
                bool: True if the directory exists or is created successfully; False if the
                target path is outside the current working directory (restriction violation).
        
        list_dir() -> list:
            Returns a list containing all the files and subfolders in the instance's path

        __abs__() -> str:
            Get the Absolute Path of the Directory from the Main System Directory
            Windows Home Directory (C:/.....)
            MacOS Home Directory (home/.....)

        __str__() -> str:
            Returns the Path of the Directory
        
        join(str) -> None:
            Modifies Directory object Attribute `path` to the new the joined path
    '''
    def __init__(self, path: str):
        self.path = path
        self.basename = os.path.basename(path)

    def __abs__(self) -> str:
        '''
        Get the Absolute Path of the Directory from the Main System Directory
            Windows Home Directory (C:/.....)
            MacOS Home Directory (home/.....)
        '''
        return os.path.abspath(self.path)
    
    def __str__(self) -> str:
        '''Returns the Path of the Directory'''
        return str(self.path)
    
    def get_full_path(self) -> str:
        """Returns the absolute path of the directory."""
        return os.path.abspath(self.path)

    def exist(self) -> bool:
        '''Check if the Directory exists in the system'''
        return os.path.exists(self.path)
    
    def isdir(self) -> bool:
        '''Check if path belongs to an existing Directory'''
        return os.path.isdir(self.path)

    def join(self, path: str) -> None:
        '''Modifies Directory object Attribute `path` to the new the joined path'''
        self.path = os.path.join(self.path, path)

    def make(self) -> bool:
        '''
        Creates a sanitized directory from the instance's path if it does not already exist.

        - Ensures the absolute intended path is within the current working directory (security check).
        - If the path already exists and is a directory, returns True.
        - If not, it:
            - Sanitizes the folder name by removing invalid Windows filename characters.
            - Constructs the sanitized path.

        Returns:
            bool: True if the directory exists or is created successfully; False if the
            target path is outside the current working directory (restriction violation).
        '''
        # The next three Lines is to apply the restrictions
        current = os.getcwd()
        join = os.path.join(current, self.__abs__())
        if join.startswith(current):
            dirname = os.path.dirname(self.path)
            basename = os.path.basename(self.path)
            global win_filename_convention
            basename = re.sub(win_filename_convention, '', basename)
            folder = os.path.join(dirname, basename)
            if os.path.isdir(folder):
                return True
            os.makedirs(folder)
            return True
        else:
            return False
    
    def list_dir(self) -> list:
        '''Returns a list containing all the files and subfolders in a specific folder'''
        return os.listdir(self.path)


    def allDirectory(self, remove: str, replace: str) -> dict:
        '''Replace a specific characters in all files in a folder.
        
        Parameters
        ----------
            remove (str)
                Characters to be removed
            replace (str)
                Characters used to replace removed characters
        '''
        try:
            assert self.isdir(), "Folder doesn't exist"    
            FILES = []
            for file in self.list_dir():
                filename, ext = File(file).name, File(file).ext
                if remove in filename:
                    new_filename = filename.replace(remove, replace)
                    if filename != new_filename:
                        os.rename(os.path.join(self.path, filename+ext), os.path.join(self.path, new_filename+ext))
                        FILES.append((filename+ext, new_filename+ext))
            return {"File": FILES, "State": 1, "Message":"Process done successfully", "Datetime":time.ctime()}
        except Exception as e:
            return {"File": self.path, "State": 0, "Error":f"An error occurred: {e}", "Datetime":time.ctime()}