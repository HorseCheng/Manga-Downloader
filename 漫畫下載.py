import requests
import re
import time
from bs4 import BeautifulSoup
import base64
from collections import OrderedDict
import os
import pyaes
import js2py

web = {
    "一拳超人": "yiquanchaoren",
    "錢進球場": "qianjinqiuchang",
    "擅長捉弄人的原高木同學": "shanchangzhuonongrendeyuangaomutongxue",
    "擅長捉弄人的高木同學": "shanchangzhuonongdegaomutongxue",
    "進擊的巨人": "jinjidejuren",
    "搖曳露營": "yaoyeluying",
}


def downloader():
    print("即將下載漫畫名稱:", page)
    print("網址:", url)

    html = requests.get(url)

    ciphertext = (
        re.search("chapterImages = .*;var chapterPath", html.text)
        .group()
        .replace('chapterImages = "', "")
        .replace('";var chapterPath', "")
    )
    ciphertext = base64.b64decode(ciphertext)

    # find Secret Key and Initial Value
    x = re.search("/js/decrypt[0-9]+.js", html.text).group(0)
    s = requests.get("https://www.manhuabei.com" + x).text
    function = s

    ivEncrypted = re.findall("iv':(_.*?),", s)[0]  # _0x28ee89
    ivSearchKey1 = re.findall(
        "var " + ivEncrypted + ".*?\['parse'\].*?('.*?')\]\);", s
    )[0]  # 'VZoxi'
    ivSearchKey2 = re.findall(ivSearchKey1 + ".*?(_.*?)};", s)[0]  # _0x1632('0','vMr8')
    iv = js2py.eval_js(function + ivSearchKey2)  # A1B2C3DEF1G321o8

    secretkeyEncrypted = re.findall("chapterImages,(.*?),", s)[0]  # _0x572aa3
    secretkeySearchKey = re.findall("var " + secretkeyEncrypted + ".*?\((_.*?)\);", s)[0]  # _0x1632('4','s^a[')
    secretkey = js2py.eval_js(function + secretkeySearchKey)  # KA58ZAQ321oobbG8

    decrypter = pyaes.Decrypter(
        pyaes.AESModeOfOperationCBC(
            secretkey.encode(encoding="utf-8"), iv.encode(encoding="utf-8")
        )
    )
    decrypted = decrypter.feed(ciphertext)
    decrypted += decrypter.feed()
    output = (
        decrypted.decode("UTF-8")
        .replace("[", "")
        .replace("]", "")
        .replace('"', "")
        .replace("\\", "")
    )
    output = output.split(",")
    print("共", len(output), "頁")

    if not os.path.exists("漫畫/" + request + "/" + str(page)):
        os.makedirs("漫畫/" + request + "/" + str(page))
    for i in range(len(output)):
        with open("漫畫/" + request + "/" + str(page) + "/" + str(i) + ".jpg", "wb") as f:
            while True:
                try:
                    if "http" in output[i]:
                        output[i] = output[i].replace("%", "%25")
                        response = requests.get(
                            "http://img01.eshanyao.com/showImage.php?url=" + output[i],
                            stream=True,
                        )
                        for block in response.iter_content(1024):
                            if not block:
                                break
                            f.write(block)
                    else:
                        path = (
                            re.search('chapterPath = .*/";var chapterPrice', html.text)
                            .group()
                            .replace('chapterPath = "', "")
                            .replace('";var chapterPrice', "")
                        )
                        response = requests.get(
                            "http://img01.eshanyao.com/" + path + output[i], stream=True
                        )
                        for chunk in response.iter_content(1024):
                            if chunk:
                                f.write(chunk)
                    break
                except Exception as e:
                    print(e)
                    continue

        print("第", i, "頁下載完成")
    print("\n已完成下載", page)


if __name__ == "__main__":
    print("正在統整最新漫畫更新時間...\n")
    outputstr = {}
    savehtml = {}
    filterlen = {}
    sectionword = {}

    for i in web:
        html = requests.get("http://www.manhuabei.com/manhua/" + web[i] + "/")
        soup = BeautifulSoup(html.text, "lxml")

        try:
            timestamp = re.search("20[0-9\- ]+\:[0-9]+", html.text).group()
        except Exception as e:
            print(i, "讀取錯誤\n", e)

        filterlist = soup.find_all("div", {"class", "zj_list autoHeight"})
        savehtml[i] = filterlist
        filterlen[i] = len(filterlist)
        temp = i + "  最新更新時間: " + timestamp + "\n"
        chosen = {}
        for q in range(1, filterlen[i]):
            temp += "    " + filterlist[q].find("em").text.replace("列表", "").replace(
                "章节", "章節"
            ).replace("单行本", "單行本")
            temp += "  最新集數: " + filterlist[q].find_all("a")[-1]["title"] + "\n"
            sectionword[i] = sectionword.get(i, "") + (
                "    "
                + str(q)
                + ". "
                + filterlist[q]
                .find("em")
                .text.replace("列表", "")
                .replace("章节", "章節")
                .replace("单行本", "單行本")
            )
            sectionword[i] = sectionword[i] + (
                "  最新集數: " + filterlist[q].find_all("a")[-1]["title"] + "\n"
            )
        outputstr[temp] = timestamp

    check = "Y"
    while check == "Y" or check == "y":
        print("現在時間", time.strftime("%Y-%m-%d %H:%M", time.localtime()))

        orderlist = list(
            OrderedDict(sorted(outputstr.items(), key=lambda t: t[1], reverse=True))
        )
        for i in range(len(orderlist)):
            print("-----------\n{}: {}".format(i + 1, orderlist[i]), end="")

        section = 1
        num = int(input("\n請輸入下載漫畫的編號: "))

        for i in web:
            if str(i) in str(orderlist[num - 1]):
                request = i

        if filterlen[request] > 2:
            print(sectionword[request], end="")
            section = int(input("要下載哪一種類? "))

        page = input('要下載哪一回?\n 註: 下載最新集數請輸入 "latest"; 下載全部請輸入 "all"\n')

        y = savehtml[request][section].find_all("div", {"class", "zj_list_con"})
        chosen = {}
        for i in y:
            x = i.find_all("a", href=True)
            for z in x:
                chosen[z["title"]] = z["href"]
            latesturl = x[-1]["href"]
            latestname = x[-1]["title"]

        if page == "latest":
            page = latestname
            url = "http://www.manhuadui.com" + str(latesturl)
            downloader()
        elif page == "all":
            for i in chosen:
                page = i
                url = "http://www.manhuadui.com" + chosen[i]
                downloader()
        else:
            matchstring = []
            for i in chosen:
                if str(page) in i:
                    matchstring.append(i)

            page = matchstring[0]
            if len(matchstring) > 1:
                print("查詢到多個匹配項目")
                for i in range(len(matchstring)):
                    print('{}: "{}"\t'.format(i, matchstring[i].strip()), end="")
                    if (i + 1) % 5 == 0:
                        print()
                temp = int(input("\n請選擇要下載的檔案: "))
                page = matchstring[temp]
            url = "http://www.manhuadui.com" + chosen[page.strip()]
            downloader()
        check = input("\n是否繼續下載 (y/n): ")
    print("已結束程式...")
