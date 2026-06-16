const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');
const { withRorkMetro } = require('@rork-ai/toolkit-sdk/metro');

const config = withRorkMetro(getDefaultConfig(__dirname));
const originalResolveRequest = config.resolver?.resolveRequest;

config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (moduleName === '@vercel/oidc') {
    return {
      filePath: path.resolve(
        __dirname,
        'node_modules/@vercel/oidc/dist/index-browser.js'
      ),
      type: 'sourceFile',
    };
  }

  if (originalResolveRequest) {
    return originalResolveRequest(context, moduleName, platform);
  }

  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
