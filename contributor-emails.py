import json
import pandas as pd
from requests import get
from contextlib import closing
from bs4 import BeautifulSoup as BS

SOURCE = 'LIST_OF_YOUR_REPOS_URLS.xlsx'
OUTPUT = 'emails.xlsx'

HEADERS = {
    'authorization': 'Basic ',
    'content-type': 'application/json',
    'x-github-otp': '',
}

COOKIES = {
        # Add your session cookies here (can be found in developer console -> Storage -> Cookies)
}

#making the correct request for BeautifulSoup
def simple_get(url):
    with closing(get(url, cookies = COOKIES, stream = True)) as resp:
        if valid(resp):
            return resp.content
        else:
            return None

def valid(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
           and content_type is not None
           and content_type.find('html') > -1)

#extract bio from a webpage with BeautifulSoup
def get_bio(url):
    bio = []
    
    try:
        soup = BS(simple_get(url), 'html.parser')
            
        if soup.findAll("span",{"class":"vcard-fullname"})[0].contents:
            name = soup.findAll("span",{"class":"vcard-fullname"})[0].contents
        else: name = 'NA'
            
        if soup.findAll("a", {"class": "u-email"}):
            email = soup.findAll("a", {"class": "u-email"})[0].contents
        else: email = 'NA'
            
        if soup.findAll("li",{"itemprop":"url"}):
            website = soup.findAll("li",{"itemprop":"url"})[0].findAll("a", {"rel":"nofollow"})[0].contents
        else: website = 'NA'
        
        if soup.findAll("li",{"itemprop":"homeLocation"}):
            location = soup.findAll("li",{"itemprop":"homeLocation"})[0].findAll("span", {"class":"p-label"})[0].contents
        else: location = 'NA'
        
        bio = [name,email,website,location]
        
    except: bio = ['Failed to load page','Failed to load page','Failed to load page','Failed to load page']
        
    return bio
#get data from a row in a projects table
def get_meta(row):
    project = row[2]
    url = row[3]
    runs = row[5]
    meta = [project, url, runs]
    return meta

#read projects list urls from file
def projects_list(source):
    with open(source) as f:
        pr = f.readlines()
        pr = [x.strip() for x in pr] 
    return pr

# dumping extracted data into a DataFrame structure (read pandas docs, if you'd want to learn more)
contacts_list = pd.DataFrame(columns=['project','profile','name','email','website','location'])

projects = pd.read_excel(SOURCE, 'Sheet1', header = 0)
for row in projects.itertuples():
    meta = get_meta(row)
    for run_number in range(0,meta[2]):
        url = meta[1] + '?anno=1&page={}&per_page=100'.format(run_number+1)
        #print(url)
        contributors = get(url, headers = HEADERS)
        #print(contributors)
        for contributor in contributors.json():
            contacts = []
            contacts.append(meta[0]) #add project name
            profile_url = contributor['html_url']
            contacts.append(profile_url) #add profile url
            bio = get_bio(profile_url) # get the rest bio
            for field in bio:
                contacts.append(field[0])
            contacts = pd.DataFrame(data = [contacts], columns = ['project','profile','name','email','website','location'])
            contacts_list = contacts_list.append(contacts)
        contacts_list.drop_duplicates()
        try: contacts_list.to_excel(OUTPUT)
        except: contacts_list.to_csv(OUTPUT)
       
print('It is done!')