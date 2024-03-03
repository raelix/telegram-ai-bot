const { goTo, delayFor } = require('./utils');

module.exports = class Scraper {

    static SCRAPE_PATH = 'pathEvaluator'

    constructor(page, options = { language: "it", timeout: 10000 }) {
        this.page = page;
        this.options = options;
        this.items = {};
    }

    async scrape(genres = [], generics = [], items={}) {
        this.items = items;
        this.genres = genres;
        this.generics = generics;

        const handleResponse = this.handleResponse.bind(this);
        this.page.on('response', handleResponse);

        // loop over each generic and call scrapeGeneric
        for (const generic of this.generics) {
            await this.scrapeGeneric(generic);
        }
        // loop over each genres and call scrapeGenre
        for (const genre of this.genres) {
            await this.scrapeGenre(genre);
        }
        this.page.off('response', handleResponse);
        return this.items;
    }

    async scrapeGenre(genreId) {
        await goTo(this.page, `https://www.netflix.com/browse/m/genre/${genreId}?so=az`);
        await this.#scrape();
    }

    async scrapeGeneric(url) {
        await goTo(this.page, url);
        await this.#scrape();
    }

    async #scrape() {
        // autoScroll allow to receive network requests
        await this.#autoScroll();
        // get the object directly from the local browser cache
        await this.parseLocalCache();
    }

    /////////////////
    // Parse cache //
    /////////////////
    async parseLocalCache() {
        const dataStringified = await this.page.evaluate(() => JSON.stringify(netflix.falcorCache));
        const data = JSON.parse(dataStringified);
        if (data.hasOwnProperty('genres')) {
            console.log('Cache found - type: genres');
            this.parseGenreObject(data.genres);
            // update known genre for all items
            for (const [key, genres] of Object.entries(data.genres)) {
                if (genres.hasOwnProperty('id') && genres.hasOwnProperty('name')) {
                    const genreId = genres.id.value;
                    const value = genres.name.value;
                    // console.log(`Updating genre - ${genreId} - with name - ${value}`);
                    for (const [titleId, content] of Object.entries(this.items)) {
                        // console.log(`Title: ${titleId} has genre: ${content.genre}`);
                        if (content.hasOwnProperty('genre') && content.genre == genreId) {
                            this.items[titleId]['genreName'] = value;
                        }
                    }
                    // // update the file
                    // writeToFile(`result`, JSON.stringify(items))
                }
            }
        }
    }

    ///////////////////////
    // Scrolling methods //
    ///////////////////////

    async #autoScroll(options={ initialDelay: 4000, scrollDelay: 1000 }) {
        let preCount = 0;
        let postCount = 0;
        await delayFor(options.initialDelay);
        do {
            preCount = await this.#getCount();
            await this.#scrollDown();
            await delayFor(options.scrollDelay);
            postCount = await this.#getCount();
        } while (postCount > preCount);
        console.log("Scroll completed.")
    }

    async #getCount() {
        return await this.page.$$eval('.rowContainer', a => a.length);
    }

    async #scrollDown() {
        await this.page.evaluate(async () => {
            // main page
            window.scrollBy(0, document.body.scrollHeight);
            // genre popups
            if (document.querySelectorAll('[data-uia="modal-content-wrapper"]') !== undefined &&
                document.querySelectorAll('[data-uia="modal-content-wrapper"]').length > 0) {
                window.scrollBy(0, document.querySelectorAll('[data-uia="modal-content-wrapper"]')[0].scrollHeight);
            }
        });
    }


    //////////////////////////////
    // Network requests handler //
    //////////////////////////////

    async handleResponse(response) {
        if (response.status() == 200 && response.url().endsWith(Scraper.SCRAPE_PATH)) {
            let jsonResponse = {};
            try {
                jsonResponse = await response.json();
            } catch (error) {
                console.log(`Failing to parse JSON from: ${response.url()}`);
            } finally {
                this.parsePathEvaluator(jsonResponse);
            }
        }
    }

    parsePathEvaluator(data) {
        if (data) {
            if (data.hasOwnProperty('jsonGraph')) {
                if (data.jsonGraph.hasOwnProperty('genres')) {
                    console.log('Network response received - type: genres');
                    this.parseGenreObject(data.jsonGraph.genres);
                }
                else if (data.jsonGraph.hasOwnProperty('lists') && Object.keys(data.jsonGraph.lists).length > 0) {
                    console.log('Network response received - type: generic');
                    this.parseGenericObject(data.jsonGraph.lists);
                }
            }
        }
    }

    parseGenreObject(data) {
        if (data) {
            for (const [key, genres] of Object.entries(data)) {
                if (genres.hasOwnProperty('az')) {
                    for (const [id, obj] of Object.entries(genres.az)) {
                        if (obj.hasOwnProperty('itemSummary') && obj.itemSummary.hasOwnProperty('value')) {
                            const currentItem = obj.itemSummary.value;
                            if (this.items.hasOwnProperty(currentItem.id)){
                                console.log(`Skipping ${currentItem.id}, it was already processed`);
                                continue;
                            }
                            this.items[currentItem.id] = currentItem;
                            this.items[currentItem.id]['genre'] = key;
                        }
                    }
                }
            }
        }
    }

    parseGenericObject(data) {
        if (data) {
            for (const [nesId, nesItem] of Object.entries(data)) {
                if (nesItem && Object.keys(nesItem).length > 0) {
                    let genre = 0;
                    let context = "";
                    let displayName = "";
                    // get NES block genre and/or context if present
                    if (nesItem.hasOwnProperty('componentSummary')) {
                        const cSummary = nesItem.componentSummary;
                        if (cSummary.hasOwnProperty('value')) {
                            if (cSummary.value.hasOwnProperty('displayName')) {
                                displayName = cSummary.value.displayName;
                            }
                            if (cSummary.value.hasOwnProperty('context')) {
                                context = cSummary.value.context;
                                if (cSummary.value.context === "genre") {
                                    genre = cSummary.value.genreId;
                                }

                            }
                        }
                    }
                    // parse the actual data
                    for (const [nesChildId, nesChild] of Object.entries(nesItem)) {
                        if (nesChild && Object.keys(nesChild).length > 0) {
                            if (nesChild.hasOwnProperty('itemSummary') && nesChild.itemSummary.hasOwnProperty('value')) {
                                const currentItem = nesChild.itemSummary.value;
                                if (this.items.hasOwnProperty(currentItem.id)){
                                    console.log(`Skipping ${currentItem.id}, it was already processed`);
                                    continue;
                                }
                                this.items[currentItem.id] = currentItem;
                                if (context !== "") {
                                    this.items[currentItem.id]['context'] = context;
                                }
                                if (genre !== 0) {
                                    this.items[currentItem.id]['genre'] = genre;
                                    // this.items[currentItem.id]['genreName'] = displayName;
                                } 
                                if (displayName !== "") {
                                    this.items[currentItem.id]['displayName'] = displayName;
                                }
                            }
                        }

                    }
                }
            }
        }
    }

}