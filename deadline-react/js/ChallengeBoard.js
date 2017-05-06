/**
 * The specific Challenge page with the description of the problem and the
 *  code editor for submission
 */
import React from 'react'
import PropTypes from 'prop-types'
import MonacoEditor from 'react-monaco-editor'
import {postChallengeSolution, getChallengeSolution, getSolutionTests} from './requests.js'
import SelectionSearch from './semantic_ui_components/SelectionSearch.js'
import ChallengeTestsResults from './semantic_ui_components/ChallengeTestsResults.js'
import { Segment, Dimmer } from 'semantic-ui-react'
import {divideCollectionIntoPieces} from './helpers.js'

class ChallengeBoard extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      code: '',  // TODO: Load sample code
      chosenLanguage: 'Python',  // TODO: Change with drop down
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
    this.getGradedSolution = this.getGradedSolution.bind(this)
    this.buildSolutionResults = this.buildSolutionResults.bind(this)
    this.displayLoadingTests = this.displayLoadingTests.bind(this)
  }

  /**
   * Build the description JSX for the challenge
   */
  buildDescription () {
    let sampleInput = this.props.description.sample_input !== undefined ? (
      <div className='challenge-desc-sample-input'>
        <p>{this.props.description.sample_input}</p>
      </div>
    ) : (<div />)
    let sampleOutput = this.props.description.sample_output !== undefined ? (
      <div className='challenge-desc-sample-output'>
        <p>{this.props.description.sample_output}</p>
      </div>
    ) : (<div />)
    let explanation = this.props.description.explanation !== undefined ? (
      <div className='challenge-desc-explanation'>
        <p>{this.props.description.explanation}</p>
      </div>
    ) : (<div />)
    return (
      <div className='challenge-description'>
        <h1>Description:</h1>
        <div className='challenge-desc-content'>
          <p>{this.props.description.content}</p>
        </div>
        <h3>Input Format:</h3>
        <div className='challenge-desc-input-format'>
          <p>{this.props.description.input_format}</p>
        </div>
        <h3>Output Format:</h3>
        <div className='challenge-desc-output-format'>
          <p>{this.props.description.output_format}</p>
        </div>
        <h3>Constraints:</h3>
        <div className='challenge-desc-constraints'>
          <p>{this.props.description.constraints}</p>
        </div>
        {sampleInput}
        {sampleOutput}
        {explanation}
      </div>
    )
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
    console.log('onChange', newValue, e)
    this.setState({code: newValue})
  }

  langChangeHandler (event, e) {
    // TODO: Change code on editor
    this.setState({chosenLanguage: e.value})
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
    postChallengeSolution(this.props.id, this.state.code, this.state.chosenLanguage).then(submission => {
      this.setState({hasSubmitted: true, isGrading: true})

      this.displayLoadingTests()

      this.getGradedSolution(this.props.id, submission.id)  // start querying for the updated solution
    }).catch(err => {
      throw err
    })
  }

  render () {
    const requireConfig = {
      url: 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.1/require.min.js',
      paths: {
        'vs': '/node_modules/monaco-editor/min/vs/'
      }
    }
    // TODO: Show test results
    return (
      <div className='challenge-board'>
        {this.buildDescription()}
        <MonacoEditor
          width='800'
          height='600'
          language='javascript'
          value={this.state.code}
          onChange={this.onChange}
          editorDidMount={this.editorDidMount}
          requireConfig={requireConfig}
        />
        <div className='lang-choice-select'>
          <SelectionSearch options={this.buildLanguageSelectOptions()} placeholder='Select Language' onChange={this.langChangeHandler} />
        </div>
        <button onClick={this.submitSolution}>Submit</button>
        {this.state.solutionResultsJSX}
        <script src={'/node_modules/monaco-editor/min/vs/loader.js'} />
      </div>
    )
  }
}

ChallengeBoard.propTypes = {
  id: PropTypes.number,
  // name: PropTypes.string,
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
  supported_languages: PropTypes.arrayOf(PropTypes.string)
}

export default ChallengeBoard
