from Product_Crawler import utils
from lxml import html
import requests, os
import pandas as pd
import chardet


def crawl_latest_proxies():
    url = "https://free-proxy-list.net"
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





if __name__ == "__main__":
    pass
    # crawl()
