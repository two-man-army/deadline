import {convertToUrlFriendlyText} from '../helpers.js'

it('convertToUrlFriendlyText should replace whitespaces and de-capitalize letters', done => {
  let input = 'Dynamic Programming'
  let expectedOuput = 'dynamic_programming'
  expect(convertToUrlFriendlyText(input)).toBe(expectedOuput)
  done()
})
