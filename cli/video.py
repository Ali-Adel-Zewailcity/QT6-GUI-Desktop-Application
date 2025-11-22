import subprocess
from cli.File import File, Directory
from cli.images import ImageOperations
from cli.user_input_handler import calculate_sec
import time
from urllib.parse import urlparse
import requests
from typing import Callable

class Video(File):
    '''
    Video
    =====
    
    Class has the following functionalities:
        - Generate GIF images from Videos
        - Embed thumbnails into Video Files
    
    Attributes
    ----------
        path (str): Path of the Video File
        name (str): Name of the Video file without extension
        ext (str): Video Extension (Video Type)
        _supported (list): contains supported video formats that can be handled by this class


    Methods
    -------
        generate_gif (str, str, str) -> dict:
            Generate GIF Images from Videos
        embed_thumbnail_video (File | ImageOperations, File) -> dict:
            Embeds thumbnails in video files
        extract_original_audio -> dict
            Extracts the original audio stream from a video file
    '''
    _supported = [".mp4", ".mkv", ".avi", ".mov", ".flv",
    ".wmv", ".mpg", ".mpeg", ".3gp", ".ts", ".m4v", ".ogv"]
    
    def __init__(self, path):
        super().__init__(path)


    def generate_gif(self, start: str, end: str, scale: str | None = None) -> dict:
        '''
        Generate GIF Images from Videos
        
        Parameters
        ----------
            start : str
                string representation of time in the following formats `HH:MM:SS`, `MM:SS`, `SS`
            end : str
                string representation of time in the following formats `HH:MM:SS`, `MM:SS`, `SS`
            scale : str
                string digits specifying the generated gif width, height is scaled automatically to
                maintain the original aspect ratio of the video
        '''
        now = time.ctime()
        
        if not self.isfile():
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                    'State': 0, 'Error': "File doesn't Exist", 'Datetime': now}
        if not (self.ext.lower() in self._supported):
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                    'State': 0, 'Error': f"File of type {self.ext} is not supported", 'Datetime': now}

        gif = File(f"Media Files Manager/Extract GIFs/{self.name}.gif")
        gif.validate_name()

        try:
            end_sec = calculate_sec(start, end)

            if scale and scale.isdecimal():
                command = ['ffmpeg', '-ss',
                    start,
                    '-t', end_sec, '-i',
                    self.path,
                    '-vf',
                    f'fps=30,scale={scale}:-1:flags=lanczos',
                    str(gif)]
            else:
                command = ['ffmpeg', '-ss',
                    start,
                    '-t', end_sec, '-i',
                    self.path,
                    '-vf',
                    f'fps=30',
                    str(gif)]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)

            if result.returncode != 0:
                err = f"Error Extracting Gif from video: {result.stderr}"
                
                return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                    'State': 0, 'Error': err, 'Datetime': now}

            return {'File': self.path, 'Process': 'Embed Thumbnail in Video', 'State': 1,
                    'Message': 'GIF Extracted Successfully','Save Location': str(gif), 'Datetime': now}

        except subprocess.TimeoutExpired:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                'State': 0, 'Error': "Process took too long and was terminated.", 'Datetime': now}

        except subprocess.SubprocessError as sub_error:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                'State': 0, 'Error': f'Subprocess error occurred: {sub_error}', 'Datetime': now}

        except Exception as e:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                'State': 0, 'Error': f"An unexpected error occurred: {e}", 'Datetime': now}


    def embed_thumbnail_video(self, image_file: File | ImageOperations, output_file: File = File('')) -> dict:
        '''
        Embeds thumbnails in Videos
        
        Parameters
        ----------
            image_file : File | ImageOperations
                File Object contains Image path that will be embedded in the video
            output_file : File
                Must not be passed explicitly, only `embed_thumbnail_in_folder` function is allowed to pass arguments for this parameter
        '''
        now = time.ctime()
        try:
            if not self.isfile():
                return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                    'State': 0, 'Error': "File doesn't Exist", 'Datetime': now}
            if not (self.ext.lower() in self._supported):
                return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                    'State': 0, 'Error': f"File of type {self.ext} is not supported", 'Datetime': now}
            if str(output_file) == '':
                url_or_localpath = download_thumbnail(str(image_file))

                # Variable that indicates if there is an images downloaded or needed to be converted to a supported format
                # to perform the embedding operation successfully
                # so that we can delete all the temp images as they are not needed after operation is done.
                local_image = True
                converted_image = False
                if url_or_localpath:
                    image_file = url_or_localpath
                    local_image = False
                else:
                    if not image_file.isfile():
                        return {'File': self.path, 'Process': 'Embed Thumbnail in Video',
                            'State': 0, 'Error': f'Image "{str(image_file)}" doesn\'t exist', 'Datetime': now}
                
                if image_file.ext == '.webp':
                    temp_image = image_file
                    image_file = ImageOperations(image_file.convert_image('.png').get("Save Location"))
                    converted_image = True
                    if not local_image:
                        temp_image.remove()

                retrieved_outout = str(output_file)
                output_file = File(f"Media Files Manager/Video Thumbnail/{self.name}{self.ext}")
                output_file.validate_name()

            command = [
                'ffmpeg',
                '-i', self.path,
                '-i', str(image_file),
                '-map', '0',
                '-map', '1',
                '-c', 'copy',
                '-disposition:v:1', 'attached_pic',
                str(output_file)
            ]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if locals().get('retrieved_outout') != None:
                if (not local_image) or (converted_image):
                    image_file.remove()

            if result.returncode != 0:
                return {'File': self.path, 'Process': 'Embed Thumbnail in Video', 'State': 0,
                    'Error': f'successfully embedded thumbnail into video but other Error occured: {result.stderr}', 'Datetime': now}
            else:
                return {'File': self.path, 'Process': 'Embed Thumbnail in Video', 'State': 1,
                    'Message': 'Thumbnail embedded Successfully','Save Location': str(output_file), 'Datetime': now}

        except FileNotFoundError as fnf_error:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video', 'State': 0,
                    'Error': f'File error: {fnf_error}', 'Datetime': now}
        except subprocess.SubprocessError as sub_error:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video', 'State': 0,
                    'Error': f'Subprocess error occurred: {sub_error}', 'Datetime': now}
        except Exception as e:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Video', 'State': 0,
                    'Error': f'An unexpected error occurred: {e}', 'Datetime': now}
    
    
    def extract_original_audio(self) -> dict:
        '''
        Extracts the original audio stream from a video file without re-encoding,
        automatically detects codec and assigns the correct file extension.
        '''
        now = time.ctime()

        try:
            if not self.isfile():
                return {'File': self.path, 'Process': 'Extract Original Audio',
                        'State': 0, 'Error': "File doesn't Exist", 'Datetime': now}
            if not self.ext.lower() in self._supported:
                return {'File': self.path, 'Process': 'Extract Original Audio',
                        'State': 0, 'Error': f"File of type {self.ext} is not supported", 'Datetime': now}

            # Step 1: Probe audio codec
            probe_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                        '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', self.path]
            codec_result = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            codec = codec_result.stdout.strip()

            if codec == '':
                return {'File': self.path, 'Process': 'Extract Original Audio',
                        'State': 0, 'Error': 'Could not detect audio codec', 'Datetime': now}

            # Map codec to a proper file extension
            codec_extension_map = {
                'aac': 'aac',
                'mp3': 'mp3',
                'opus': 'opus',
                'vorbis': 'ogg',
                'flac': 'flac',
                'pcm_s16le': 'wav'
            }
            ext = codec_extension_map.get(codec, 'mka')  # fallback to .mka if unknown

            output_file = File(f"Media Files Manager/Extracted Audio/{self.name}.{ext}")
            output_file.validate_name()

            # Step 2: Extract audio stream without re-encoding
            extract_cmd = [
                'ffmpeg',
                '-i', self.path,
                '-vn',
                '-acodec', 'copy',
                str(output_file)
            ]

            result = subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                return {'File': self.path, 'Process': 'Extract Original Audio',
                        'State': 0, 'Error': result.stderr, 'Datetime': now}
            else:
                return {'File': self.path, 'Process': 'Extract Original Audio',
                        'State': 1, 'Message': f'Original audio extracted using codec "{codec}"',
                        'Save Location': str(output_file), 'Datetime': now}

        except FileNotFoundError as fnf_error:
            return {'File': self.path, 'Process': 'Extract Original Audio',
                    'State': 0, 'Error': f'File error: {fnf_error}', 'Datetime': now}
        except subprocess.SubprocessError as sub_error:
            return {'File': self.path, 'Process': 'Extract Original Audio',
                    'State': 0, 'Error': f'Subprocess error occurred: {sub_error}', 'Datetime': now}
        except Exception as e:
            return {'File': self.path, 'Process': 'Extract Original Audio',
                    'State': 0, 'Error': f'An unexpected error occurred: {e}', 'Datetime': now}




