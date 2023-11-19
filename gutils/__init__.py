import os
import csv
from typing import List
from .ckpt_tr import WeightTrans
from .logger import get_logger
from .utils import print_run_time

__all__ = ['WeightTrans', 'get_logger', 'print_run_time',
           'csvwriter', 'path_builder']

def csvwriter(path_csv: str, content: List[str]) -> None:
    """
    open a csv file, and add content at the end of file
    """
    with open(path_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(content)

def path_builder(path: str) -> str:
    if not os.path.exists(path):
        os.makedirs(path)
    return path