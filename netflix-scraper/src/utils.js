
const fs = require('fs');

async function goTo(page, url, options = { timeout: 10000, extraWait: [] }) {
    wait = [
        'load',
        'domcontentloaded',
    ].concat(options.extraWait??[]);
    await page.goto(url, {
        timeout: options.timeout?? 10000,
        waitUntil: wait,
    });
}

async function waitAndClick(page, selector, options = { visible: true, timeout: 1000 }) {
    try {
        await page.waitForSelector(selector, options);
        await page.click(selector);
        return true;
    }
    catch (error) {
        return false
    }
}

async function writeToFileAsJson(filename, data) {
    fs.writeFile(filename, JSON.stringify(data, null, 2), (err) => {
        if (err) {
            console.log(err);
        }
    });
}

const delayFor = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

module.exports.goTo = goTo;
module.exports.waitAndClick = waitAndClick;
module.exports.delayFor = delayFor;
module.exports.writeToFileAsJson = writeToFileAsJson;