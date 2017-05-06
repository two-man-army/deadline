import {divideCollectionIntoPieces, convertToUrlFriendlyText, convertFromUrlToFriendlyText} from '../helpers.js'

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

it('divide collection should divide', done => {
  let inputCol = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  let expectedOutput = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]]

  expect(divideCollectionIntoPieces(inputCol, 3)).toEqual(expectedOutput)
  done()
})

it('divideCollectionIntoPieces should not alter original array', done => {
  let inputCol = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  let expectedOutput = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]]

  divideCollectionIntoPieces(inputCol, 3)
  expect(inputCol).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
  done()
})

it('divideCollection should put as much as possible into one list', done => {
  let inputCol = [1, 2, 3]
  let expectedOutput = [[1, 2, 3]]
  expect(divideCollectionIntoPieces(inputCol, 12)).toEqual(expectedOutput)
  done()
})
