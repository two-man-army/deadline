/**
 * Restructures text to be more url friendly.
 * Replaces whitespace with underscore (_) and removes capital letters
 * eg: Dynamic Programming -> dynamic_programming
 * @param {String} text
 */
function convertToUrlFriendlyText (text) {
  return text.replace(' ', '_').toLowerCase()
}

export {convertToUrlFriendlyText}