class Audio(File):
    '''
    Audio
    =====
    
    Class has the following functionalities:
        - Embed thumbnails into Audio Files
    
    Attributes
    ----------
        path (str): Path of the Audio File
        name (str): Name of the Audio file without extension
        ext (str): Audio Extension (Audio Type)
        _supported (list): contains supported Audio formats that can be handled by this class


    Methods
    -------
        embed_thumbnail_audio (File | ImageOperations, File) -> dict:
            Embeds thumbnails in Audio files
    '''
    _supported = ['.mp3', '.flac', '.m4a', '.mka']

    def __init__(self, path):
        super().__init__(path)


    def embed_thumbnail_audio(self, image_file: File | ImageOperations, output_file: File = File('')) -> dict:
        '''
        Embeds thumbnails in Audio Files
        
        Parameters
        ----------
            image_file : File | ImageOperations
                File Object contains Image path that will be embedded in the Audio
            output_file : File
                Must not be passed explicitly, only `embed_thumbnail_in_folder` function is allowed to pass arguments for this parameter
        '''
        now = time.ctime()
        try:
            if not self.isfile():
                return {'File': self.path, 'Process': 'Embed Thumbnail in Audio',
                    'State': 0, 'Error': "File doesn't Exist", 'Datetime': now}
            if not (self.ext.lower() in self._supported):
                return {'File': self.path, 'Process': 'Embed Thumbnail in Audio',
                    'State': 0, 'Error': f"File of type {self.ext} is not supported", 'Datetime': now}
            if str(output_file) == '':
                url_or_localpath = download_thumbnail(str(image_file))

                # Variable that indicates if there is an images downloaded or needed to be converted to a supported format
                # to perform the embedding operation successfully
                # so that we can delete all the temp images as they are not needed after operation is done.
                local_image = True
                converted_image = False
                if url_or_localpath:
                    image_file = url_or_localpath
                    local_image = False
                else:
                    if not image_file.isfile():
                        return {'File': self.path, 'Process': 'Embed Thumbnail in Audio',
                            'State': 0, 'Error': f'Image "{str(image_file)}" doesn\'t exist', 'Datetime': now}

                if image_file.ext == '.webp' or self.ext.lower() in ['.m4a']:
                    convert_to_format = '.png' if self.ext.lower() not in ['.m4a'] else '.jpg'
                    temp_image = image_file
                    image_file = ImageOperations(image_file.convert_image(convert_to_format).get("Save Location"))
                    converted_image = True
                    if not local_image:
                        temp_image.remove()

                retrieved_outout = str(output_file)
                output_file = File(f"Media Files Manager/Audio Thumbnail/{self.name}{self.ext}")
                output_file.validate_name()
            else:
                if self.ext.lower() in ['.m4a'] and image_file.ext != '.jpg':
                    tttk = 's'      # not for any useful except checking if this condition has been met
                    convert_to_format = '.jpg'
                    image_file = ImageOperations(image_file.convert_image(convert_to_format).get("Save Location"))
                    converted_image = True

            if self.ext.lower() in ['.mp3', '.flac', '.mka']:
                command = [
                    'ffmpeg',
                    '-i', self.path,
                    '-i', str(image_file),
                    '-map', '0',
                    '-map', '1',
                    '-c', 'copy',
                    '-id3v2_version', '3',
                    '-metadata:s:v', 'title="Album cover"',
                    '-metadata:s:v', 'comment="Cover (front)"',
                    str(output_file)
                ]
            elif self.ext.lower() in ['.m4a']:
                command = [
                    'ffmpeg',
                    '-i', self.path,
                    '-i', str(image_file),
                    '-map', '0',
                    '-map', '1',
                    '-c:a', 'copy',
                    '-c:v:1', 'png',
                    '-disposition:v:1',
                    'attached_pic',
                    str(output_file)
                ]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if locals().get('retrieved_outout') != None:
                if (not local_image) or (converted_image):
                    image_file.remove()
            if locals().get('tttk') != None:
                image_file.remove()

            if result.returncode != 0:
                return {'File': self.path, 'Process': 'Embed Thumbnail in Audio', 'State': 0,
                    'Error': f'successfully embedded thumbnail into video but other Error occured: {result.stderr}', 'Datetime': now}
            else:
                return {'File': self.path, 'Process': 'Embed Thumbnail in Audio', 'State': 1,
                    'Message': 'Thumbnail embedded Successfully','Save Location': str(output_file), 'Datetime': now}

        except FileNotFoundError as fnf_error:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Audio', 'State': 0,
                    'Error': f'File error: {fnf_error}', 'Datetime': now}
        except subprocess.SubprocessError as sub_error:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Audio', 'State': 0,
                    'Error': f'Subprocess error occurred: {sub_error}', 'Datetime': now}
        except Exception as e:
            return {'File': self.path, 'Process': 'Embed Thumbnail in Audio', 'State': 0,
                    'Error': f'An unexpected error occurred: {e}', 'Datetime': now}




