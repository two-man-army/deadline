/**
 * The specific Challenge page with the description of the problem and the
 *  code editor for submission
 */
import React from 'react'
import PropTypes from 'prop-types'
import MonacoEditor from 'react-monaco-editor'
import {postChallengeSolution} from './requests.js'
import SelectionSearch from './semantic_ui_components/SelectionSearch.js'

class ChallengeBoard extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      code: '',  // TODO: Load sample code
      chosenLanguage: 'Python'  // TODO: Change with drop down
    }
    this.buildDescription = this.buildDescription.bind(this)
    this.onChange = this.onChange.bind(this)
    this.editorDidMount = this.editorDidMount.bind(this)
    this.submitSolution = this.submitSolution.bind(this)
    this.langChangeHandler = this.langChangeHandler.bind(this)
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

  submitSolution () {
    console.log('Submitting challenge')
    postChallengeSolution(this.props.id, this.state.code, this.state.chosenLanguage).then(submission => {
      console.log(submission)
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
        <script src={'/node_modules/monaco-editor/min/vs/loader.js'} />
      </div>
    )
  }
}

ChallengeBoard.propTypes = {
  id: PropTypes.number,
  name: PropTypes.string,
  rating: PropTypes.number,
  score: PropTypes.number,
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
  category: PropTypes.string,
  supported_languages: PropTypes.arrayOf(PropTypes.string)
}

export default ChallengeBoard
