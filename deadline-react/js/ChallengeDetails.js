import React from 'react'
import PropTypes from 'prop-types'
import Tabs from 'react-tabs-navigation'
import {getChallengeDetails} from './requests.js'
import ChallengeBoard from './ChallengeBoard.js'

class ChallengeDetails extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      id: undefined,
      name: undefined,
      rating: undefined,
      score: undefined,
      description: {
        content: undefined,
        input_format: undefined,
        output_format: undefined,
        constraints: undefined,
        sample_input: undefined,
        sample_output: undefined,
        explanation: undefined
      },
      test_case_count: undefined,
      category: undefined,
      supported_languages: []
    }

    this.loadChallengeDetails = this.loadChallengeDetails.bind(this)
    this.loadChallengeDetails()
  }

  loadChallengeDetails () {
    getChallengeDetails(this.props.match.params.challengeId).then(challenge => {
      this.setState(challenge)
    }).catch(err => {
      throw err  // TODO: handle
    })
  }

  render () {
    return (
      <Tabs
        banner={{
          children: this.state.name
        }}
        tabs={[
          {
            children: () => (
              <ChallengeBoard {...this.state} />
            ),
            displayName: 'Challenge'
          },
          {
            children: () => (
              <div>
                This is the second tab content
              </div>
            ),
            displayName: 'Submissions'
          },
          {
            children: () => (
              <div>
                This is the second tab content
              </div>
            ),
            displayName: 'Leaderboard'
          }
        ]}
      />
    )
  }
}

ChallengeDetails.propTypes = {
  match: PropTypes.shape({
    params: PropTypes.shape({
      challengeId: PropTypes.string.isRequired
    })
  })
}

export default ChallengeDetails
