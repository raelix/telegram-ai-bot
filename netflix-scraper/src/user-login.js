const { goTo, waitAndClick } = require('./utils');

module.exports = class UserLogin {

    constructor(page, profileName, username, password, options={language: "it", timeout: 10000}) {
        this.profileName = profileName;
        this.page = page;
        this.username = username;
        this.password = password;
        this.options = options;
    }

    async login(){
        await goTo(this.page, `https://www.netflix.com/${this.options.language}/login`, {timeout: this.options.timeout});
        await this.typeCredentials();
        await this.selectProfile(this.profileName);
    }

    async typeCredentials(){
            try {
                await this.page.waitForSelector('input[name="userLoginId"]', { visible: true, timeout: 1000 });
                await this.page.type('input[name="userLoginId"]', this.username, { delay: 100 });
                await this.page.type('input[name="password"]', this.password, { delay: 100 });
                await waitAndClick(this.page, 'button[data-uia="login-submit-button"]', 1000);
                await this.page.waitForNavigation();
            } catch (error) {
                console.log('Already logged-in!');
            }
    }

    async selectProfile(profileName) {
        try {
            await this.page.waitForSelector('a.profile-link', { visible: true, timeout: 1000 })
            await this.page.waitForSelector('span.profile-name', { visible: true, timeout: 1000 })
            await this.page.evaluate((profileName) => {
                const spans = document.querySelectorAll('span.profile-name');
                for (const span of spans) {
                    if (span.textContent.trim() === profileName) {
                        const parentA = span.closest('a');
                        if (parentA)
                            parentA.click();
                    }
                }
            }, profileName);
            await this.page.waitForNavigation({ timeout: 5000 });
        }
        catch (error) {
            console.log(`Profile ${profileName} already selected!`);
        }
    }
}