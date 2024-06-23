var addon = require('bindings')('ffmpeg_hello');

console.log(addon.hello()); // 'world'