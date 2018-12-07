import os, time, json, sys
import urllib3
import re
import pandas as pd
from datetime import datetime
import Product_Crawler.project_settings as settings
from Product_Crawler.project_settings import DEFAULT_TIME_FORMAT


def get_time_str(time=datetime.now(), fmt=DEFAULT_TIME_FORMAT):
    try:
        return time.strftime(fmt)
    except:
        return ""


def get_time_obj(time_str, fmt=DEFAULT_TIME_FORMAT):
    try:
        return datetime.strptime(time_str, fmt)
    except:
        return None


def transform_time_fmt(time_str, src_fmt, dst_fmt=DEFAULT_TIME_FORMAT):
    time_obj = get_time_obj(time_str, src_fmt)
    time_str = get_time_str(time_obj, dst_fmt)
    return time_str


def convert_unix_time(float_unix_time, dst_fmt=DEFAULT_TIME_FORMAT):
    try:
        return get_time_str(datetime.utcfromtimestamp(float_unix_time), fmt=dst_fmt)
    except:
        return ""


def mkdirs(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def load_json(path):
    data = []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        print("Load csv data (size = {}) to {} done".format(len(data), os.path.abspath(path)))
    except:
        print("Error when load csv data (size = {}) from P{".format(os.path.abspath(path)))

    return data


def save_json(data, path):
    dir = path[:path.rfind("/")]
    mkdirs(dir)

    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False)
    print("Save json data (size = {}) to {} done".format(len(data), os.path.abspath(path)))


def load_csv(path, **kwargs):
    try:
        df = pd.read_csv(path, **kwargs)
        print("Load csv data (size = {}) to {} done".format(df.shape[0], os.path.abspath(path)))
    except:
        print("Error when load csv from ", os.path.abspath(path))
        raise
    return df


def save_csv(df, path, fields=None):
    dir = path[:path.rfind("/")]
    mkdirs(dir)
    if fields is None or len(fields) == 0:
        columns = df.columns
    else:
        columns = fields
    df.to_csv(path, index=False, columns=columns)
    print("Save csv data (size = {}) to {} done".format(df.shape[0], os.path.abspath(path)))


def load_list(path):
    data = []
    try:
        with open(path, 'r') as f:
            data = f.readlines()
        data = [e.strip() for e in data]
    except:
        print("Error when load list from ", os.path.abspath(path))

    return data


def save_list(data, path):
    dir = path[:path.rfind("/")]
    mkdirs(dir)

    with open(path, 'w') as f:
        f.write("\n".join(data))
    print("Save list data (size = {}) to {} done".format(len(data), os.path.abspath(path)))


def save_str(data, path):
    dir = path[:path.rfind("/")]
    mkdirs(dir)

    with open(path, 'w') as f:
        f.write(data)
    print("Save str data to {} done".format(len(data), os.path.abspath(path)))


def is_valid_url(url):
    parsed_url = urllib3.util.parse_url(url)
    return bool(parsed_url.scheme)


def get_crawl_limit_setting(domain):
    crawl_limit = settings.CRAWL_LIMIT
    default = crawl_limit.get("default_crawl_limit")
    limit = crawl_limit.get(domain, 5) if default is None else default
    if limit < 0:
        limit = sys.maxsize

    return limit


# def get_export_fields_setting():
#     return settings.EXPORT_FIELDS


def get_export_format_setting():
    return settings.EXPORT_FORMAT


def remove_duplicate_whitespaces(str):
    return re.sub("\s+", " ", str)


def concatnate_dfs(paths):
    dfs = [load_csv(path) for path in paths]
    result = pd.concat(dfs, ignore_index=True)

    return result


def sleep(time_sleep=2):
    print("Sleep ...")
    time.sleep(time_sleep)
