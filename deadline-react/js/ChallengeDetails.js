import React from 'react'
import PropTypes from 'prop-types'
import Tabs from 'react-tabs-navigation'
import {getTopSolutions, getChallengeDetails, getAllUserSolutions} from './requests.js'
import ChallengeBoard from './ChallengeBoard.js'
import SubmissionsTable from './semantic_ui_components/SubmissionsTable.js'
import LeaderboardTable from './semantic_ui_components/LeaderboardTable.js'
import { Container } from 'semantic-ui-react'

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
      supported_languages: [],
      solutions: []
    }

    this.loadChallengeDetails = this.loadChallengeDetails.bind(this)
    this.loadTopSubmissions = this.loadTopSubmissions.bind(this)
    this.loadChallengeDetails()
  }

  loadChallengeDetails () {
    getChallengeDetails(this.props.match.params.challengeId).then(challenge => {
      this.setState(challenge)
      this.loadSubmissions(challenge.id)
    }).catch(err => {
      throw err  // TODO: handle
    })
  }

  loadSubmissions (challengeId) {
    getAllUserSolutions(challengeId).then(solutions => {
      this.setState({solutions})
      this.loadTopSubmissions(challengeId)
    }).catch(err => {
      throw err
    })
  }

  loadTopSubmissions (challengeId) {
    getTopSolutions(challengeId).then(solutions => {
      this.setState({topSolutions: solutions})
    }).catch(err => {
      throw err
    })
  }

  render () {
    return (
      <Container>
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
                <SubmissionsTable maxScore={this.state.score} submissions={this.state.solutions} />
              ),
              displayName: 'Submissions'
            },
            {
              children: () => (
                <LeaderboardTable maxScore={this.state.score} submissions={this.state.topSolutions} />
              ),
              displayName: 'Leaderboard'
            }
          ]}
        />
      </Container>
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
