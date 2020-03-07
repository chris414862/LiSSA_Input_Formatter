import re


'''
These functions are responsible for parsing the input files and ensuring that formatting is uniform for LiSSA 
annotations regardless of the source of the original annotation.
'''

def parse_dsafe_ann_line(line: list, source_or_sink: str = ""):
    '''
    Parses one line from the DroidSafe annotations for the relevent fields needed for the lissa_annotation class.
    Representative example:
    void android.content.ContentProviderResult.writeToParcel(Parcel,int) - @DSSink({DSSinkKind.SENSITIVE_UNCATEGORIZED}\
    )-@DSGenerator(tool_name="Doppelganger",tool_version="2.0",generated_on="2013-12-30 12:34:37.021 -0500",hash_origin\
    al_method="9CD6B2E6D05DCE725086FF1495B545F8",hash_generated_method="CE8FF229D3F429077C3F103CC7EC30FE")

    :param line:
    :param source_or_sink: included for compatibility with get_anns's parse_func parameter
    :return:
    '''

    ret_dict = {}

    # Each DroidSafe annotation starts with "@"
    pieces = line.split("@")

    # We don't consider native (c/c++) Android methods (This doesn't catch all of them though I think)
    if re.match("native", pieces[0]):
        return ret_dict

    # Parse the method information
    meth_info = pieces[0].split()
    method_name_raw_toks = re.split(r"[()]", meth_info[1])
    ret_dict["meth_name"] = method_name_raw_toks[0]
    ret_dict["meth_params"] = [re.sub(r"final", "", p) for p in method_name_raw_toks[1].split(",")]
    ret_dict["ret_type"] = meth_info[0]

    # Parse the annotation information
    ret_dict['source_or_sink'] = 'none'
    ret_dict['category'] = "NO_CATEGORY"
    if len(pieces) > 1:
        for ann in pieces[1:]:
                if re.match("DSSource", ann):
                    ret_dict['source_or_sink'] = "source"
                    ret_dict['category'] = re.sub(r".*DSSourceKind\.([^}]*).*", r"\1", ann).strip()

                if re.match("DSSink", ann):
                    ret_dict['source_or_sink'] = 'sink'
                    ret_dict['category'] = re.sub(r".*DSSinkKind\.([^}]*).*", r"\1", ann).strip()

    return ret_dict


def parse_susi_ann_line(line, source_or_sink=""):
    '''
    Parses one line from the SuSi annotations for the relevent fields needed for the lissa_annotation class.
    Representative example line: <com.android.server.WifiService: int getFrequencyBand()> (NETWORK_INFORMATION)

    :param line:
    :param source_or_sink:
    :return:
    '''
    ret_dict = {}

    # Some lines are only headers for categories. We ignore these since header info is redundant
    if re.match("<", line) is None:
        return ret_dict

    meth_info, ann = line[1:].split("> ")
    (class_name, ret_dict["ret_type"], meth_name, *excess) = meth_info.split()
    meth_name, params, *excess = re.split(r"[\(\)]", meth_name)
    ret_dict['meth_name'] = class_name.strip(":") + "." + meth_name
    ret_dict["meth_params"] = params.split(",")
    ret_dict['source_or_sink'] = source_or_sink
    ann_toks = ann.split()
    ret_dict["category"] = ann_toks[-1].strip(" ()")
    return ret_dict


def parse_perm_map_line(csv_row, **kwargs):
    '''
    Parses one row from the permission mappings csv file. Method info is extracted, but there are assumed to be no annotations
    when parsed.
    Representative example csv row: ['void android.accounts.AccountManager.clearPassword(Account)', 'MANAGE_ACCOUNTS']

    :param csv_row:
    :param kwargs:
    :return:
    '''
    ret_dict = {}

    # We don't care about the actual mapped permission for this
    method_info, *_ = csv_row

    ret_dict["ret_type"], *rest = method_info.split()
    ret_dict["meth_name"], *rest = "".join(rest).split("(")
    ret_dict["meth_params"] = [param.strip(")") for param in "".join(rest).split(",")]
    ret_dict["source_or_sink"] = "unannotated"
    ret_dict['category'] = "unannotated"

    return ret_dict