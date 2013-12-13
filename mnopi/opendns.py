from lxml import html
import urllib2 #TODO: pensar si viene mejor el modulo Request+
from models import CategorizedDomain
from django.db import transaction

APPROVED_CATEGORIES_QUERY = "//td[text()=\"Approved\"]/parent::node()/td/b/text()"

CATEGORIES = { "Academic Fraud": "Academic Fraud",
               "Adult Themes": "Adult Themes",
               "Advertising": "Advertising",
               "Alcohol": "Alcohol",
               "Anime/Manga/Webcom...": "Anime/Manga/Webcomic",
               "Educational Instit...": "Educational Institutions",
               "Financial Institut...": "Financial Institutions",
               "Forums/Message boa...": "Forums/Message boards",
               "Hate/Discriminatio...": "Hate/Discrimination",
               "Software/Technolog...": "Software/Technology",
               "Visual Search Engi...": "Visual Search Engines",
               "Auctions": "Auctions",
               "Automotive": "Automotive",
               "Blogs": "Blogs",
               "Business Services": "Business Services",
               "Chat": "Chat",
               "Classifieds": "Classifieds",
               "Dating": "Dating",
               "Drugs": "Drugs",
               "Ecommerce/Shopping": "Ecommerce/Shopping",
               "File Storage": "File Storage",
               "Gambling": "Gambling",
               "Games": "Games",
               "Government": "Government",
               "Health and Fitness": "Health and Fitness",
               "Humor": "Humor",
               "Instant Messaging": "Instant Messaging",
               "Jobs/Employment": "Jobs/Employment",
               "Lingerie/Bikini": "Lingerie/Bikini",
               "Movies": "Movies",
               "Music": "Music",
               "News/Media": "News/Media",
               "Non-Profits": "Non-Profits",
               "Nudity": "Nudity",
               "P2P/File sharing": "P2P/File sharing",
               "Parked Domains": "Parked Domains",
               "Photo Sharing": "Photo Sharing",
               "Podcasts": "Podcasts",
               "Politics": "Politics",
               "Pornography": "Pornography",
               "Portals": "Portals",
               "Proxy/Anonymizer": "Proxy/Anonymizer",
               "Radio": "Radio",
               "Religious": "Religious",
               "Research/Reference": "Research/Reference",
               "Search Engines": "Search Engines",
               "Sexuality": "Sexuality",
               "Social Networking": "Social Networking",
               "Sports": "Sports",
               "Tasteless": "Tasteless",
               "Television": "Television",
               "Tobacco": "Tobacco",
               "Travel": "Travel",
               "Video Sharing": "Video Sharing",
               "Weapons": "Weapons",
               "Web Spam": "Web Spam",
               "Webmail": "Webmail" }


class OpenDNS_DOMException(Exception):
    """
    Exception that indicates that OpenDNS has changed its DOM (and hence we can't scrape html correctly)
    or that the category found is not registered in our system
    """
    pass

def getCategories(domain, add_if_does_not_exist=True):
    """
    Returns list of OpenDNS categories for a domain
    """

    # First, search domain in pre-fetched categories. If the domain was not previously saved, query OpenDns
    # Transaction protects from other threads creating same domain
    # Todo: habra que hacer algo para que con el tiempo se vuelva a hacer peticion a opendns
    approved_categories = []
    with transaction.commit_on_success():
        if CategorizedDomain.objects.filter(domain=domain).exists():
            approved_categories = CategorizedDomain.objects.get(domain=domain).categories.all()
            approved_categories = [cat.name for cat in approved_categories]
        elif add_if_does_not_exist:
            page = urllib2.urlopen("http://domain.opendns.com/" + domain)
            htmlCode = "".join(page.readlines()).replace("\n", "").replace("\t", "")
            xmlTree = html.fromstring(htmlCode)
            approved_categories = xmlTree.xpath(APPROVED_CATEGORIES_QUERY)

            # Check existence and adapt to our categories
            for category in approved_categories:
                if category not in CATEGORIES.keys():
                    raise OpenDNS_DOMException()
            approved_categories = [CATEGORIES[cat] for cat in approved_categories]

            cat_domain = CategorizedDomain(domain=domain)
            cat_domain.save()
            cat_domain.add_categories(approved_categories)

    return approved_categories