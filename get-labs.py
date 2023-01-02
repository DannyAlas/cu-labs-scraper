"""
College labs page -> [email, ~phone, ~address, website, ~faculty, blurb]

TODO: tidy up code, add commentsc and error handling
- fix subdomain.colorado.edu links navbar scraping
- add phone number scraping
- add address scraping
- add faculty scraping
"""

import requests # NOTE get object should be closed to avioud multi connection server errors
from bs4 import BeautifulSoup
import re
import uuid
import pandas as pd
from tqdm import tqdm

# a list of words to avoid when guessing lab names
AVOID = ["www", "org", "colorado", "edu", "mcdb", "research", "labs", "lab", "com", "https", "https:", "http", "http:", "mcdbiology"]
dict_href_links = {}

def getdata(url):
    return requests.get(url).text

def get_links(html_data, site_link):
    """returns a list of links on a webpage"""
    soup = BeautifulSoup(html_data, "html.parser")
    lab_dict = []
    for link in soup.find_all("a", href=True):
        
        # Append to list if new link contains original link
        if str(link["href"]).startswith((str(site_link))):
            lab_dict.append(link["href"])
            
        # Include all href that do not start with website link but with "/"
        if str(link["href"]).startswith("/"):
            if link["href"] not in dict_href_links:
                dict_href_links[link["href"]] = None
                link_with_www = site_link + link["href"][1:]
                lab_dict.append(link_with_www)
    return {"site": site_link, "subpages" : lab_dict}

def guess_lab_name(labs: dict):
    uniques = []
    for lab in labs:
        # append unique link attributes to a list
        if labs[lab]["lab"] == "UNNAMED":
            url = labs[lab]["link"]
            text = url.split(".")
            text = [x.split("/") for x in text]
            text = [item for sublist in text for item in sublist]
            for item in text:
                if item not in uniques and item not in AVOID and item != "":
                    uniques.append(item)
            # check if the url contains a unique attribute
            matches = []
            for item in text:
                if item in uniques:
                    matches.append(item)
            # if there is only one unique attribute, assign it to the lab
            if len(matches) == 1:
                labs[lab]["lab"] = matches[0]
                uniques.remove(matches[0])
            # if there are multiple unique attributes, join them and assign it to the lab
            else:
                for item in matches:
                    # if the item is a word with no unique characters, assign it to the lab
                    if item in re.findall(r"^[a-zA-Z]+$", item):
                        labs[lab]["lab"] = item
                        uniques.remove(item)
                        break
                    # else just assign all the unique attributes to the lab seperated by "-"
                    else:
                        labs[lab]["lab"] = "-".join(matches)
                        uniques.remove(item)
                for item in matches:
                    try:
                        uniques.remove(item)
                    except Exception: pass

            
    for lab in labs:
        # append unique link attributes to a list
        if labs[lab]["lab"] == "UNNAMED":
            print("unable to guess name for: ", labs[lab]["link"])

def get_lab_desc(lab_name: str) -> str:
    url = f"https://www.google.com/search?&q=cu+boulder+{lab_name}+lab"
    req = requests.get(url)
    sor = BeautifulSoup(req.text, "html.parser")
    
    return sor.findAll("div",{"class":"BNeawe"})[2].text


def get_links(webpage, soup, search_navbar: bool = True):
    """returns a list of subpages on a webpage
    Parameters
    ----------
    webpage : str
        url of the webpage
    soup : str
        BeutifulSoup object of the webpage, created using BeautifulSoup(html_data, "html.parser")
    search_navbar : bool, optional
        whether to search for subpages in the navbar, by default True
    
    Returns
    -------
    list_links : list
        list of subpages on a webpage
    """

    list_links = [webpage]
    dict_href_links = {}
    
    for link in soup.find_all("a", href=True):
        
        # Append to list if new link contains original link
        if str(link["href"]).startswith((str(webpage))):
            list_links.append(link["href"])
            
        # Include all href that do not start with website link but with "/"
        if str(link["href"]).startswith("/"):
            if link["href"] not in dict_href_links:
                dict_href_links[link["href"]] = None
                link_with_www = webpage + link["href"][1:]
                list_links.append(link_with_www)
    
    if search_navbar:
        for link in soup.find_all("a", href=True):
            if str(link["href"]).startswith("/"):
                if link["href"] not in dict_href_links:
                    dict_href_links[link["href"]] = None
                    link_with_www = webpage + link["href"][1:]
                    list_links.append(link_with_www)
    
    return list_links

