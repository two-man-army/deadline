import {convertToUrlFriendlyText, convertFromUrlToFriendlyText} from '../helpers.js'

it('convertToUrlFriendlyText should replace whitespaces and de-capitalize letters', done => {
  let input = 'Dynamic Programming'
  let expectedOuput = 'dynamic_programming'
  expect(convertToUrlFriendlyText(input)).toBe(expectedOuput)
  done()
})


it('convertFromUrlToFriendlyText should replace underscores with white spaces and capitalize letters', done => {
  let input = 'dynamic_programming'
  let expectedOutput = 'Dynamic Programming'
  expect(convertFromUrlToFriendlyText(input)).toBe(expectedOutput)
  done()
})

it('convert helper functions should be resuable one after another', done => {
  let input = 'What The Hell Is Happening'
  let origInput = input
  for (let i = 0; i < 10; i++) {
    input = convertFromUrlToFriendlyText(convertToUrlFriendlyText(input))
  }
  expect(input).toBe(origInput)
  done()
})
