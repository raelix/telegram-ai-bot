const puppeteer = require('puppeteer');
const fs = require('fs');
// Will search for production.* in config
process.env.NODE_ENV = "production"

const config = require('config');
const { writeToFileAsJson } = require('./utils');
const UserLogin = require('./user-login');
const UserActivity = require('./user-activity');
const Scraper = require('./scraper');
const MovieDetails = require('./movie-details');

const BROWSER_HEADERS = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'

let browser = null;

function markWatched(watched, scraped) {
    let watchedCount = 0;
    for (const [key, value] of Object.entries(scraped)) {
        if (watched.hasOwnProperty(key)) {
            scraped[key]['watched'] = true;
            watchedCount++;
        } else {
            scraped[key]['watched'] = false;
        }
    }
    console.log(`Watched ${watchedCount} scraped movies.`);
    return scraped;
}

async function start() {

    browser = await puppeteer.launch({
        executablePath: process.env['PUPPETEER_EXECUTABLE_PATH'],
        headless: true,
        userDataDir: './session',
        defaultViewport: null,
        detached: false,
        args: [
            '--mute-audio',
            // '--disable-features=site-per-process',
            // '--enable-chrome-browser-cloud-management',
        ],
        // dumpio: true,
    })

    var [page] = await browser.pages();
    await page.setUserAgent(BROWSER_HEADERS);

    let appendToExisting = true
    if (config.has('scrape.appendToExisting')) {
        appendToExisting = config.get('scrape.appendToExisting');
    }

    let scrapeEnabled = true;
    if (config.has('scrape.enabled')) {
        scrapeEnabled = config.get('scrape.enabled');
    }

    let userActivityEnabled = false;
    if (config.has('activity.enabled')) {
        userActivityEnabled = config.get('activity.enabled');
    }

    let detailsEnabled = true;
    if (config.has('details.enabled')) {
        detailsEnabled = config.get('details.enabled');
    }

    let scrapedFilename = 'netflix.json';
    if (config.has('output.scrapedFileName')) {
        scrapedFilename = config.get('output.scrapedFileName');
    }

    let watchedFilename = 'watched.json';
    if (config.has('output.watchedFileName')) {
        watchedFilename = config.get('output.watchedFileName');
    }

    if (config.has('login.profile') && config.has('login.username') && config.has('login.password')) {
        const userLogin = new UserLogin(page, config.get('login.profile'), config.get('login.username'), config.get('login.password'));
        await userLogin.login();
    }

    let watchedMovies = {};
    if (userActivityEnabled) {
        const userActivity = new UserActivity(page);
        watchedMovies = await userActivity.fetch();
        writeToFileAsJson(watchedFilename, watchedMovies);
    } else {
        try { watchedMovies = JSON.parse(fs.readFileSync(watchedFilename, 'utf-8')); } catch (error) { }
    }

    let scraped = {};

    if (appendToExisting) {
        try { 
            scraped = JSON.parse(fs.readFileSync(scrapedFilename, 'utf-8')); 
        } catch (error) {
            console.log("No previous scrape found.");
            if (scrapeEnabled){
                console.log('Starting fresh.');
            }
        }
    }

    if (scrapeEnabled) {
        let genres = [];
        if (config.has('genres')) {
            genres = config.get('genres');
        }

        let generics = [];
        if (config.has('generics')) {
            generics = config.get('generics');
        }

        const scraper = new Scraper(page);
        scraped = await scraper.scrape(
            genres = genres,
            generics = generics,
            items = scraped
        );
        writeToFileAsJson(scrapedFilename, scraped);
    } 

    scraped = markWatched(watchedMovies, scraped);

    try {
        if (detailsEnabled) {
            const movieDetails = new MovieDetails(browser, scraped);
            scraped = await movieDetails.scrapeDetails();
        }
    } catch (error) {
        console.log(error);
    }
    
    writeToFileAsJson(scrapedFilename, scraped);
    console.log(`Done. File saved to ${scrapedFilename}`);

    await browser.close();
}

start();

async function close() {
    await browser.close();
}
process.on('SIGTERM', async function () {
    console.log("Caught interrupt signal");
    await close();
});
process.on('SIGINT', async function () {
    console.log("Caught interrupt signal");
    await close();
});



// page = await browser.newPage();
// await page.reload({
//     timeout: 5000, waitUntil: [
//         'load',
//         'domcontentloaded',
//         //  'networkidle0',
//         //  'networkidle2'
//     ],
// });
// try {
//     await page.$eval('.rowContainer:last-child', e => {
//         e.scrollIntoView({ behavior: 'smooth', block: 'end', inline: 'end' });
//     });
// } catch (error) { }
// Similar https://www.netflix.com/browse/m/similars/80218885 - ID for search similar stuff