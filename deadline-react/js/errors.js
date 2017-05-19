/**
 * A custom Error type for easy handling of errors which we want to show to the user
 * @param {String} title
 * @param {String} message
 */

function SweetAlertError (title, message, field) {
  this.name = 'SweetAlertError'
  this.title = title || 'Unknown Error'
  this.field = field || 'Unknown'
  this.message = message || 'Unknown Error'
  this.stack = (new Error()).stack
}
SweetAlertError.prototype = Object.create(Error.prototype)
SweetAlertError.prototype.constructor = SweetAlertError

export {SweetAlertError}
