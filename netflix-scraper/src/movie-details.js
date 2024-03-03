const { goTo, delayFor } = require('./utils');
var _ = require('lodash');
const rxjs = require("rxjs");
const { mergeMap, toArray } = require("rxjs/operators");
const { interval, take, lastValueFrom } = require('rxjs');

module.exports = class MovieDetails {
    static CONCURRENT_TABS = 5;

    constructor(browser, items) {
        this.browser = browser;
        this.items = items;
        this.availableTabs = [];
    }

    // withPage = (browser) => async (fn) => {
    //     const page = await browser.newPage();
    //     try {
    //         return await fn(page);
    //     } finally {
    //         await page.close();
    //     }
    // }
    splitArrayIntoSubArrays(array, numSubArrays) {
        const subArrays = [];
        const itemsPerSubArray = Math.floor(array.length / numSubArrays);
        let startIndex = 0;
    
        for (let i = 0; i < numSubArrays; i++) {
            let chunk = [];
    
            if (i === numSubArrays - 1) {
                // Last sub-array, include the remaining elements
                chunk = array.slice(startIndex);
            } else {
                chunk = array.slice(startIndex, startIndex + itemsPerSubArray);
            }
    
            subArrays.push(chunk);
            startIndex += itemsPerSubArray;
        }
    
        return subArrays;
    }

    async scrapeDetails() {
        const waitBetween = 5000;
        const numberOfSubArrays = Object.keys(this.items).length / 20;
        const subArrays = this.splitArrayIntoSubArrays(Object.keys(this.items), numberOfSubArrays);
        // let counter = 0;
        let status = {
            counter: 0,
            errorCounts: 0,
        };
        for (const subArray of subArrays) {
            status = await this.elaborate(subArray, status);
            if (status.errorCounts > 20){
                console.log(`Aborting due to too many errors, error counts: ${status.errorCounts}`);
                break;
            }
            console.log(`Waiting for ${waitBetween / 1000} seconds...`);
            await delayFor(waitBetween);
        }
        return this.items;

    }

    async elaborate(titleIds, status){
        const promise = rxjs.from(titleIds).pipe(
            mergeMap(async (id) => {
                if (this.items[id].hasOwnProperty('cast')){
                    status.counter++;
                    console.log(`Skipping ${id}, it was already processed`);
                    return
                }
                const page = await this.browser.newPage();
                try {
                    await goTo(page, `https://www.netflix.com/title/${id}`, { timeout: 50000, extraWait: ['networkidle0', 'networkidle2'] });
                    await delayFor(500);
                    this.fetchMoviesDescription(page, id, status);
                    console.log(`Got movie details for ${status.counter++} on ${Object.keys(this.items).length}`);
                } catch (error) {
                    console.log(`Failed to load page for: ${id}`);
                    status.errorCounts++;
                }
                await page.close();
            }, MovieDetails.CONCURRENT_TABS),
            toArray(),
        );
        await lastValueFrom(promise);
        return status;
    }

    async fetchMoviesDescription(tab, titleId, status) {
        let data = {};
        try {
            const dataStringified = await tab.evaluate(() => {
                return JSON.stringify(netflix.falcorCache.videos);
            });
            data = JSON.parse(dataStringified);
        } catch (error) {
            console.log(`Failed to fetch description for: ${titleId}. Increasing error count...`);
            status.errorCounts++;
            return;
        }

        // console.log(`Fetched description for: ${titleId} - ${JSON.stringify(data[titleId])}`);
        // this.items[titleId]['extraInfo'] = data[titleId];
        this.items[titleId]['matchScore'] = _.get(data[titleId], "userRating.value.matchScore");
        this.items[titleId]['description'] = _.get(data[titleId], "jawSummary.value.contextualSynopsis.text");
        this.items[titleId]['tags'] = _.get(data[titleId], "bobSummary.value.evidence.tags.value");
        this.items[titleId]['quality'] = _.get(data[titleId], "bobSummary.value.delivery.quality");
        this.items[titleId]['cast'] = this.flattenList(_.get(data[titleId], "jawSummary.value.cast"));
        this.items[titleId]['creators'] = this.flattenList(_.get(data[titleId], "jawSummary.value.creators"));
        this.items[titleId]['directors'] = this.flattenList(_.get(data[titleId], "jawSummary.value.directors"));
        this.items[titleId]['genres'] = this.flattenList(_.get(data[titleId], "jawSummary.value.genres"));
        this.items[titleId]['writers'] = this.flattenList(_.get(data[titleId], "jawSummary.value.writers"));
        await delayFor(10000);
    }

    flattenList(objectList) {
        if (objectList === undefined) {
            return [];
        }
        let newobjectList = [];
        for (const cast of objectList) {
            if (cast.hasOwnProperty('name')) {
                newobjectList.push(cast.name);
            }
        }
        return newobjectList;
    }
}
