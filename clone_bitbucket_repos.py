import os
import logging
import time
from urllib.parse import urljoin

from selenium import webdriver
from selene import browser
from selene.support.conditions import be, have
from selene.support.jquery_style_selectors import s, ss


root_path = os.path.dirname(__file__)
repos_dir = os.path.join(root_path, "repos")


# export BB_URL=url BB_USERNAME=username BB_PASSWORD=password
base_url = os.environ.get("BB_URL")
credentials = {
    "username": os.environ.get("BB_USERNAME"),
    "password": os.environ.get("BB_PASSWORD")
}


class BitbucketPage:
    def __init__(self):
        self.login = s("#j_username")
        self.password = s("#j_password")
        self.submit = s("#submit")

        self.projects_button = s("a[href='/projects']")
        self.projects = ss("#projects-container > div > div > table > tbody a")
        self.repos = ss("#repositories-container > div > div.paged-table-container > table > tbody a")

        self.clone_button = s("#clone-repo-button")
        self.actual_href_element = s(
            "#clone-repo-dialog-content > div.clone-url.ssh-clone-url-default > div.aui-buttons > input"
        )


options = webdriver.ChromeOptions()
driver = webdriver.Chrome

options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

browser.set_driver(driver(options=options))
page = BitbucketPage()


def authenticate():
    logging.info("authentication has been initiated.")
    browser.open_url(base_url)

    page.login.should(be.visible).set(credentials['username'])
    page.password.should(be.visible).set(credentials['password'])
    page.submit.click()

    browser.should(have.url(urljoin(base_url, "dashboard")))
    logging.info("authentication has been successful.")


def collect_repos():
    logging.info("start collecting repo urls ...")
    urls = {}

    page.projects_button.should(be.clickable).click()
    projects_url = browser.driver().current_url

    time.sleep(10)
    for project in page.projects:

        # form project dir name
        project_dir = project.get_attribute("href").split("/")[-1].lower()
        urls[project_dir] = []

        project.click()

        repos_url = browser.driver().current_url

        time.sleep(10)
        for repo in page.repos:
            repo.click()
            page.clone_button.click()

            url = page.actual_href_element.should(be.visible).get_attribute("value")
            urls[project_dir].append(url)
            logging.info(f"repo url: '{url}' has been collected ...")

            browser.open_url(repos_url)
        browser.open_url(projects_url)

    logging.info("repo collecting has been finished.")
    return urls


def clone_repos(repos):
    os.makedirs(repos_dir, exist_ok=True)

    for project in repos:
        os.makedirs(f"{repos_dir}/{project}", exist_ok=True)

        for repo in repos[project]:
            logging.info(f"system is preparing to clone into {repos_dir}/{project} folder ...")
            exit_code = os.system(f"cd {repos_dir}/{project}; git clone {repo}")

            if exit_code == 0:
                logging.info(f"repo: '{repo}' has been cloned to the dir: '{repos_dir} ...")
            else:
                logging.error(f"clone: {repo} failed with: {exit_code}")

    logging.info("repo cloning has been finished.")


def main():
    logging.basicConfig(level=logging.INFO)

    authenticate()
    repos = collect_repos()
    clone_repos(repos)
    browser.quit()


if __name__ == "__main__":
    main()