def emailExtractor(soup):
    """returns a list of emails on a webpage
    
    Parameters
    ----------
    soup : str
        BeutifulSoup object of the webpage, created using BeautifulSoup(html_data, "html.parser")
    
    Returns
    -------
    emailList : list
        list of emails on a webpage
    """
    emailList = []

    mailtos = soup.find_all('a')

    href_lst = []
    for i in mailtos:
        if i not in href_lst:
            try:
                href_lst.append(i['href'])
            except: pass

    for href in href_lst:
        if ':' in href:
            if href not in emailList and 'mailto' in href:
                emailList.append(href)
    
    return emailList

def get_inner(website_link):
    response = requests.get(website_link).text
    soup = BeautifulSoup(response, "html.parser")
    
    pattern = re.compile(r"^/[a-zA-Z]+/.*$", re.IGNORECASE)
    content = soup.find_all("div", {"class": "content-grid-item"})
    lab_dict = {}
    
    for div in content:
        links = div.find_all("a", href=True)
        for link in links:
            link_text = link.text if not link.text == "" else "UNNAMED"
            link_herf = link.get('href')
            ID = uuid.uuid4().int
            if pattern.match(str(link_herf)) and link_herf not in [x for x in [lab_dict[lab]['link'] for lab in lab_dict]]:
                lab_dict[ID] = {"lab": link_text, 'link': str("https://www.colorado.edu" + link_herf)}
            else:
                if link_herf not in [x for x in [lab_dict[lab]['link'] for lab in lab_dict]]:
                    lab_dict[ID] = {"lab": link_text, 'link': link_herf} 
    
    # guess the name of the lab if UNNAMED
    guess_lab_name(lab_dict)
    # double check for duplicates
    
    # FIX THIS MESS...
    #----------------------------
    # a list of all the links
    lab_links = [x for x in [lab_dict[lab]['link'] for lab in lab_dict]]
    # get a list of all lab links that appear more than once
    matching_lab_links = []
    for lab_link in lab_links:
        if lab_links.count(lab_link) > 1:
            matching_lab_links.append(lab_link)
    # get a list of all the lab UUIDs with matching links
    matching_labs = [lab for lab in lab_dict if lab_dict[lab]['link'] in matching_lab_links]
    # get the lab names for the matching labs
    names = [lab_dict[lab]['lab'] for lab in matching_labs]
    for name in names:
        # if there is an uppercase name use that as the lab name
        if bool(re.match(r'\w*[A-Z]\w*', name)):
            linkofthislab = lab_dict[matching_labs[names.index(name)]]['link']
            labstobechanges = [lab for lab in matching_labs if lab_dict[lab]['link'] == linkofthislab]
            for lab in labstobechanges:
                lab_dict[lab]['lab'] = name
    # delete duplicates
    for lab_name in [lab_dict[lab]['lab'] for lab in lab_dict]:
        if [lab_dict[lab]['lab'] for lab in lab_dict].count(lab_name) > 1:
            lab_dict.pop([lab for lab in lab_dict if lab_dict[lab]['lab'] == lab_name][0])
    #----------------------------

    # get the email of the lab
    for lab in tqdm(lab_dict, desc="Getting emails"):
        response = requests.get(lab_dict[lab]['link'])
        soup = BeautifulSoup(response.text, "html.parser")
        subpages = get_links(lab_dict[lab]['link'], soup)
        response.close()
        emails = []
        for subpage in subpages:
            response = requests.get(subpage)
            soup = BeautifulSoup(response.text, "html.parser")
            emails.extend(emailExtractor(soup))
            response.close()
        
        lab_dict[lab]['email'] = emails

    # get the description of the lab
    for lab in tqdm(lab_dict, desc="Getting descriptions"):
        lab_dict[lab]['desc'] = str(get_lab_desc(lab_dict[lab]['lab']))
    
    return lab_dict


if __name__ == "__main__":
        
    mcdb_labs = get_inner("URL HERE")

    pd.DataFrame.from_dict(mcdb_labs, orient="index").to_csv("labs.csv")