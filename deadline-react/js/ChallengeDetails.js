import React from 'react'
import PropTypes from 'prop-types'
import { Tabs } from 'antd'
import {getSelfUserTopSubmission, getTopSolutions, getChallengeDetails, getAllUserSolutions} from './requests.js'
import ChallengeBoard from './ChallengeBoard.js'
import SubmissionsTable from './semantic_ui_components/SubmissionsTable.js'
import LeaderboardTable from './semantic_ui_components/LeaderboardTable.js'
import { Container } from 'semantic-ui-react'

const TabPane = Tabs.TabPane

class ChallengeDetails extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      id: undefined,
      name: undefined,
      difficulty: undefined,
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
      solutions: [],
      topSolutions: [],
      slideIndex: 0,
      userInfo: {maxScore: 0}
    }
    // TODO: Load user Max Score for challenge
    this.loadChallengeDetails = this.loadChallengeDetails.bind(this)
    this.loadTopSubmissions = this.loadTopSubmissions.bind(this)
    this.handleTabChange = this.handleTabChange.bind(this)
    this.modifyScore = this.modifyScore.bind(this)
    this.loadChallengeDetails()
  }

  loadChallengeDetails () {
    getChallengeDetails(this.props.match.params.challengeId).then(challenge => {
      this.setState(challenge)
      getSelfUserTopSubmission(challenge.id).then(topSubmission => {
        this.modifyScore(topSubmission.result_score || 0)
      }).catch(err => {
        throw err
      })
      this.loadSubmissions(challenge.id)
      this.loadTopSubmissions(challenge.id)
    }).catch(err => {
      throw err  // TODO: handle
    })
  }

  loadSubmissions (challengeId) {
    getAllUserSolutions(challengeId).then(solutions => {
      this.setState({solutions})
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

  handleTabChange (value, e) {
    this.setState({
      slideIndex: value
    })
  }

  modifyScore (newScore) {
    if (newScore > this.state.userInfo.maxScore) {
      this.setState({userInfo: {maxScore: newScore}})
    }
  }

  render () {
    return (
      <div className='main challenge-details'>
        <Container>
          <h1 className='challenge-name'>{this.state.name}</h1>
          <Tabs defaultActiveKey='1'>
            <TabPane tab='CHALLENGE' key='1'>
              <ChallengeBoard {...this.state} userInfo={this.state.userInfo} modifyScore={this.modifyScore} />
            </TabPane>
            <TabPane tab='SUBMISSIONS' key='2'>
              <SubmissionsTable maxScore={this.state.score} submissions={this.state.solutions} />
            </TabPane>
            <TabPane tab='LEADERBOARD' key='3'>
              <LeaderboardTable maxScore={this.state.score} submissions={this.state.topSolutions} hasUnlockedSubmissions={this.state.userInfo.maxScore === this.state.score && this.state.score !== undefined} />
            </TabPane>
          </Tabs>
        </Container>
      </div>
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
