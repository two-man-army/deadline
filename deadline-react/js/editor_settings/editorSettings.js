const options = {
  scrollbar: {
    arrowSize: 30,
    verticalHasArrows: true,
    horizontalHasArrows: true
  }
}

const themeOptions = [
  {
    key: 'monokai',
    value: 'monokai',
    text: 'Monokai'
  },
  {
    key: 'terminal',
    value: 'terminal',
    text: 'Terminal'
  },
  {
    key: 'github',
    value: 'github',
    text: 'Github'
  }
]

const requireConfig = {
  url: 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.1/require.min.js',
  paths: {
    'vs': '/node_modules/monaco-editor/min/vs'
  }
}

export { themeOptions, requireConfig, options }
