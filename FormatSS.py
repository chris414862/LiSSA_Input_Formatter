import re
from utils.helper_classes import lissa_annotation
from utils.helper_funcs import  get_file_contents, parse_args, get_file_contents_csv, get_ann_type,save_annotations
from utils.helper_funcs import  get_annotation_stats, print_stats
from utils.parse_funcs import parse_susi_ann_line,parse_dsafe_ann_line,parse_perm_map_line
from typing import List

'''
This module was created to unify and standardize the annotations for training/optimizing the LiSSA classifier. The 
annotations were taken from annotations done in two previous projects: the SuSi project (https://github.com/
secure-software-engineering/SuSi/tree/develop/SourceSinkLists/Android%204.2/SourcesSinks), and the DroidSafe project
(https://github.com/MIT-PAC/droidsafe-src, scanning_2014-02-10.txt). A third set of methods are also added to provide
more negative samples. These are the methods output from our tool to map Android permissions to methods based on the 
documentation. Any methods that were annotated in a different set will be given that annotation.

Besides standardizing the string representations of the methods and annotations, this module also resolves any duplicate
methods. During this process, if either method has a neutral (i.e. no annotation or no category etc.) annotation the
it is assumed the true annotation is the non-neutral one. This is an imperfect assumption, but this does not constitute
very many methods, as agreement was fairly high, so we will address it later if we find evidence of a problem.
'''


def get_anns_internal(lines: list, parse_func, source_or_sink="", origin=''):
    '''
    Generalized function that invokes arbitrary parse function and aggregates annotations to list

    :param lines:           Lines from file
    :param parse_func:      Function to parse one line
    :param source_or_sink:  Needed for susi annotations since they are separated by file
    :param origin:          Where lines came from [dsafe, susi, perm_map]
    :return:
    '''
    print(len(lines))
    method_anns = []
    for method_ann in lines:
        parse = parse_func(method_ann, source_or_sink=source_or_sink)
        if parse == {}:
            continue
        method_anns.append(lissa_annotation(method_name=parse["meth_name"], parameters=parse["meth_params"],
                                            returns=parse["ret_type"], category=parse["category"],
                                            source_or_sink=parse["source_or_sink"], origin=origin))

    return method_anns


def get_anns_from_file_list(fnames: list = [], get_contents_func=None, parse_func=None, origin:str=''):
    '''
    Wrapper around get_anns_internal that iterates through filename list and handle unique file level issues (i.e.
    SuSi's separation of sources and sinks into different files)

    :param fnames:
    :param get_contents_func:   arbitrary function for extracting lines from a file
    :param parse_func:          arbitrary function for parsing a line from the file type in the fnames list
    :param origin:              string indicating which files these are [dsafe, susi, perm_map]
    :return:
    '''
    annotations = []
    for fname in fnames:
        source_or_sink = get_ann_type(fname)
        lines = get_contents_func(fname)
        annotations += get_anns_internal(lines, parse_func, source_or_sink=source_or_sink, origin=origin)

    return annotations


def get_annotations(dsafe_files:list=None, susi_files:list=None, perm_map_files:list=None):
    '''
    Entry point function to extract unified annotations. All filenames should be in a list to accommodate iteration.

    :param dsafe_files:
    :param susi_files:
    :param perm_map_files:
    :return:
    '''
    annotations = []
    annotations += get_anns_from_file_list(dsafe_files, get_file_contents, parse_dsafe_ann_line, "dsafe")
    annotations += get_anns_from_file_list(susi_files, get_file_contents, parse_susi_ann_line, "susi")
    annotations += get_anns_from_file_list(perm_map_files, get_file_contents_csv, parse_perm_map_line, "perm_map")

    annotations = resolve_dups(annotations)

    return annotations


def resolve_dups(annotations: List[lissa_annotation]):
    '''
    Many of the methods in the three files are duplicates. This method detects these copies and resolves any differences
    in the annotations. Broadly, differences are primarily resolved by assuming the annotation that was more specific
    was correct. We define "unannotated", "none", and "NO_CATEGORY" as less specific and everything else as more
    specific (e.g. "source","sink","some category").

    :param annotations:  list of lissa_annotation objects
    :return:
    '''
    seen_names = dict()
    new_list = []
    for ann in annotations:
        # If we haven't seen it
        full_name = ann.class_name + "." + ann.method_name + "(" + ",".join(
            [p.split(".")[-1] for p in ann.parameters]) + ")"
        if full_name not in seen_names:
            seen_names[full_name] = ann
            new_list.append(ann)

        # If we have seen it
        else:
            # Check if they have different annotations for source and sink
            if seen_names[full_name].source_or_sink != ann.source_or_sink:
                # Choose the more specific annotation
                if seen_names[full_name].source_or_sink == 'unannotated' \
                        or  seen_names[full_name].source_or_sink == 'none':
                    seen_names[full_name] = ann

                # If they disagree on specific annotation, alert user
                elif ann.source_or_sink != 'unannotated':
                    print("houston we have a problem:", full_name)
                    print(ann.source_or_sink + ' ' + ann.origin, "|||",
                          seen_names[full_name].source_or_sink + " " + seen_names[full_name].origin)

                    # Found one disagreement (manually) and DroidSafe appeared more correct
                    if full_name == "android.content.ContextWrapper.openFileInput(String)":
                        print("Using DroidSafe annotation:")
                        if ann.origin == "dsafe":
                            seen_names[full_name] = ann
                        print(seen_names[full_name].source_or_sink)

            # Check if they have different annotations for source and sink
            elif seen_names[full_name].category != ann.category:
                # Choose the more specific annotation
                if seen_names[full_name].category == 'unannotated' \
                        or re.search(r"NO_CATEGORY", seen_names[full_name].category):
                    seen_names[full_name] = ann

                # If they disagree on specific annotation, alert user
                elif ann.category != 'unannotated' and not re.search(r"NO_CATEGORY", ann.category):
                    print("houston we have a problem:", full_name)
                    print(ann.category + ' ' + ann.origin, "|||",
                          seen_names[full_name].category + " " + seen_names[full_name].origin)

            # Check if seen annotation has a more complete method id (the string for return vals is the main diff)
            if len(seen_names[full_name].returns) < len(ann.returns):
                seen_names[full_name].returns = ann.returns

    return new_list


if __name__ == "__main__":
    output_filename = 'lissa_annotations.csv'
    parse = parse_args()

    annotations = get_annotations(parse.dsafe, parse.susi, [parse.perm_map])

    # Remove "_INFORMATION" from the end of annotations. Seems to needlessly split categories. Maybe rethink this later
    for ann in annotations:
        ann.category = re.sub(r"_INFORMATION", "", ann.category)

    annotations = resolve_dups(annotations)
    counts = get_annotation_stats(annotations)
    print_stats(counts)

    save_annotations(annotations, output_filename)

