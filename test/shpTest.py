import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.file_handler import extract_zip

zip_path = r'D://Desktop//土地利用.zip'
extract_zip(Path(zip_path), Path(r'data\uploads'))