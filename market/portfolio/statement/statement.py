import fitz
from pprint import pp
from datetime import datetime

class Statement():
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        self.doc = fitz.open(self.pdf_file)
        self.page_count = self.doc.page_count

        # get creation date
        date_string = self.doc.metadata['creationDate']
        # print(date_string)
        # year = date_string[2:6]
        # month = date_string[6:8]
        # day = date_string[8:10]
        # self.creation_date = datetime(year=int(year), month=int(month), day=int(day))

        self.blocks = {}
        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            text_blocks = page.get_text('blocks')
            blocks = []
            for block in text_blocks:
                lines = []
                for line in block[4].split('\n'):
                    line = line.strip()
                    if line != '':
                        lines.append(line.strip())
                if len(lines) != 0:
                    blocks.append(lines)
            self.blocks[page_num] = blocks
        
        self.doc.close()

    def get_page_blocks(self, page_num):
        if page_num in self.blocks:
            return self.blocks[page_num]
        else:
            raise Exception(f'Page {page_num} not found: {self.pdf_file}')
    
    def get_page_lines(self, page_num):
        lines = []
        for block in self.get_page_blocks(page_num):
            lines += block
        return lines
    
    def get_blocks(self):
        return self.blocks

    def get_lines(self):
        lines = []
        for page_num in sorted(self.blocks.keys()):
            for block in self.blocks[page_num]:
                lines += block

        return lines

    def get_tables(self, page_num):
        self.doc = fitz.open(self.pdf_file)
        page = self.doc.load_page(page_num)
        tables = page.find_tables().tables
        pp(tables)
        self.doc.close()
