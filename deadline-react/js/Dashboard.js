import React from 'react'
import { getLatestAttemptedChallenges } from './requests.js'
import { Route, Switch } from 'react-router-dom'
import ChallengeMetaInfo from './ChallengeMetaInfo.js'
import CategoryChallengeList from './CategoryChallengeList.js'
import ChallengeDetails from './ChallengeDetails.js'

class Dashboard extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      challenges: []
    }

    this.loadLatestAttemptedChallenges = this.loadLatestAttemptedChallenges.bind(this)
    this.getDefaultDashboardDOM = this.getDefaultDashboardDOM.bind(this)
    this.loadLatestAttemptedChallenges()
  }

  loadLatestAttemptedChallenges () {
    getLatestAttemptedChallenges().then(challenges => {
      this.setState({challenges})
    }).catch(err => {
      // TODO: Handle
      throw err
    })
  }

  /**
   * The default dashboard simply shows the latest attempted challenges by the user
   */
  getDefaultDashboardDOM () {
    return (
      <div>
        {this.state.challenges.map(challenge => {
          return (
            <ChallengeMetaInfo {...challenge} />
          )
        })}
      </div>
    )
  }

  render () {
    return (
      <div className='dashboard'>
        <Switch>
          <Route exact path='/' render={() => { return this.getDefaultDashboardDOM() }} />
          <Route exact path='/categories/:category' component={CategoryChallengeList} />
          <Route exact path='/challenges/:challengeId' component={ChallengeDetails} />
        </Switch>
      </div>
    )
  }
}

export default Dashboard
