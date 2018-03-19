import requests
from lxml import html
from bs4 import BeautifulSoup
import re
import datetime
from pymongo import MongoClient,errors
import telebot


client = MongoClient('mongodb://app:Cbvajybz1@ds117509.mlab.com:17509/heroku_b99pt4qd')
db=client.heroku_b99pt4qd
board=db.board

BOT_TOKEN = '585739860:AAESdPwdtYxUoxl4fjR8CPwW464ufaDzvFw'
CHANELL='@olxgrabernote'
bot = telebot.TeleBot(BOT_TOKEN)


def get_page(url):
    r=requests.get(url)
    tree = BeautifulSoup(r.text,'html.parser')
    return tree

def get_date(dt):
    months=['января','февраля','марта','апреля','мяйя','июня','июля','августа','сентября','октября','ноября','декабря']
    date_pattern=re.compile('\d{2}:\d{2},\s\d{1,2}\s.{4,20}\s\d{4}')
    month_pattern=re.compile('января|февраля|марта|апреля|мяйя|июня|июля|августа|сентября|октября|ноября|декабря')    
    date_math=date_pattern.search(dt)
    if date_math:
        date_str=date_math.group(0)
        month_math=month_pattern.search(date_str)
        if month_math:
            month_str=month_math.group(0)
            m_num=months.index(month_str)
            date_str=date_str.replace(month_str,str(m_num+1))
            try:
                return datetime.datetime.strptime(date_str,'%H:%M, %d %m %Y')
            except ValueError:
                return False
            
    else:
        return False
    
def get_details(item,details):
    owner_pattern=re.compile('Бизнес|Частного лица')
    digit_pattern=re.compile('[0-9]{1,2}')
    for detail in details.find_all('td',class_='value'):
        key=detail.parent.th.get_text()
        if key=='Объявление от':
            owner_math=owner_pattern.search(detail.strong.get_text())
            if owner_math:
                owner=owner_math.group(0)
                item['owner']='anency' if owner=='Бизнес' else 'private'
        elif key=='Площадь участка':
            sq_math=digit_pattern.search(detail.strong.get_text())
            if sq_math:
                item['squeue']=int(sq_math.group(0))
        return item

def get_data(n,main_url):
    items=[]
    page=get_page(main_url)
    for offer in page.find_all('td',class_='offer'):
        item={}
        try:
            item['price']=float(offer.find('p',class_='price').strong.get_text()[:-4].replace(' ',''))
            item['url']=offer.find('a',class_='marginright5 link linkWithHash detailsLink').get('href')
            item['_id']=offer.find('table').get('data-id')
            item_page=get_page(item['url'])
            title_box=item_page.find('div',class_='offer-titlebox')
            item['title']=title_box.h1.get_text()[1:].strip()
            date_str=title_box.find('div',class_='offer-titlebox__details').em.get_text()
            item['date']=get_date(date_str)
            details_box=item_page.find('table',class_='details fixed marginbott20 margintop5 full')
            item=get_details(item,details_box)
            text_box=item_page.find('div',{'id':'textContent'})
            item['text']=text_box.p.get_text()
            items.append(item)
        except AttributeError:
            continue
    return items

def format_message(data):
    return data['title']+'Price: '+str(data['price'])+' ... '+'<a href="'+data['url']+'">'+data['_id']+'</a>'

    
for i in range(1,5):
    items=get_data(1,'https://www.olx.ua/nedvizhimost/zemlya/prodazha-zemli/dnepr/?search%5Bfilter_float_price%3Ato%5D=70000&search%5Bdist%5D=10&page='+str(i))
    for i in items:
        try:
            board.insert_one(i)
            message=format_message(i)
            bot.send_message('@olxgrabernote',message,parse_mode='HTML')
        except errors.DuplicateKeyError:
            continue

