from cli.File import File
from PIL import Image
import time
from typing import Tuple

class ImageOperations(File):
    '''
    ImageOperations
    ===============
    
    Class Functionality is to convert between different images formats

    Attributes
    ----------
        path (str): Path of the Image File
        name (str): Name of the Image file without extension
        ext (str): Image Extension (Image Type)
        img (Image.Image): Image Object from PIL.Image Module
        mode (str): Image Mode (Supported: `RGB`, `RGBA`)
        _supported (list): contains supported image formats that can be handled by this class
        _mode (dict): Dictionary conatins each format as a key and it's mode as a value

    Methods
    -------
        open() -> None:
            Opens an instance of the Image in the Memory
        
        close() -> None:
            Deletes the Image instance from the Memory
        
        convert(str) -> dict
            Convert between different image formats
            Supported: `.jpg`, `.jpeg`, `.webp`, `.png`, `.ico`, `.bmp`
    '''

    _supported = ['.jpg', '.jpeg', '.webp', '.png', '.ico', '.bmp']

    _mode = {'.jpg': 'RGB', '.jpeg': 'RGB', '.webp': 'RGB', '.bmp': 'RGB', '.png': 'RGBA', '.ico': 'RGBA'}

    def __init__(self, path: str):
        super().__init__(path)
        self.img = None
        self.mode = None
    
    def open(self):
        '''Sets Self.img to a Image Object from PIL.Image Module'''
        self.img = Image.open(str(self))
        self.mode = self.img.mode

    def close(self):
        '''Closes Image Object from PIL.Image Module in memory'''
        self.img.close()


    def convert_image(self, convert_to: str) -> dict:
        '''Convert this ImageOperations Object Instance into the specified the Type
        and saves the Converted Image'''
        now = time.ctime()
        
        if not self.isfile():
            return {'File': self.path,
                    'Process': 'Image Convertion',
                    'State': 0,
                    'Error': "File doesn't exist",
                    'Datetime': now}
        if not self.isvalid(self._supported):
            return {'File': self.path,
                    'Process': 'Image Convertion',
                    'State': 0,
                    'Error': f"'{self.ext}' Files is not supported",
                    'Datetime': now}
        
        try:
            self.open()
            
            new_mode = self._mode[convert_to]

            save_loc = File(f'Media Files Manager/Image Convertion/{self.name}{convert_to}')
            save_loc.validate_name()
            
            if self.ext == '.png' and convert_to == '.ico':
                st, s, sl = png_to_ico(self.img, save_loc)
                er, ms= (None, s) if st else (s, None)
                return {'File': self.path,
                    'Process': 'Image Convertion',
                    'State': st,
                    'Message': ms,
                    'Save Location': sl,
                    'Error': er,
                    'Datetime': now}

            elif self.ext == '.ico' and convert_to != '.png':
                through_png = self.convert_image('.png')
                if through_png.get('State'):
                    png = ImageOperations(through_png.get('Save Location'))
                    result = png.convert_image(convert_to)
                    rm_res = png.remove()
                    result['Insiders'] = [through_png, result, rm_res]
                    return result
                else:
                    return through_png

            elif convert_to == '.ico':
                through_png = self.convert_image('.png')
                if through_png.get('State'):
                    png = ImageOperations(through_png.get('Save Location'))
                    result = png.convert_image(convert_to)
                    rm_res = png.remove()
                    result['Insiders'] = [through_png, result, rm_res]
                    return result
                else:
                    return through_png
            
            if (self.mode != new_mode) and (convert_to != '.png'):
                image = self.img.convert(new_mode)


            if locals().get('image'):
                image.save(str(save_loc))
                image.close()
                self.close()
            else:
                self.img.save(str(save_loc))
                self.close()
            
            return {'File': self.path,
                    'Process': 'Image Convertion',
                    'State': 1,
                    'Message': f"Image converted successfully at '{str(save_loc)}'",
                    'Save Location': abs(save_loc),
                    'Datetime': now}
        except Exception as e:
            return {'File': self.path,
                    'Process': 'Image Convertion',
                    'State': 0,
                    'Error': f"An unexcepected error occured: {e}",
                    'Datetime': now}


def square_image(image: Image.Image) -> Image.Image:
    '''Return a Squared Version from the Image
    
    *e.g.* image size (1920, 1080) --> new image size (1920, 1920)
    '''
    new_image = Image.new('RGBA', (max(image.size), max(image.size)), (0,0,0,0))
    new_image.paste(image, ((max(image.size) - image.width) // 2, (max(image.size) - image.height) // 2))
    return new_image


def png_to_ico(image: Image.Image, name: File) -> Tuple[bool, str, str | None]:
    '''
    Convert PNG to ICO Image
    
    Parameters
    ----------
        image (Image.Image): Image Object from PIL.Image Module
        name (File): File object specifying the path of the output ICO image and it's name
    '''
    try:
        width = image.width
        height = image.height
        size = image.size

        if width == height:
            size = (256,256) if width > 256 else size

            if (image.mode != 'RGBA'):
                image = image.convert('RGBA')

            image.save(str(name), format='ICO', sizes = [size])
        else:
            new_image = square_image(image)
            new_image = new_image.crop((new_image.getbbox()))
            new_image = square_image(new_image)
            size = (256,256) if new_image.width > 256 else new_image.size

            new_image.save(str(name), format='ICO', sizes=[size])
        return True, f"Image converted successfully at '{abs(name)}'", abs(name)
    except Exception as e:
        return False, f"An unexcepected error occured: {e}", None