import re

import requests

from bs4 import BeautifulSoup


DESCRIPTIONS = {1: "in a sexy outfit",
                2: "in lingerie",
                3: "in see-through clothing",
                4: "top and/or bottomless",
                5: "fully nude"}  # Interpretations based on what the image names say


class Appearance:

    def __init__(self, app_id, ng_url=None, soup=None):
        self.app_id = app_id

        if not soup:
            self.ng_url = ng_url
            r = requests.get(ng_url)
            soup = BeautifulSoup(r.text, "html.parser")

        self.name = soup.select_one("div#CelebName").text[:-5].strip()

        app = soup.select_one("div.Link a[id='{}']".format(app_id))
        self.source, self.date, self.age, self.nudity = \
            self.parse_appearance(app.find_parent("div", class_="Appearance"))

        self.nudity_str = DESCRIPTIONS[self.nudity]

    def __str__(self):
        return "{} in {} ({})".format(self.nudity_str.capitalize(), self.source, self.date)

    @staticmethod
    def parse_appearance(appearance_soup):
        soup = appearance_soup

        date = soup.find("div", class_="Date").text.strip()

        age = re.match(r"\(.*\)", soup.select_one(".Age").text.strip())[0][1:-1]
        age = age.replace(" ", "")

        source = soup.select_one(".Link")
        try:
            source.find(class_="NewAppearance").extract()
        except AttributeError:
            pass
        source = source.text.strip()

        nudity = int(soup.select_one("div.Nudity").img["src"][8])

        return source, date, age, nudity


class Celeb:

    @staticmethod
    def __ng_search(search):
        """"""
        r = requests.post("https://www.nudography.com/Search.aspx", data={"ctl00_txtSearch": search})
        soup = BeautifulSoup(r.text, "html.parser")

        found = False

        for link in soup.select_one("div#MainContent").find_all("a"):
            if search.lower() in link.text.lower():
                return "https://www.nudography.com" + link["href"]
            else:
                found = True
                continue

        if not found:
            print('Search returned no results: {}'.format(search))
            return None

    @staticmethod
    def nude_ratings(soup):
        """"""
        appearances = soup.select("div.Appearance")
        if not appearances:
            return None

        for appearance in appearances:
            app_id = appearance.find("div", class_="Link").a["id"]
            yield Appearance(soup=soup, app_id=app_id)

    def __init__(self, ng_url=None, search=None):
        """"""
        if search:
            self.ng_url = self.__ng_search(search)
            if not self.ng_url:
                raise AttributeError
        else:
            self.ng_url = ng_url

        soup = BeautifulSoup(requests.get(self.ng_url).text, "html.parser")
        self.name = soup.select_one("div#CelebName").text[:-5].strip()

        if not soup.find(id="Appearances"):
            raise ValueError("{} has no appearances!".format(self.name))

        self.apps = [x for x in self.nude_ratings(soup)]
        self.max_nudity = max([app.nudity for app in self.apps])
