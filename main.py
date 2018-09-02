import requests, datetime, webbrowser
import lxml.etree as etree
from concurrent import futures as cf

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

###### Enter gmail and password for email notifications ######
email = ''
password = ''
##############################################################

session = requests.session()
session.headers.update({'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
links = [line.rstrip('\n') for line in open('links.txt', 'r')]
inStock = []
pushNotification = False

def getDatetime():
    return '[{}]'.format(str(datetime.datetime.now())[:-3])

def sendEmail(link):
    try:
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = 'Product in stock alert!'
        message = link
        msg.attach(MIMEText(message))

        mailserver = smtplib.SMTP('smtp.gmail.com', 587)
        # identify ourselves to smtp gmail client
        mailserver.ehlo()
        # secure our email with tls encryption
        mailserver.starttls()
        # re-identify ourselves as an encrypted connection
        mailserver.ehlo()
        mailserver.login(email, password)

        mailserver.sendmail(email, email, msg.as_string())

        mailserver.quit()
    except Exception as e:
        print(getDatetime(), e)

def monitor(link):
    try:
        with session as s:
            r = s.get(link, timeout=10)
            r.raise_for_status()

            tree = etree.HTML(r.content)
            if 'walmart' in link:
                oos = False if 'Add' in tree.xpath('/html/body/div[1]/div/div[1]/div/div[2]/div/div/div[4]/div[4]/div[2]/div[1]/div/div/div/div[10]/div/div/button/text()')[0] \
                    else True
            elif 'gamestop' in link:
                oos = False if tree.xpath('//div[@class="button qq"]') else True
            elif 'bestbuy' in link:
                oos = True if 'Sold' in tree.xpath('//*[@id="priceblock-wrapper"]/div[2]/script/text()')[0] else False
            elif 'target' in link:
                oos = False if tree.xpath('//button[@data-test="addToCartBtn"]') else True
            elif 'bhphoto' in link:
                oos = True if tree.xpath('//a[@data-selenium="showNotifyMeLink"]') else False

            if oos and link in inStock:
                inStock.remove(link)
            elif not oos and link not in inStock:
                inStock.append(link)
                if pushNotification:
                    print(getDatetime(), 'In Stock: {}'.format(link))
                    webbrowser.open(link)
                    if email and password:
                        sendEmail(link)
    except Exception as e:
        print(getDatetime(), e)

if __name__ == '__main__':
    print(getDatetime(), 'Starting initial scanning.')
    with cf.ThreadPoolExecutor(len(links)) as pool:
        pool.map(monitor, links)
    print(getDatetime(), 'Finished initial scanning.')

    while True:
        pushNotification = True
        with cf.ThreadPoolExecutor(len(links)) as pool:
            pool.map(monitor, links)
