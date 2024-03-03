
const { goTo } = require('./utils');

module.exports = class UserActivity {
    static DEFAULT_PAGE_TIMEOUT = 10000
    constructor(page) {
        this.page = page;
        this.internalCounter = 0;
        this.currentPage = 0;
        this.viewedItems = {};
    }

    async fetch() {
        await this.page.setRequestInterception(true);
        const interceptRequest = this.interceptRequest.bind(this);
        this.page.on('request', interceptRequest);
        const interceptResponse = this.interceptResponse.bind(this);
        this.page.on('response', interceptResponse);
        await this.goToUserActivity();
        // start triggering the loop
        await this.clickShowNext();
        // wait for the button to be disabled
        await this.page.waitForSelector('button.disabled');
        console.log(`Fetched ${Object.keys(this.viewedItems).length} items watched.`);
        console.log('Process completed.');
        // remove listeners
        await this.page.setRequestInterception(false);
        this.page.off('request', interceptRequest);
        this.page.off('request', interceptResponse);
        return this.viewedItems;
    }

    async interceptRequest(request) {
        if (request.url().includes("viewingactivity")) {
            try {
                // increase the size of the results and start from 0 instead of 1
                const newPath = request.url().replace(/pg=\d*&/gm, `pg=${this.currentPage}&`).replace('pgsize=50', 'pgsize=1000');
                this.currentPage++;
                request.continue({ 'url': newPath });
            } catch (error) {
                console.log('Error while request interception', { error });
            }
        } else {
            request.continue();
        }
    }

    async interceptResponse(response) {
        if (response.status() == 200 && response.url().includes("viewingactivity")) {
            let jsonResponse = {};
            try {
                jsonResponse = await response.json();
            } catch (error) {
                console.log(`Failing to parse JSON from: ${response.url()}`);
            } finally {
                this.internalCounter++;
                if (jsonResponse.hasOwnProperty('viewedItems') && jsonResponse.viewedItems.length > 0) {
                    for (const item of jsonResponse.viewedItems) {
                        let fullTitle = item.videoTitle;
                        let id = item.movieID;
                        // in case it's a series it become like:
                        // "Berlino: Stagione 1: Un elefante in via d'estinzione"
                        if (item.hasOwnProperty('seriesTitle')){
                            fullTitle = `${item.seriesTitle}: ${item.seasonDescriptor}: ${item.episodeTitle}`;
                        }
                        if (!this.viewedItems.hasOwnProperty(id)) {
                            this.viewedItems[id] = item;
                            this.viewedItems[id]['fullTitle'] = fullTitle;
                        }
                    }
                    await this.clickShowNext();
                } else {
                    // generally here the button is disabled so we do not receive any response with 0 items
                    console.log(`Fetched ${Object.keys(this.viewedItems).length} items.`);
                    console.log('Process completed.');
                }
            }
        }
    }

    async clickShowNext() {
        try {
            await this.page.waitForSelector('button.btn-small')
            await this.page.click('button.btn-small');
        } catch (error) {
            console.log('No more pages to fetch');
            return;
        }
    }

    async goToUserActivity() {
        await goTo(this.page, 'https://www.netflix.com/settings/viewed/');
    }
}