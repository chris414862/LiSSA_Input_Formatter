import sys
import os
import pathlib
import argparse
import re
import csv
from typing import List
from utils.helper_classes import lissa_annotation
from collections import Counter


def err_exit(message):
    print(message)
    sys.exit()


def check_filename_list(f_list):
    for filename in f_list:
        # print("Checking "+filename)
        if not pathlib.Path(filename).is_file():
            err_exit(filename+" is not a file.")

    return True


def parse_args():
    parser = argparse.ArgumentParser(description="Uniformly formats different annotation files with varying"\
                                                 " styles for input into LiSSA")
    parser.add_argument("-dsafe", nargs="*", help="filename for annotations from DroidSafe")
    parser.add_argument("-susi", nargs="*", help="filename for annotations from SuSi")
    parser.add_argument("-perm_map", help="filename for methods that were mapped to permissions")
    parser.add_argument("-docs", help="filename for full method documentation. Helps resolve incomplete entries.")

    parse = parser.parse_args()
    if (parse.dsafe == None or parse.dsafe == []) and  (parse.dsafe == None or parse.susi == [] ):
        err_exit("Must enter a filename after either -dsafe flag or -susi flag")
    check_filename_list(parse.dsafe + parse.susi)


    return parse


def get_ann_type(fname):
    if re.search(r"[Ss]ource", fname):
        ann_type = "source"
    elif re.search(r"[Ss]ink", fname):
        ann_type = 'sink'
    else:
        ann_type = ''

    return ann_type


def get_file_contents(fname):
    with open(fname, encoding="utf-8") as f:
        ret_list = [l.strip() for l in f.readlines()]
    return ret_list

def get_file_contents_csv(fname):
    with open(fname, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, dialect='excel')
        ret = [row for row in reader]
    return ret


def save_annotations(annotations:List[lissa_annotation], out_filename:str):
    with open(out_filename,'w', newline='', encoding='utf-8') as f:
        writer:csv.DictWriter = csv.writer(f, dialect='excel')
        for ann in annotations:
            row_to_write = ann.to_string().split('|||')
            writer.writerow(row_to_write)


def get_annotation_stats(annotations:List[lissa_annotation]):
    '''
    Extracts count information about the annotations

    :param annotations:
    :return:
    '''

    ret_dict = {'SinksAndSourcesByCat':{'sink':Counter(), 'source':Counter(), 'none':Counter(),
                                        'unannotated':Counter()},
                'SinksAndSourcesCount':{'sink':0,'source':0, 'none':0, 'unannotated':0},
                'Categories':Counter(),
                'Origin':{'dsafe':0, 'susi':0, 'perm_map':0},
                'OriginByCat':{'dsafe':Counter(), 'susi':Counter(), 'perm_map':Counter()},
                'OriginBySS':{'dsafe':Counter(), 'susi':Counter(), 'perm_map':Counter()}}

    for ann in annotations:
        # print(ann.to_string())
        ret_dict['SinksAndSourcesByCat'][ann.source_or_sink][ann.category] += 1
        ret_dict['SinksAndSourcesCount'][ann.source_or_sink] += 1
        ret_dict['Categories'][ann.category] += 1
        ret_dict['Origin'][ann.origin] += 1
        ret_dict['OriginByCat'][ann.origin][ann.category] += 1
        ret_dict['OriginBySS'][ann.origin][ann.source_or_sink] += 1

    return ret_dict


def print_stats(stats):

    # Basic counts
    print("\n\nANNOTATION COUNTS")
    print("Num. sinks:\t\t",stats['SinksAndSourcesCount']['sink'],"\t\tNum. sources:\t",
          stats['SinksAndSourcesCount']['source'])
    print("From DroidSafe:\t",stats['Origin']['dsafe'],'\t\tFrom SuSi:\t\t',stats['Origin']['dsafe']
          ,'\tFrom permission map:\t',stats['Origin']['perm_map'])

    # Category counts
    print("\nBy Category:")
    [print(f"\t{key:<30s}{str(stats['Categories'][key]):>10s}") for key in stats['Categories'].keys()]

    # Category counts grouped by source and sink
    print("\nCategories grouped by sources:")
    [print(f"\t{key:<30s}{str(stats['SinksAndSourcesByCat']['source'][key]):>10s}") for key in
                                                                        stats['SinksAndSourcesByCat']['source'].keys()]
    print("\nCategories grouped by sinks:")
    [print(f"\t{key:<30s}{str(stats['SinksAndSourcesByCat']['sink'][key]):>10s}") for key in
     stats['SinksAndSourcesByCat']['sink'].keys()]

    # Categoty counts grouped by origin (permission map did not have categories
    print("\nCategory counts from DroidSafe:")
    [print(f"\t{key:<30s}{str(stats['OriginByCat']['dsafe'][key]):>10s}") for key in
     stats['OriginByCat']['dsafe'].keys()]
    print("\nCategory counts from SuSi:")
    [print(f"\t{key:<30s}{str(stats['OriginByCat']['susi'][key]):>10s}") for key in
     stats['OriginByCat']['susi'].keys()]



