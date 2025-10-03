from config.config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD
from Scraper.GroupsMembersScraper import GroupsMembersScraper



scraper = GroupsMembersScraper(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)

scraper.run("https://www.linkedin.com/groups/39683/", "data/output.csv","Ahmed")

