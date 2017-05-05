/**
 * Restructures text to be more url friendly.
 * Replaces whitespace with underscore (_) and removes capital letters
 * eg: Dynamic Programming -> dynamic_programming
 * @param {String} text
 */
function convertToUrlFriendlyText (text) {
  return text.replace(' ', '_').toLowerCase()
}

/**
 * Reverts the conversion from the convertToUrlFriendlyText function
 * @param {String} text
 */
function convertFromUrlToFriendlyText (text) {
  return text.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

/**
 * Returns the link for the challenge details page
 * @param {Number} id
 */
function getChallengeDetailsLink (id) {
  return `/challenges/${id}`
}

export {convertToUrlFriendlyText, convertFromUrlToFriendlyText, getChallengeDetailsLink}
