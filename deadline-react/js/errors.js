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

function EmptySolutionError (title, message) {
  this.name = 'EmptySolutionError'
  this.title = title || 'Unknown Error'
  this.message = message || 'Unknown Error'
  this.stack = (new Error()).stack
}
EmptySolutionError.prototype = Object.create(Error.prototype)
EmptySolutionError.prototype.constructor = EmptySolutionError

export {SweetAlertError, EmptySolutionError}
