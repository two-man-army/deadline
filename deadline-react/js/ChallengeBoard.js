/** * The specific Challenge page with the description of the problem and the
 *  code editor for submission
 */
import React from 'react'
import PropTypes from 'prop-types'
import SweetAlert from 'sweetalert-react'
import { EmptySolutionError } from './errors'
import {getLanguageDetail, postChallengeSolution, getChallengeSolution, getSolutionTests} from './requests.js'
import SelectionSearch from './semantic_ui_components/SelectionSearch.js'
import ChallengeTestsResults from './semantic_ui_components/ChallengeTestsResults.js'
import { themeOptions } from './editor_settings/editorSettings.js'
import { Button, Segment, Dimmer, Container } from 'semantic-ui-react'
import { divideCollectionIntoPieces } from './helpers.js'
import AceEditor from 'react-ace'
import 'brace/mode/javascript'
import 'brace/theme/monokai'
import 'brace/theme/terminal'
import 'brace/theme/github'
import 'brace/keybinding/vim'

class ChallengeBoard extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      code: '',
      selectedLanguage: '',
      selectedTheme: 'monokai',
      displayStyle: 'none',
      showRedBorder: '',
      showAlert: false,
      hasSubmitted: false,
      isGrading: false,
      loadedResults: false,
      gradedSolution: undefined,
      solutionResultsJSX: <div />
    }
    this.buildDescription = this.buildDescription.bind(this)
    this.onChange = this.onChange.bind(this)
    this.submitSolution = this.submitSolution.bind(this)
    this.langChangeHandler = this.langChangeHandler.bind(this)
    this.themeChangeHandler = this.themeChangeHandler.bind(this)
    this.getGradedSolution = this.getGradedSolution.bind(this)
    this.buildSolutionResults = this.buildSolutionResults.bind(this)
    this.displayLoadingTests = this.displayLoadingTests.bind(this)
    this.convertBold = this.parseTextIntoHTML.bind(this)
  }

  /**
   * Build the description JSX for the challenge
   */
  buildDescription () {
    let sampleInput = this.props.description.sample_input !== undefined && this.props.description.sample_input.length >= 1 ? (
      <div className='io-format'>
        <h3>Sample Input</h3>
        <div dangerouslySetInnerHTML={{__html: this.parseTextIntoHTML(this.props.description.sample_input)}} />
      </div>
    ) : (<div />)
    let sampleOutput = this.props.description.sample_output !== undefined && this.props.description.sample_output.length >= 1 ? (
      <div className='io-format'>
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
          <h3>Description:</h3>
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

  // Parses text into HTML, searching for certain placeholders like {{NPL}} and ** surroundings
  parseTextIntoHTML (str) {
    if (str === undefined) {
      return str
    }

    // a bold word markup is a word surrounded by **word**
    let re = /\*\*(:?.+?)\*\*/g
    let match
    let result

    while ((match = re.exec(str)) !== null) {
      let strToReplace = match[0]
      let replacer = `<strong class=variable-descriptor>${match[1]}</strong>`
      str = str.replace(strToReplace, replacer)
    }

    result = str.split('{{NPL}}').join('<br>')  // format new line placeholders

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

  onChange (newValue, e) {
    this.setState({code: newValue})
  }

  langChangeHandler (event, language) {
    let languageName = language.value
    getLanguageDetail(languageName).then(lang => {
      let defaultCode = lang.default_code
      this.setState({code: defaultCode})
    })
    this.setState({
      selectedLanguage: languageName,
      displayStyle: 'none',
      showRedBorder: ''
    })
  }

  themeChangeHandler (event, theme) {
    this.setState({selectedTheme: theme.value})
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
    if (this.state.selectedLanguage) {
      postChallengeSolution(this.props.id, this.state.code, this.state.selectedLanguage).then(submission => {
        this.setState({hasSubmitted: true, isGrading: true})

        this.displayLoadingTests()

        this.getGradedSolution(this.props.id, submission.id)  // start querying for the updated solution
      }).catch(err => {
        if (err instanceof EmptySolutionError) {
          this.setState({
            showAlert: true,
            alertDesc: err.message,
            alertTitle: err.title
          })
        }
        throw err
      })
    } else {
      this.setState({
        displayStyle: 'block',
        showRedBorder: '1px solid red'
      })
    }
  }

  render () {
    return (
      <Container>
        <div className='challenge-board'>
          {this.buildDescription()}
          <div className='editor-options'>
            <div className='lang-choice-select'>
              <span>Language</span>
              <div style={{color: 'red', display: this.state.displayStyle}}>Choose language</div>
              <SelectionSearch options={this.buildLanguageSelectOptions()} style={{border: this.state.showRedBorder}} placeholder='Select Language' onChange={this.langChangeHandler} />
            </div>
            <div className='theme-select'>
              <span>Theme</span>
              <SelectionSearch options={themeOptions} placeholder='Select Theme' onChange={this.themeChangeHandler} />
            </div>
          </div>
          <SweetAlert
            type='error'
            show={this.state.showAlert}
            title={this.state.alertTitle}
            text={this.state.alertDesc}
            onConfirm={() => this.setState({ showAlert: false })}
          />
          <AceEditor
            mode='javascript'
            keyboardHandler='vim'
            theme={this.state.selectedTheme}
            name='blah2'
            width='100%'
            value={this.state.code}
            fontSize={18}
            showPrintMargin
            showGutter
            highlightActiveLine
            setOptions={{
              enableBasicAutocompletion: true,
              enableLiveAutocompletion: true,
              enableSnippets: false,
              showLineNumbers: true,
              useWorker: false,
              tabSize: 2
            }} />
          <div className='submit-solution-btn'>
            <Button color='orange' onClick={this.submitSolution}>Submit solution</Button>
          </div>
          {this.state.solutionResultsJSX}
        </div>
      </Container>
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
  supported_languages: PropTypes.arrayOf(PropTypes.string),
  modifyScore: PropTypes.func.isRequired,
  userInfo: PropTypes.object
}

export default ChallengeBoard
