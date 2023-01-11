import requests  # NOTE get object should be closed to aviod multi connection server errors
from bs4 import BeautifulSoup, element
import re
import uuid

# a list of words to avoid when guessing lab names
AVOID = [
    "www",
    "org",
    "colorado",
    "edu",
    "mcdb",
    "research",
    "labs",
    "lab",
    "com",
    "https",
    "https:",
    "http",
    "http:",
    "mcdbiology",
    "sites",
    "faculty",
    "people",
]
# a list of social media names
SOCIAL = [
    "facebook",
    "twitter",
    "linkedin",
    "instagram",
    "youtube",
    "github",
    "pinterest",
    "reddit",
]


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
                    except Exception:
                        pass

    return labs


def get_lab_desc(lab_name: str) -> str:
    url = f"https://www.google.com/search?&q=cu+boulder+{lab_name}+lab"
    req = url
    sor = BeautifulSoup(req.text, "html.parser")

    return sor.findAll("div", {"class": "BNeawe"})[2].text


def get_links(
    webpage: str,
    soup: BeautifulSoup,
    recursion: int = 1,
    search_navbar: bool = True,
):
    """returns a list of subpages on a webpage

    Parameters
    ----------
    webpage : str
        url of the webpage
    soup : str
        BeutifulSoup object of the webpage, created using BeautifulSoup(html_data, "html.parser")
    search_navbar : bool, optional
        whether to search for subpages in the navbar, by default True
    nav_recursion : int, optional
        how many levels of recursion to search for subpages in the navbar, by default 1

    Returns
    -------
    list_links : list
        list of subpages on a webpage
    """
    # list of links in the colorado footer to avoid
    avoid = [
        "http://www.colorado.edu",
        "http://www.colorado.edu/about/privacy-statement",
        "http://www.colorado.edu/about/legal-trademarks",
        "http://www.colorado.edu/map",
        "https://www.colorado.edu/search",
        "https://calendar.colorado.edu",
        "https://www.colorado.edu/artsandsciences",
    ]
    list_links = [webpage]

    def is_webpage(link: str):
        """returns True if a link points to a webpage

        Parameters
        ----------
        link : str
            the link to check
        """

        # if a link is a full link, check if it is a subpage of the webpage
        if re.search("text/html", str(requests.get(link).headers["Content-Type"])):
            return True

    def add_link(
        links: element.ResultSet,
        links_list: list = list_links,
        avoid: list = avoid,
        only_sub_urls: bool = True,
    ):
        """adds links to list_links
        Parameters
        ----------
        links : bs4.element.ResultSet
            a list of links to check
        links_list : list, optional
            a list of links to add to, by default get_links.list_links
        avoid : list, optional
            a list of links to avoid, by default get_links.avoid
        only_sub_urls : bool, optional
            whether to search only links that are subpages of the webpage, by default True
            for example: if website = "https://lab.colorado.edu" and link = "https://youtube.com/video", if only_sub_urls = True, the link will be ignored
        """

        # since we're already looping through links, other useful data as well
        if only_sub_urls:
            # remove duplicates and links that are not subpages of the webpage and are not webpages and are in aviod
            links = [
                x
                for x in set(links)
                if x["href"] not in avoid
                and x["href"].startswith("http")
                and any([x for x in set(x["href"].split("/")).intersection(webpage.split("/")) if x not in ["https:", "http:", "", "/", "www", ":", ".com", ".edu", "www.colorado.edu", "colorado.edu"]])
                or x["href"].startswith("/")
            ]
        else:
            # remove duplicates and links that are not webpages and are in aviod
            links = [
                x
                for x in set(links)
                if x["href"] not in avoid
                and x["href"].startswith("http")
                or x["href"].startswith("/")
            ]

        for link in links:
            # if the link is a relative link, add the webpage to the beginning of the link
            full_link = (
                str(
                    webpage
                    + "/".join(
                        [
                            x
                            for x in link["href"].split("/")
                            if x not in webpage.split("/")
                        ]
                    )
                )
                if link["href"].startswith("/")
                else link["href"]
            )
            # if the link is novel, not to be avoided and is a subpage of the webpage, add it to the list of links
            if full_link not in list_links + avoid and is_webpage(full_link):
                list_links.append(full_link)

        return links_list

    # if search_navbar is true, recurse into those pages and extract the links
    if search_navbar:
        # Search for links in navbar
        navbar = soup.find("nav")
        list_links = []

        if navbar:
            # add navbar links to links to be searched
            list_links.extend(add_link(navbar.find_all("a", href=True)))
            print(f"Found {list_links} links in navbar")

    for x in range(recursion + 1):
        print(f"recursion {x}")
        # recurse through list_links and add to list_links, removing from nav links when srearched
        # remove duplicates
        list_links = list(set(list_links))
        for link in list_links:
            try:
                print(f"searching {link}")
                html_data = requests.get(link)
                soup = BeautifulSoup(html_data.text, "html.parser")
                links=soup.find_all("a", href=True)

                list_links.extend(add_link(links=links))
                html_data.close()
                list_links = list(set(list_links))
            except Exception as e:
                print(e)
                break

    print(f"list_links: \n{list_links}\n")
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

    mailtos = soup.find_all("a")

    href_lst = []
    for i in mailtos:
        if i not in href_lst:
            try:
                href_lst.append(i["href"])
            except:
                pass

    for href in href_lst:
        if ":" in href:
            if href not in emailList and "mailto" in href:
                emailList.append(str(href).split(":")[1])

    return emailList


def get_labs(soup: BeautifulSoup) -> dict:
    """returns a dictionary of labs on a webpage

    Parameters
    ----------
    soup : str
        BeutifulSoup object of the webpage, created using BeautifulSoup(html_data, "html.parser")

    Returns
    -------
    labs : dict
        dictionary of labs on a webpage
    """

    lab_dict = {}
    pattern = re.compile(r"^/[a-zA-Z]+/.*$", re.IGNORECASE)
    content = soup.find_all("div", {"class": "content-grid-item"})

    for div in content:
        links = div.find_all("a", href=True)
        for link in links:
            link_text = link.text if not link.text == "" else "UNNAMED"
            link_herf = link.get("href")
            ID = uuid.uuid4().int
            if pattern.match(str(link_herf)) and link_herf not in [
                x for x in [lab_dict[lab]["link"] for lab in lab_dict]
            ]:
                lab_dict[ID] = {
                    "lab": link_text,
                    "link": str("https://www.colorado.edu" + link_herf),
                }
            else:
                if link_herf not in [
                    x for x in [lab_dict[lab]["link"] for lab in lab_dict]
                ]:
                    lab_dict[ID] = {"lab": link_text, "link": link_herf}

    return lab_dict


def remove_duplicates(lab_dict: dict) -> dict:
    """removes duplicate labs from a dictionary of labs

    Parameters
    ----------
    lab_dict : dict
        dictionary of labs on a webpage

    Returns
    -------
    lab_dict : dict
        dictionary of labs on a webpage without duplicates
    """

    labs = [lab_dict[lab]["lab"] for lab in lab_dict]
    links = [lab_dict[lab]["link"] for lab in lab_dict]
    for i in range(len(labs)):
        if labs.count(labs[i]) > 1:
            if links.count(links[i]) > 1:
                lab_dict.pop(i)

    return lab_dict