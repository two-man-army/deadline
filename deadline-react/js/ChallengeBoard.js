/**
 * The specific Challenge page with the description of the problem and the
 *  code editor for submission
 */
import React from 'react'
import PropTypes from 'prop-types'
import MonacoEditor from 'react-monaco-editor'
import {postChallengeSolution} from './requests.js'


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

  editorDidMount (editor, monaco) {
    console.log('editorDidMount', editor)
    editor.focus()
  }

  onChange (newValue, e) {
    console.log('onChange', newValue, e)
    this.setState({code: newValue})
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