def embed_thumbnail_in_folder(folder: Directory, image_file: File | ImageOperations, media: str, progress_callback: Callable | None = None) -> dict:
    '''
    Embeds a thumbnail in each Video/Audio File in a Folder
    
    Parameters
    ----------
        folder : Directory
            Directory Object Contains the path of the folder that all Vido/Audio files in it will be embedded with thumbnail
        image_file : File | ImageOperations
            ImageOperations Object contains the oath of the thumbnail image
        media : str
            Media type `Video` or ` Audio` only
    '''
    now = time.ctime()

    if not folder.isdir():
        return {'File': str(folder), 'Process': f'Embed Thumbnail in {media}',
                'State': 0, 'Error': "Folder doesn't Exist", 'Datetime': now}
    url_or_localpath = download_thumbnail(str(image_file))
    
    # Variable that indicates if there is an images downloaded or needed to be converted to a supported format
    # to perform the embedding operation successfully
    # so that we can delete all the temp images as they are not needed after operation is done.
    local_image = True
    converted_image = False

    if url_or_localpath:
        image_file = url_or_localpath
        local_image = False
    else:
        if not image_file.isfile():
            return {'File': str(folder), 'Process': f'Embed Thumbnail in {media}',
                    'State': 0, 'Error': f'Image "{str(image_file)}" doesn\'t exist', 'Datetime': now}
    
    if image_file.ext == '.webp':
        temp_image = image_file
        image_file = ImageOperations(image_file.convert_image('.png').get("Save Location"))
        converted_image = True
        if not local_image:
            temp_image.remove()

    Insiders = []

    save_folder = Directory(f"Media Files Manager/{media} Thumbnail/{folder.basename}")
    save_folder.make()

    for filename in folder.list_dir():

        file = Directory(str(folder))
        file.join(filename)
        file = Video(str(file)) if media == 'Video' else Audio(str(file))

        new_file = File(save_folder.path + '/' + filename)
        new_file.validate_name()

        try:
            if media == 'Video':
                result = file.embed_thumbnail_video(image_file, new_file)
            elif media == 'Audio':
                result = file.embed_thumbnail_audio(image_file, new_file)

            Insiders.append(result)
            if result['State'] == 1:
                msg = f"✅ Thumbnail Embedded successfully: {file.name + file.ext}"
                if progress_callback:
                    progress_callback(msg)
            else:
                msg = f"❌ {file.name + file.ext}: {result['Error']}"
                if progress_callback:
                    progress_callback(msg)

        except Exception as e:
            Insiders.append({'File': file.path, 'Process': f'Embed Thumbnail in {media}', 'State': 0,
                            'Error': f'An unexpected error occurred while processing "{file.path}": {e}',
                            'Datetime': now})
    if (not local_image) or (converted_image):
        image_file.remove()

    return {'File': folder.path, 'Process': 'Embed Thumbnail in Video', 'State': 1,
            'Message': 'Batch thumbnail embedding process completed.','Save Location': abs(save_folder), 'Datetime': now,
            "Insiders": Insiders}


def download_thumbnail(url: str) -> bool | ImageOperations:
    '''Downloads an Image from the internet
    
    Parameters
    ----------
        url : str
            the URL of the image
    '''
    parsed = urlparse(url)

    if parsed.scheme == "https" and parsed.netloc:
        r = requests.get(url)
        if r.status_code == 200:
            content_type = r.headers.get('Content-Type', "")
            if content_type:
                type_file, ext = content_type.split("/")
                if type_file == "image":
                    name = Directory(f'{parsed.path}').basename or "downloaded_image"
                    ext = '.' + ext
                    name = name.rstrip(ext)
                    file_name = name + ext

                    image_file = ImageOperations(f"Media Files Manager/Temp/{file_name}")
                    image_file.validate_name()
                    try:
                        with open(str(image_file), 'wb') as handler:
                            handler.write(r.content)
                        return image_file
                    except Exception:
                        return False
                else:
                    return False
            else:
                 return False
        else:
            return False
    else:
        return False
