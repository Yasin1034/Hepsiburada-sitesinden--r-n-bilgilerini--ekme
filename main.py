from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import sqlite3

db_name = "deneme.sqlite"

if os.path.exists(db_name):
    os.remove(db_name)
    conn = sqlite3.connect(db_name)
else:
    conn = sqlite3.connect(db_name)

bag = conn.cursor()
query = """
        CREATE TABLE IF NOT EXISTS utuler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        urun_adi TEXT NOT NULL,
        marka TEXT NOT NULL,
        fiyat INTEGER NOT NULL,
        link TEXT NOT NULL,
        urun_ozellikleri TEXT NOT NULL
        )
        """
bag.execute(query)

bag = conn.cursor()
query = """
        CREATE TABLE IF NOT EXISTS yorumlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        urun_id INTEGER NOT NULL,
        satici_firma TEXT NOT NULL,
        star INTEGER NOT NULL,
        tarih DATE NOT NULL,
        yorum TEXT,
        FOREIGN KEY (urun_id) REFERENCES utuler (id)
        )
        """
bag.execute(query)

#selenium kullanarak chrome tarayıcısıyla siteyi açıyoruz
driver = webdriver.Chrome()
sayfalar = [f"https://www.hepsiburada.com/utuler-c-155122?siralama=degerlendirmepuani&sayfa={i}" for i in range(1,11)]
# ürünlerin bulundukları sayfaların hepsini bir liste şeklinde alıyoruz
print(sayfalar)

urun_linkleri= []
#her ürünün etiketi bu listeye eklenir
for i in sayfalar:
    # her sayfa içerisinde tek gezerek ürünlerin linklerini alacağız
    driver.get(i)

    # ürünlerin bulunduğu kutuyu sayfa içinde bulup içerisindeki ürün divlerini (li etiketi) buluyoruz
    content = driver.find_element(By.CLASS_NAME, "productListContent-rEYj2_8SETJUeqNhyzSm")
    urunler = content.find_elements(By.TAG_NAME, "li")

    for li in urunler:
        # her ürüne içerisinde a etiketini bularak linkleri çekiyoruz
        try:
            a = li.find_element(By.TAG_NAME, "a")
            link = a.get_attribute("href")
            #print(link)
            urun_linkleri.append(link)
        except:
            pass
        # her sayfada linkleri toplayıp urun linkleri listesine ekliyoruz

for i in urun_linkleri:
    print(i)


urun_bilgileri = []
urun_yorum = []
for urun_id,i in enumerate(urun_linkleri):
    driver.get(i)
    try:

        urun_adi = driver.find_element(By.XPATH, "//*[@id=\"product-name\"]").text
        marka = urun_adi.split(" ")[0]
        fiyati = driver.find_element(By.XPATH,"//*[@id=\"offering-price\"]/span[1]").text
        ozellikleri = driver.find_element(By.XPATH,"/html/body/div[2]/main/div[3]/section[1]/div[3]/div/div[1]/div[1]/div[3]/div[1]/ul" ).text
        #print(urun_adi,fiyati,marka,ozellikleri)
        urun_bilgileri.append([urun_adi,fiyati,marka,ozellikleri])
        urun_yorum.append([urun_adi,fiyati,marka,ozellikleri])
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        query = """
        INSERT INTO utuler 
        (urun_adi, marka, fiyat, link, urun_ozellikleri)
        VALUES (?,?,?,?,?)
        """
        degerler = (urun_adi, marka, fiyati, i, ozellikleri)

        cur.execute(query,degerler)
        con.commit()
        yorum_linki = str(i)+"-yorumlari"
        yorum_sayfalari = None

        try:

            driver.get(yorum_linki)
            driver.implicitly_wait(1)#bekleme süresi ekle internet kötü

            yorum_sayfa_barı = driver.find_element(By.CLASS_NAME, "paginationBarHolder")
            yorum_sayfa_listesi= yorum_sayfa_barı.find_element(By.TAG_NAME, "ul")
            yorum_sayfa_sayisi= yorum_sayfa_listesi.find_elements(By.TAG_NAME, "li")[-1].text

            yorum_sayfalari = [str(yorum_linki) + str("?sayfa=") + str(k) for k in range(1, int(yorum_sayfa_sayisi)+1)]

        except:
            yorum_sayfalari = [str(yorum_linki) + str("?sayfa=1")]
            print("hata1")

        sayac = 0
        yorumlar = []

        for ys in yorum_sayfalari:
            driver.get(ys)

            driver.implicitly_wait(2)

            div_content = driver.find_element(By.XPATH, "//*[@id=\"hermes-voltran-comments\"]/div[6]/div[3]/div")
            yorum_divs = div_content.find_elements(By.CLASS_NAME, "hermes-ReviewCard-module-dY_oaYMIo0DJcUiSeaVW")

            for yd in yorum_divs:

                try:
                    star = len(yd.find_element(By.CLASS_NAME,"hermes-RatingPointer-module-UefD0t2XvgGWsKdLkNoX").find_elements(By.CLASS_NAME, "star"))
                    tarih = yd.find_element(By.CLASS_NAME, "hermes-ReviewCard-module-ba888_vGEW2e_XKxTgdA").text
                    div = yd.find_element(By.CLASS_NAME,"hermes-ReviewCard-module-KaU17BbDowCWcTZ9zzxw")

                    try:
                        sayac += 1
                        yorum = div.find_element(By.TAG_NAME, "span").text
                    except:
                        yorum = "yorum yok"

                    satici_firma = yd.find_element(By.CLASS_NAME,"hermes-ReviewCard-module-_yfz1l8ZrCQDTEOSHbzQ").text

                    yorum_info = [star, tarih, yorum, satici_firma]
                    print(yorum_info)

                    yorumlar.append(yorum_info)

                    con = sqlite3.connect(db_name)
                    cur = con.cursor()
                    query = """
                            INSERT INTO yorumlar 
                            (urun_id, satici_firma, star, tarih, yorum)
                            VALUES (?,?,?,?,?)
                            """
                    degerler = (urun_id+1, satici_firma, star, tarih.split("\n")[0], yorum)

                    cur.execute(query, degerler)
                    con.commit()

                except:
                    print("hata 2")#hata aldığımız kısımları görebilmek için ekrana hata yazdırdık
            if sayac >= 100:
                break

        urun_yorum.append(yorumlar)


    except:
        print("hata son")
        #hata aldığımız kısımları görebilmek için ekrana hata yazdırdık
for i in urun_yorum:
    print(i)

