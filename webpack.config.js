module.exports = {
  entry: './casinodicegame/js/game.js',
  output: {
    filename: 'casinodicegame/static/bundle.js'       
  },
  module: {
    loaders: [
      { test: /\.js$/, loader: 'jsx-loader?harmony' }
    ]
  }
};
