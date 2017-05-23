import React from 'react'
import { getLatestAttemptedChallenges } from './requests.js'
import { Route, Switch } from 'react-router-dom'
import DashboardHeader from './semantic_ui_components/DashboardHeader'
import DisplayMetaInfo from './semantic_ui_components/DisplayMetaInfo'
import CategoryChallengeList from './CategoryChallengeList'
import ChallengeDetails from './ChallengeDetails'
import RouteNotFound from './RouteNotFound'
import Profile from './Profile'

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
            <DisplayMetaInfo key={challenge.id} {...challenge} userScore={challenge.user_max_score} />
          )
        })}
      </div>
    )
  }

  render () {
    return (
      <div className='dashboard'>
        <DashboardHeader />
        <Switch>
          <Route exact path='/' render={() => { return this.getDefaultDashboardDOM() }} />
          <Route exact path='/categories/:category' component={CategoryChallengeList} />
          <Route exact path='/challenges/:challengeId' component={ChallengeDetails} />
          <Route exact path='/accounts/password/change' component={Profile} />
          <Route exact path='/accounts/edit' component={Profile} />
          <Route path='*' component={RouteNotFound} />
        </Switch>
      </div>
    )
  }
}

export default Dashboard
