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

/**
 * Divides a collection into pieces of peiceCount parts
 * Basically splits it into lists which all contain at most pieceCount items
 * example - divideCollectionIntoPieces([1,2,3,4,5,6,7], 2) -> [[1,2], [3,4], [5,6], [7]]
 * @param {Number} pieceCount
 */
function divideCollectionIntoPieces (collection, pieceCount) {
  let splitItems = []
  let idx = 0
  while (idx < collection.length) {
    splitItems.push(collection.slice(idx, idx + pieceCount))
    idx += pieceCount
  }

  return splitItems
}

export {divideCollectionIntoPieces, convertToUrlFriendlyText, convertFromUrlToFriendlyText, getChallengeDetailsLink}
