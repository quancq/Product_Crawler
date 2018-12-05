# from Product_Crawler import utils
from lxml import html
import requests
import os
import pandas as pd
import random


def mkdirs(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def save_csv(df, path, fields=None):
    dir = path[:path.rfind("/")]
    mkdirs(dir)
    if fields is None or len(fields) == 0:
        columns = df.columns
    else:
        columns = fields
    df.to_csv(path, index=False, columns=columns)
    print("Save csv data (size = {}) to {} done".format(df.shape[0], path))


def load_list(path):
    data = []
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = f.readlines()
            data = [e.strip() for e in data]
    except:
        print("Error when load list from ", path)

    return data


def save_list(data, path, mode="w"):
    dir = path[:path.rfind("/")]
    mkdirs(dir)

    if mode == "a":
        archive_data = load_list(path)
        data.extend(archive_data)

    with open(path, 'w') as f:
        f.write("\n".join(data))
    print("Save list data (size = {}) to {} done".format(len(data), path))


def crawl_latest_proxies():
    # url = "https://free-proxy-list.net"
    url = "https://www.sslproxies.org/"
    root = html.document_fromstring(requests.get(url).content)

    th_elms = root.cssselect("table#proxylisttable thead tr th")
    columns = [th.text for th in th_elms]
    print(columns)

    data = []

    tr_elms = root.cssselect("table#proxylisttable tbody tr")
    for tr in tr_elms:
        data.append([td.text for td in tr.cssselect("td")])

    print("Crawl {} proxies from {} done".format(len(data), url))
    return pd.DataFrame(data, columns=columns)


def get_proxy_urls(df):
    proxies = []
    for idx, row in df.iterrows():
        scheme = "https" if row["Https"] == "yes" else "http"
        url = "{}://{}:{}".format(scheme, row["IP Address"], row["Port"])
        proxies.append(url)

    return proxies


def crawl():
    proxies = crawl_latest_proxies()

    proxy_dir = "./Proxy"
    proxy_txt_path = os.path.join(proxy_dir, "proxy_list.txt")
    proxy_csv_path = os.path.join(proxy_dir, "proxies.csv")
    utils.mkdirs(proxy_dir)

    # proxies.to_csv(os.path.join(proxy_dir, "proxies.csv"), index=False)
    utils.save_csv(proxies, proxy_csv_path)

    proxy_urls = get_proxy_urls(proxies)

    # Union crawled proxies with archive proxies
    archive_proxies = utils.load_list(proxy_txt_path)
    # print("archive: ", archive_proxies)
    all_proxies = archive_proxies

    for proxy_url in proxy_urls:
        if proxy_url not in all_proxies:
            all_proxies.append(proxy_url)

    utils.save_list(all_proxies, path=proxy_txt_path)
    print(proxies.head())

    # print("\n".join(proxy_urls[:10]))


class ProxyManager:
    def __init__(self, proxies_path="./Proxy/proxy_list.txt", proxy_type="https"):
        self.proxies_path = proxies_path
        self.proxies = []
        self.update_latest_proxies(proxy_type)

    @staticmethod
    def crawl_latest_proxies(proxy_type="https"):
        if proxy_type == "https":
            url = "https://www.sslproxies.org/"
        else:
            url = "https://free-proxy-list.net"
        root = html.document_fromstring(requests.get(url).content)

        th_elms = root.cssselect("table#proxylisttable thead tr th")
        columns = [th.text for th in th_elms]
        # print(columns)

        data = []
        tr_elms = root.cssselect("table#proxylisttable tbody tr")
        for tr in tr_elms:
            data.append([td.text for td in tr.cssselect("td")])

        df = pd.DataFrame(data, columns=columns)
        is_https_proxy = "yes" if proxy_type == "https" else "no"
        df = df[df["Https"] == is_https_proxy]

        print("Crawl {} proxies from {} done".format(df.shape[0], url))
        return df

    @staticmethod
    def _extract_proxy_urls(proxy_df):
        proxies = []
        for idx, row in proxy_df.iterrows():
            scheme = "https" if row["Https"] == "yes" else "http"
            url = "{}://{}:{}".format(scheme, row["IP Address"], row["Port"])
            proxies.append(url)

        return proxies

    def load_proxies(self, proxies_path="./Proxy/proxy_list.txt"):
        self.proxies = load_list(proxies_path)

    def save_proxies(self, proxies_path="./Proxy/proxy_list.txt"):
        save_list(self.proxies, proxies_path)

    def update_latest_proxies(self, proxy_type="https"):
        proxy_df = ProxyManager.crawl_latest_proxies(proxy_type=proxy_type)
        self.proxies = ProxyManager._extract_proxy_urls(proxy_df)

        print("Update latest proxies done. Number proxies : ", len(self.proxies))

    def generate_proxy_with_scheme(self):
        for proxy in self.proxies:
            if proxy.startswith("https"):
                scheme = "https"
            else:
                scheme = "http"

            yield {scheme: proxy}

    def get_response(self, url):
        random.shuffle(self.proxies)

        for proxy in self.generate_proxy_with_scheme():



if __name__ == "__main__":
    pass
    # crawl()
