# Netflix Scraper
This tool aims to extract different information from Netflix. This includes:
- Recent titles
- Genre based titles
- Watched movies
- Affinity match percentage

# Requirements
- nodejs
- typescript
- npm

# Quick start
### Install the dependencies
```shell
npm install
```
### Create the configuration
Place it in ```./config``` and call it ```production.yaml```
```yaml
login:
  username: YOUR_NETFLIX_EMAIL
  password: YOUR_NETFLIX_PASSWORD
  profile: THE_USER_PROFILE_NAME
activity:
  enabled: true # set to true if you want to extract the watched movies
scrape:
  enabled: true # set to true to enable the movies scraper
  appendToExisting: true # set to true to append extracted data to an existing/previous scrape
details:
  enabled: true # set to true to fetch extra details from each movie discovered during the scrape procedure
```
### Run it!
```shell
npm run start
```
# How it works
Under the wood this small tool uses Puppeteer to open a managed browser and connect to the session to extract all the data.

# Disclaimer
This tool is only for learning purposes. Do not use against the Netflix website as it's not allowed and you could be banned!!