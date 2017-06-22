/**
 * The specific Challenge page with the description of the problem and the
 *  code editor for submission
 */
import React from 'react'
import PropTypes from 'prop-types'
import MonacoEditor from 'react-monaco-editor'
import {getLanguageDetail, postChallengeSolution, getChallengeSolution, getSolutionTests} from './requests.js'
import SelectionSearch from './semantic_ui_components/SelectionSearch.js'
import ChallengeTestsResults from './semantic_ui_components/ChallengeTestsResults.js'
import { themeOptions, requireConfig } from './editor_settings/editorSettings.js'
import { Segment, Dimmer, Container } from 'semantic-ui-react'
import { divideCollectionIntoPieces } from './helpers.js'

class ChallengeBoard extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      code: '',
      selectedLanguage: 'Python',
      selectedTheme: 'vs-dark',
      hasSubmitted: false,
      isGrading: false,
      loadedResults: false,
      gradedSolution: undefined,
      solutionResultsJSX: <div />
    }
    this.buildDescription = this.buildDescription.bind(this)
    this.onChange = this.onChange.bind(this)
    this.editorDidMount = this.editorDidMount.bind(this)
    this.submitSolution = this.submitSolution.bind(this)
    this.langChangeHandler = this.langChangeHandler.bind(this)
    this.themeChangeHandler = this.themeChangeHandler.bind(this)
    this.getGradedSolution = this.getGradedSolution.bind(this)
    this.buildSolutionResults = this.buildSolutionResults.bind(this)
    this.displayLoadingTests = this.displayLoadingTests.bind(this)
    this.convertBold = this.parseTextIntoHTML.bind(this)
    this.cleanArray = this.cleanArray.bind(this)
  }

  /**
   * Build the description JSX for the challenge
   */
  buildDescription () {
    let sampleInput = this.props.description.sample_input !== undefined && this.props.description.sample_input.length >= 1 ? (
      <div className='challenge-desc-sample-input'>
        <h3>Sample Input</h3>
        <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.sample_input)}} />
      </div>
    ) : (<div />)
    let sampleOutput = this.props.description.sample_output !== undefined && this.props.description.sample_output.length >= 1 ? (
      <div className='challenge-desc-sample-output'>
        <h3>Sample Output:</h3>
        <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.sample_output)}} />
      </div>
    ) : (<div />)

    let explanation = this.props.description.explanation !== undefined && this.props.description.explanation.length >= 1 ? (
      <div className='challenge-desc-explanation'>
        <h3>Explanation:</h3>
        <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.explanation)}} />
      </div>
    ) : (<div />)

    return (
      <div className='challenge-description'>
        <div className='challenge-desc-content'>
          <h1>Description:</h1>
          <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.content)}} />
        </div>
        <div className='challenge-desc-input-format'>
          <h3>Input Format:</h3>
          <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.input_format)}} />
        </div>
        <div className='challenge-desc-output-format'>
          <h3>Output Format:</h3>
          <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.output_format)}} />
        </div>
        <div className='challenge-desc-constraints'>
          <h3>Constraints:</h3>
          <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.constraints)}} />
        </div>
        {sampleInput}
        {sampleOutput}
        {explanation}
      </div>
    )
  }
 // Will remove all falsy values: undefined, null, 0, false, NaN and "" (empty string)
  cleanArray (actual) {
    let newArray = []
    for (var i = 0; i < actual.length; i++) {
      if (actual[i]) {
        newArray.push(actual[i])
      }
    }
    return newArray
  }

  // Parses our text into HTML, searching for certain placeholders like {{NPL}} and ** surroundings
  parseTextIntoHTML (str) {
    if (str === undefined) {
      return str
    }

    var splitContent = str.split(/\s/)
    for (var i = 0; i < splitContent.length; i++) {
      let word = splitContent[i]

      // a bold word markup is a word surrounded by **word**
      if (word.length > 4 && word.startsWith('**')) {
        let lastThreeElements = word.substring(word.length - 3)

        if (lastThreeElements.endsWith('**')) {
          let wantedStr = word.substring(2, word.length - 2)
          word = '<span class="variable-descriptor">' + wantedStr + '</span>'
        } else if (lastThreeElements[0] === '*' && lastThreeElements[1] === '*') {
          // word ends with a punctuation at the end. i.e **tank**.
          var wantedStr = word.substring(2, word.length - 3)
          let lastElement = lastThreeElements[2]
          word = '<span class="variable-descriptor">' + wantedStr + '</span>' + lastElement
        }
      }

      splitContent[i] = word
    }
    var result = this.cleanArray(splitContent.join(' ')
                  .split('{{NPL}}')).join('<br>')  // format new line placeholders

    if (result.length === 0) {
      return ''
    } else {
      return '<p>' + result + '</p>'
    }
  }

  /**
   * Build the information for the Select component with the Challenge's supported languages
   */
  buildLanguageSelectOptions () {
    let options = []
    this.props.supported_languages.forEach(lang => {
      options.push({
        key: lang,
        value: lang,
        text: lang,
        image: {
          avatar: true,
          src: `/assets/img/avatars/small/${lang.toLowerCase()}.png`
        }
      })
    })

    return options
  }

  /**
   * Build the JSX for displaying what the submission has scored
   */
  buildSolutionResults () {
    let solution = this.state.gradedSolution
    if (solution.pending) {
      throw Error('Solution is pending when we want to show the results!')
    }

    if (!solution.compiled) {
      // TODO: Solution has not compiled - show an error message
    }

    // TODO: Query the server for the test results and display them
    getSolutionTests(solution.challenge, solution.id).then(tests => {
      // Assign a number to each test case
      tests = tests.map((test, idx) => {
        test.number = idx + 1
        return test
      })

      // Divide the tests into components with 5 tests each
      let splitTests = divideCollectionIntoPieces(tests, 5)

      let solutionResultsJSX = (
        <div className='solution-tests-container'>
          {splitTests.map((tsts, idx) => {
            return <ChallengeTestsResults key={idx} tests={tsts} />
          })}
        </div>
      )

      this.setState({solutionResultsJSX: solutionResultsJSX})
    }).catch(err => {
      throw err  // TODO: Handle
    })
  }

  editorDidMount (editor, monaco) {
    console.log('editorDidMount', editor)
    editor.focus()
  }

  onChange (newValue, e) {
    this.setState({code: newValue})
  }

  langChangeHandler (event, language) {
    let languageName = language.value
    getLanguageDetail(languageName).then(lang => {
      let defaultCode = lang.default_code
      this.setState({code: defaultCode})
    })
    this.setState({selectedLanguage: languageName})
  }

  themeChangeHandler (event, theme) {
    this.setState({selectedTheme: theme.value})
    console.log(theme.value)
  }

  /**
   * Constantly query the server until the solution is grader
   * @param {Number} challengeId
   * @param {Number} solutionId
   */
  getGradedSolution (challengeId, solutionId) {
    return getChallengeSolution(challengeId, solutionId).then(solution => {
      console.log(`Solution is pending ${solution.pending}`)
      if (solution.pending) {
        // Continue to query the server for the given solution
        return setTimeout(() => {
          return this.getGradedSolution(challengeId, solutionId)
        }, 1000)
      }

      this.setState({isGrading: false, gradedSolution: solution})
      this.buildSolutionResults()
      // TODO: Add to max score
      if (this.props.userInfo.maxScore < solution.result_score) {
        console.log('NEW SCORE')
        this.props.modifyScore(solution.result_score)
      }
      return solution
    })
  }

  /**
   * Displays loading test cases for when a user submits a solution and is waiting for it to be graded
   */
  displayLoadingTests () {
    let loadingTests = []
    for (let i = 1; i < this.props.test_case_count + 1; i += 1) {
      loadingTests.push({number: i, success: false})
    }

    let splitTests = divideCollectionIntoPieces(loadingTests, 5)

    let solutionResultsJSX = (
      <Segment>
        <div className='solution-tests-container'>
          <Dimmer active />
          {splitTests.map((tsts, idx) => {
            return <ChallengeTestsResults key={idx} tests={tsts} toDim toLoad />
          })}
        </div>
      </Segment>
    )

    this.setState({solutionResultsJSX: solutionResultsJSX})
  }

  submitSolution () {
    postChallengeSolution(this.props.id, this.state.code, this.state.selectedLanguage).then(submission => {
      this.setState({hasSubmitted: true, isGrading: true})

      this.displayLoadingTests()

      this.getGradedSolution(this.props.id, submission.id)  // start querying for the updated solution
    }).catch(err => {
      throw err
    })
  }

  render () {
    // TODO: Show test results
    // TODO: Create new component for editor options
    return (
      <Container>
        <div className='challenge-board'>
          <h1 className='challenge-board-title'>{this.props.name}</h1>
          {this.buildDescription()}
          <div className='editor-options'>
            <div className='lang-choice-select'>
              <span>Language</span>
              <SelectionSearch options={this.buildLanguageSelectOptions()} placeholder='Select Language' onChange={this.langChangeHandler} />
            </div>
            <div className='theme-select'>
              <span>Theme</span>
              <SelectionSearch options={themeOptions} placeholder='Select Theme' onChange={this.themeChangeHandler} />
            </div>
          </div>
          <MonacoEditor
            height='600'
            language={this.state.selectedLanguage.toLowerCase()}
            theme={this.state.selectedTheme}
            value={this.state.code}
            onChange={this.onChange}
            editorDidMount={this.editorDidMount}
            requireConfig={requireConfig}
          />
          <button onClick={this.submitSolution}>Submit</button>
          {this.state.solutionResultsJSX}
          <script src={'/node_modules/monaco-editor/min/vs/loader.js'} />
        </div>
      </Container>
    )
  }
}

ChallengeBoard.propTypes = {
  id: PropTypes.number,
  name: PropTypes.string,
  // rating: PropTypes.number,
  // score: PropTypes.number,
  description: PropTypes.shape({
    content: PropTypes.string,
    input_format: PropTypes.string,
    output_format: PropTypes.string,
    constraints: PropTypes.string,
    sample_input: PropTypes.string,
    sample_output: PropTypes.string,
    explanation: PropTypes.string
  }),
  test_case_count: PropTypes.number,
  // category: PropTypes.string,
  supported_languages: PropTypes.arrayOf(PropTypes.string),
  modifyScore: PropTypes.func.isRequired,
  userInfo: PropTypes.object
}

export default ChallengeBoard
