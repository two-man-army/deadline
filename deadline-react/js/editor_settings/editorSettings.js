const options = {
  scrollbar: {
    arrowSize: 30,
    verticalHasArrows: true,
    horizontalHasArrows: true
  }
}

const themeOptions = [
  {
    key: 'vs',
    value: 'vs',
    text: 'Visual Studio'
  },
  {
    key: 'vs-dark',
    value: 'vs-dark',
    text: 'Visual Studio Dark'
  },
  {
    key: 'hc-black',
    value: 'hc-black',
    text: 'High Contrast'
  }
]

const requireConfig = {
  url: 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.1/require.min.js',
  paths: {
    'vs': '/node_modules/monaco-editor/min/vs'
  }
}

export { themeOptions, requireConfig, options }
