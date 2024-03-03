const fs = require('fs')
process.env.NODE_ENV = "production"

const config = require('config');
const { writeToFileAsJson } = require('./utils');
// Load the full build.
var _ = require('lodash');

class Cleaner {

    constructor(filename, fieldsToRemove=[], fieldsToReplace=[]) {
        this.items = JSON.parse(fs.readFileSync(filename, 'utf-8'));
        this.fieldsToRemove = fieldsToRemove;
        this.fieldsToReplace = fieldsToReplace;
    }

    async run(){
        this.replaceFields();
        this.clean();
        writeToFileAsJson(config.get('output.fileName'), this.items);
    }

    async clean() {
        for (const [key, content] of Object.entries(this.items)) {
            for (const field of this.fieldsToRemove) {
                if (content.hasOwnProperty(field)) {
                    delete content[field];
                }
            }
        }
    }

    async replaceFields() {
        // use lodash to check and read the content of the variable in the child
        // then use the fieldsToReplace list which is a list of objects source and target fields
        for (const [key, content] of Object.entries(this.items)) {
            for (const entity of this.fieldsToReplace) {
                console.log(`getting ${entity.source} from ${key}`);
                if(_.get(content, entity.source)) {
                    _.set(content, entity.target, _.get(content, entity.source));
                }
            }
        }
    }
}

let fieldsToReplace = [];
if (config.has('filters.replace')) {
    fieldsToReplace = config.get('filters.replace');
}

let cleanFields = [];
if (config.has('filters.clean')) {
    cleanFields = config.get('filters.clean');
}
if (config.has('output.fileName')) {
    const cleaner = new Cleaner(config.get('output.fileName'), cleanFields, fieldsToReplace);
    cleaner.run();
}