module.exports = {
  transpileDependencies: [
    'vuetify'
  ],

  pluginOptions: {
    i18n: {
      locale: 'en',
      fallbackLocale: 'en',
      localeDir: 'locales',
      enableInSFC: false
    }
  },

  configureWebpack: {
    module: {
      rules: [
        {
          test: /\.md$/,
          loader: "raw-loader",
        },
      ],
    },
  },
}
