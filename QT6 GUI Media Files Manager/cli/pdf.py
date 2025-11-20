from cli.File import File, Directory
import os
import time
import requests
import fitz
from cli.user_input_handler import pdf_split_handle_input, pdf_pd_input

class PDF(File):
    '''
    Class PDF
    =========
    This class is used to apply the following operations on PDF Files
    - Splitting PDF from specific page
    - Merging Two PDFs Together
    - Extract all Images in a PDF File
    - Delete Specific Pages from a PDF
    - Converting PDF Files into DOCX
    - Converting PDF Files into PPTX 
    
    Attributes
    ----------
        path (str): Path of the PDF File
        name (str): Name of the PDF file without `.pdf` extension
        ext (str): PDF Extension `.pdf`
        doc (Document): Document Object from `fitz` Module

    Methods
    -------
        open() -> None:
            Opens an instance of the Document in the Memory
        
        close() -> None:
            Deletes the PDF Document instance from the Memory
        
        split_pdf(int, int, str) -> dict:
            Splits PDF from certain Page to another one and saves extracted pdf within the range specified
            into the folder specified
        
        merge_pdf(iterable, str) -> dict:
            Merge Two or more PDF Files together
        
        pdf_extract_images() -> dict:
            EXtracts all Images in PDF File
        
        pdf_pages_delete() -> dict:
            Remove Specific Pages in a PDF and save a copy in the same folder where the original one exists

        convert_pdf(str) -> dict:
            Convert PDF Files with cloudconvert API
    '''
    def __init__(self, path: str):
        super().__init__(path)
        self.doc = None



    def open(self) -> None:
        '''Opens PDF Document and Store in in self.doc Attribute'''
        self.doc = fitz.open(self.path)



    def close(self) -> None:
        '''Closes PDF Document'''
        self.doc.close()



    def split_pdf(self, start_page: str, end_page: str, save_folder: str) -> dict:
        '''
        Splits PDF from certain Page to another one and saves extracted pdf within the range specified
        into the folder specified
        
        Parameters
        ----------
            start_page:
                Page to start splitting from
            
            end_page:
                Page to end split
            
            save_folder:
                path of the folder to save the extracted pdf 
        '''
        now = time.ctime()
        if not self.exist():
            return {'File': self.path,
                    'Process': 'Split PDF',
                    'State': 0,
                    'Error': "PDF File doesn't exist",
                    'Datetime': now}

        if not self.ext == '.pdf':
            return {'File': self.path,
                    'Process': 'Split PDF',
                    'State': 0,
                    'Error': "File type is not PDF.",
                    'Datetime': now}

        try:
            self.open()

            start_page, end_page = pdf_split_handle_input(self.doc, start_page, end_page)
            
            new_doc = fitz.open()                   # Create a new empty PDF
            new_doc.insert_pdf(self.doc, from_page=start_page-1, to_page=end_page-1)

            save_dir = Directory(save_folder)
            if save_dir.isdir():
                new_pdf_name = f'Page{start_page}-{end_page} ' + self.name + self.ext
                save_file_path = File(os.path.join(str(save_dir), new_pdf_name))
                save_file_path.validate_name()
            else:
                return {'File': self.path,
                    'Process': 'Split PDF',
                    'State': 0,
                    'Error': 'Folder Specified to Save new PDF doesn\'t exist',
                    'Datetime': now}

            new_doc.save(str(save_file_path))
            new_doc.close()
            self.close()

            return {'File': self.path,
                    'Process': 'Split PDF',
                    'State': 1,
                    'Message': 'Split Process completed',
                    'Save Location': f'{save_file_path}',
                    'Datetime': now}
        except Exception as e:
            return {'File': self.path,
                    'Process': 'Split PDF',
                    'State': 0,
                    'Error': f'Error Occured: {e}',
                    'Datetime': now}



    def merge_pdf(self, files_to_merge: tuple | list, save_path: str) -> dict:
        '''
        Merge Two or more PDF Files together
        
        Paramaters
        ---------
            files_to_merge:
                An iterable contains all PDF files you want to merge
            save_path:
                The Folder Path and Output PDF File Name that contains all PDF files that will be merged  
        '''
        output = fitz.open()
        errors_list = []
        now = time.ctime()

        for file in files_to_merge:
            pdf = PDF(file)
            if pdf.isfile() and pdf.ext == '.pdf':
                try:
                    with fitz.open(pdf.path) as doc:
                        output.insert_pdf(doc)
                except Exception as e:
                    errors_list.append(f"An Unexcepected Error occured {e} - file: {pdf.path}")
            else:
                errors_list.append(f"{pdf.path} is not of type PDF or doesn't exist")
        try:
            assert len(errors_list) < len(files_to_merge)-1, "Failed to Merge PDF Files"
            save_l = File(save_path)
            assert Directory(save_l.dir()).isdir(), "Directory specified to save new PDF file is not exist"

            save_l.validate_name()
            assert save_l.isvalid(['.pdf']), "Specified Name of saved PDF file doesn't contain .pdf"
            output.save(str(save_l.path))
            output.close()
            return {'File':files_to_merge,
                    'Process': 'Merge',
                    'State': 1,
                    'Message': 'Merge Process completed',
                    'Save Location': f'{save_l}',
                    'Error': errors_list,
                    'Datetime': now}
        except Exception as e:
            errors_list.append(f"Error while saving final PDF file: {e}")
            return {'File':files_to_merge,
                    'Process': 'Merge',
                    'State': 0,
                    'Error': errors_list,
                    'Datetime': now}



    def pdf_extract_images(self) -> dict:
        '''EXtracts all Images in PDF File'''
        now = time.ctime()
        if self.isfile() and self.ext == '.pdf':
            try:
                self.open()
                images_count = 0
                page_num = 0

                make = Directory(f"Media Files Manager/Extract Images/{self.name}")
                make.make()

                for page in self.doc:
                    page_num += 1
                    for img in page.get_images():
                        try:
                            xref = img[0]
                            pix = fitz.Pixmap(self.doc, xref)
                            pix.save(f"{make.path}/{page_num}_image_{xref}.png")
                            images_count += 1
                        except Exception as e:
                            print(f'❌ Skipped Saving image{xref} in page {page_num} due to {e}')
                self.close()
                now = time.ctime()
                return {'File':self.path,
                    'Process': 'Extract Images',
                    'State': 1,
                    'Message': f"Extraction completed. {images_count} image(s) saved",
                    'Save Location': f'{Directory(f'Media Files Manager/Extract Images/{self.name}').__abs__()}',
                    'Datetime': now}
            except Exception as e:
                return {'File':self.path,
                    'Process': 'Extract Images',
                    'State': 0,
                    'Error': f"An unexcepected error occured {e}",
                    'Datetime': now}
        else:
            return {'File':self.path,
                    'Process': 'Extract Images',
                    'State': 0,
                    'Error': f"{self.path} do not exist or not a PDF file type",
                    'Datetime': now}



    def pdf_pages_delete(self, nums: str) -> dict:
        '''Remove Specific Pages in a PDF and save a copy in the same folder where the original one exists'''
        now = time.ctime()
        if self.isfile() and self.ext == '.pdf':
            try:
                self.open()
                delete = pdf_pd_input(nums)
                self.doc.delete_pages(delete)
                save_dir = File(os.path.join(self.dir(), 'modified_' + self.name + self.ext))
                save_dir.validate_name()
                self.doc.save(str(save_dir))
                self.close()
                return {'File': self.path,
                    'Process': 'Delete Pages from PDF',
                    'State': 1,
                    'Message': f"Pages deletion completed\nFile Saved at: {str(save_dir)}",
                    'Save Location': str(save_dir),
                    'Datetime': now}
            except Exception as e:
                return {'File':self.path,
                    'Process': 'Delete Pages from PDF',
                    'State': 0,
                    'Error': f"An unexcepected error occured {e}",
                    'Datetime': now}
        else:
            return {'File':self.path,
                    'Process': 'Delete Pages from PDF',
                    'State': 0,
                    'Error': f"{self.path} do not exist or not a PDF file type",
                    'Datetime': now}



    # def _convert_pdf2docs(self, name: str) -> str:
    #     '''
    #     Convert PDF to a DOCX file using pdf2docx library
        
    #     Parameters
    #     ----------
    #         name : str
    #             The Path (containing file name) where to save the new docx file generated from pdf file  
    #     '''           
    #     try:
    #         cv = Converter(self.path)
    #         cv.convert(name, start=0, end=None)     # Convert all pages
    #         cv.close()
    #         return 1, "Conversion complete."
    #     except Exception as e:
    #         return 0, f"Error occured while Conversion Process: {e}"



    # def convert_pdf(self, converted_to: str) -> dict:
    #     '''
    #     Convert PDF Files with cloudconvert API
        
    #     Parameters
    #     ----------
    #         converted_to : str
    #             must be one of these three option (docx, pptx, xlsx)  
    #     '''
    #     now = time.ctime()
    #     if not self.isfile():
    #         return {'File':self.path,
    #                 'Process': 'Convert PDF',
    #                 'State': 0,
    #                 'Error': "PDF File doesn't exist",
    #                 'Datetime': now}
    #     if not self.ext == '.pdf':
    #         return {'File':self.path,
    #                 'Process': 'Convert PDF',
    #                 'State': 0,
    #                 'Error': "File type is not PDF format",
    #                 'Datetime': now}
    #     if converted_to.lower() not in ('docx','xlsx','pptx'):
    #         return {'File':self.path,
    #                 'Process': 'Convert PDF',
    #                 'State': 0,
    #                 'Error': "Conversion type is not Spported",
    #                 'Datetime': now}

    #     try:
    #         api_key = ''

    #         cloudconvert.configure(api_key=api_key)

    #         # Step 2: Create the conversion job
    #         job = cloudconvert.Job.create(payload={
    #             "tasks": {
    #                 'import-1': {
    #                     'operation': 'import/upload'
    #                 },
    #                 'convert-1': {
    #                     'operation': 'convert',
    #                     'input': 'import-1',
    #                     'input_format': 'pdf',
    #                     'output_format': f'{converted_to.lower()}'
    #                 },
    #                 'export-1': {
    #                     'operation': 'export/url',
    #                     'input': 'convert-1'
    #                 }
    #             }
    #         })

    #         # Step 3: Upload your PDF to CloudConvert
    #         upload_task = job['tasks'][0]
    #         upload_url = upload_task['result']['form']['url']
    #         form_parameters = upload_task['result']['form']['parameters']

    #         with open(self.path, 'rb') as file:
    #             files = {'file': file}
    #             response = requests.post(upload_url, data=form_parameters, files=files)

    #         # Step 4: Wait for the job to finish
    #         job = cloudconvert.Job.wait(id=job['id'])

    #         # Step 5: Get the export task and download URL
    #         for task in job['tasks']:
    #             if task['name'] == 'export-1':
    #                 file_info = task['result']['files'][0]
    #                 download_url = file_info['url']
    #                 filename = file_info['filename']
    #                 print("Download URL:", download_url)

    #                 # Step 6: Download the converted file
    #                 docx_response = requests.get(download_url)
    #                 if docx_response.status_code != 200:
    #                     raise Exception("Error fetching converted file from download URL")
    #                 save_dir = File(f"Media Files Manager/PDF to Office/{filename}")
    #                 save_dir.validate_name()
    #                 with open(str(save_dir), 'wb') as output_file:
    #                     output_file.write(docx_response.content)

    #                 return {'File':self.path,
    #                         'Process': 'Convert PDF',
    #                         'State': 1,
    #                         'Message': f"File converted, saved as '{save_dir.name + save_dir.ext}'",
    #                         'Save Location': f'{File(abs(save_dir)).dir()}',
    #                         'Datetime': now}
    #     except Exception as e:
    #         if converted_to.lower() == 'docx':
    #             print(f"An unexpected error occurred: {e}")
    #             name_docx = File(f"Media Files Manager/PDF to Office/{self.name}.docx")
    #             name_docx.validate_name()
    #             print("try 2: Converting through pdf2docx")
    #             st, res = self._convert_pdf2docs(str(name_docx))
    #             errors = [f"An unexpected error occurred: {e}"] if st else [f"An unexpected error occurred: {e}", res]
    #             mes = f"File converted, saved as '{name_docx.name + name_docx.ext}'" if st else None
    #             loc = f'{File(abs(name_docx)).dir()}' if st else None

    #             return {'File':self.path,
    #                     'Process': 'Convert PDF',
    #                     'State': st,
    #                     'Message': mes,
    #                     'Save Location': loc,
    #                     'Error': errors,
    #                     'Datetime': now}

    #         else:
    #             return {'File':self.path,
    #                 'Process': 'Convert PDF',
    #                 'State': 0,
    #                 'Error': f"An unexpected error occurred: {e}",
    #                 'Datetime': now}