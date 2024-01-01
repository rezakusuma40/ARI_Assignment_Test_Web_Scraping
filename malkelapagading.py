import requests
from bs4 import BeautifulSoup as bsoup
import pandas as pd

# this site use load more button instead of pagination for showing more elements
# by inspecting network tab, it turns out that it can be scraped by adding page number in it's url

# count the number of page, 1 page for every 21 tenants
url='https://www.malkelapagading.com/directory'
response=requests.get(url)
soup=bsoup(response.text, 'html.parser')
total_tenant_tag=soup.find('h2', class_='blog-details-headline')
total_tenant=total_tenant_tag.find('span').text.replace('( ', '').replace(' )', '')
total_page=int(total_tenant)//21+2
tenant_dict_list=[] # a list of dictionaries for storing tenant data

for page in range (1,total_page):
    print(f'page-{page}') # for tracking webscraping progress
    paginated_url=url+'?page='+str(page)
    response=requests.get(paginated_url)
    paginated_soup=bsoup(response.text, 'html.parser')
    tenants_page_logo=paginated_soup.find_all('div', attrs={'class':'work-process-sub'})
    for tenant_page_logo in tenants_page_logo:
        tenant_dict={} # for storing tenant data, 1 dictionary for 1 tenant
        try:
            tenant_dict['tenant_page_url']=tenant_page_logo.find('a', attrs={'class':'highlight-button-dark'})['href']
        except:
            tenant_dict['tenant_page_url']=None
            continue
        try:
            tenant_dict['tenant_logo_url']=tenant_page_logo.find('img')['src']
        except:
            tenant_dict['tenant_logo_url']=None
        tenant_page_response=requests.get(tenant_dict['tenant_page_url'])
        tenant_page_soup=bsoup(tenant_page_response.text, 'html.parser')
        name_category=tenant_page_soup.find_all('li', class_='white-text')
        try:
            tenant_dict['category']=name_category[0].text.strip()
        except:
            tenant_dict['category']=None
        try:
            tenant_dict['subcategory']=name_category[1].text.strip()
        except:
            tenant_dict['subcategory']=None
        try:
            tenant_dict['tenant_name']=name_category[2].text.strip()
        except:
            tenant_dict['tenant_name']=None
        try:
            tenant_photo=tenant_page_soup.find('img', class_='img-rounded')
            if tenant_photo['alt']=='SMS-default-foto': # some tenants have no photo but they have common image for substitute
                tenant_dict['tenant_photo_url']=None
            else:
                tenant_dict['tenant_photo_url']=tenant_photo['src']
        except:
            tenant_dict['tenant_photo_url']=None
        try:
            detail_parent=tenant_page_soup.find('div', class_='col-md-5')
        except:
            detail_parent=None # this element contain the rest of the data
            continue # skip to next loop if not exists
        locations=detail_parent.find_all('div', class_='col-md-6')
        # some tenants have more than 1 locations
        tenant_dict['buildings']=[]
        tenant_dict['floors']=[]
        for location in locations:
            building_and_floor=location.find_all('p')
            try:
                building=building_and_floor[0].text.strip()
            except:
                building=''
            try:
                floor=building_and_floor[1].text.strip()
            except:
                floor=''
            tenant_dict['buildings'].append(building)
            tenant_dict['floors'].append(floor)
        if (tenant_dict['buildings']==[]):
            tenant_dict['buildings']=None
        if (tenant_dict['floors']==[]):
            tenant_dict['floors']=None
        product_tag=detail_parent.find('p', text='product')
        try:
            tenant_dict['products']=product_tag.find_next_sibling().text.strip()
        except:
            tenant_dict['products']=None
        where_to_park_tag=detail_parent.find('p', text='where to park')
        try:
            tenant_dict['where_to_park']=where_to_park_tag.find_next_sibling().text.strip()
        except:
            tenant_dict['where_to_park']=None
        if (tenant_dict['where_to_park']==''):
            tenant_dict['where_to_park']=None            
        try:
            pickup_point=detail_parent.find('b', text=' Pickup point').find_parent().text
            pickup_point_colon=pickup_point.find(':')
            tenant_dict['pickup_point_stripped']=pickup_point[pickup_point_colon+2:].strip()
        except:
            tenant_dict['pickup_point_stripped']=None
        if 'Takeaway' in detail_parent.get_text():
            tenant_dict['takeaway']='allowed'
        else: tenant_dict['takeaway']=None
        try:
            contact_phone=detail_parent.find('a', text='Contact Phone')['href']
            contact_phone_colon=contact_phone.find(':')
            tenant_dict['contact_phone_stripped']=contact_phone[contact_phone_colon+1:].strip()
        except:
            tenant_dict['contact_phone_stripped']=None
        if 'See Catalogue' in detail_parent.get_text():
            tenant_dict['catalogue']='available'
        else: tenant_dict['catalogue']=None
        if 'Chat Whatsapp' in detail_parent.get_text():
            tenant_dict['whatsapp_chat']='available'
        else: tenant_dict['whatsapp_chat']=None
        if 'Go Food' in detail_parent.get_text():
            tenant_dict['go_food']='available'
        else: tenant_dict['go_food']=None
        if 'Grab Food' in detail_parent.get_text():
            tenant_dict['grab_food']='available'
        else: tenant_dict['grab_food']=None
        if 'Shopee Food' in detail_parent.get_text():
            tenant_dict['shopee_food']='available'
        else: tenant_dict['shopee_food']=None
        for key, value in tenant_dict.items():
            print(f'{key}: {value}') # for tracking webscraping progress
        tenant_dict_list.append(tenant_dict)
# save all tenants data to a dataframe than save as csv
tenant_df=pd.DataFrame(tenant_dict_list)
tenant_df.to_csv('malkelapagading.csv', index=False)