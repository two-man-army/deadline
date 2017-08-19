import React from 'react'
import { getLatestAttemptedChallenges } from './requests.js'
import { Route, Switch } from 'react-router-dom'
import Header from './components/Header'
import FollowSuggestions from './components/FollowSuggestions'
import RanklistBox from './components/ranklist/RanklistBox'
import SubcategoriesPage from './components/categories/SubcategoriesPage'
import ActivityFeed from './components/newsfeed/ActivityFeed'
import DisplayMetaInfo from './semantic_ui_components/DisplayMetaInfo'
import SidebarNav from './components/SidebarNav'
import CategoryPage from './components/categories/CategoryPage'
import ChallengeDetails from './ChallengeDetails'
import OverallLeaderboard from './semantic_ui_components/OverallLeaderboardTable'
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
    // this.loadLatestAttemptedChallenges()
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
      <main className='main'>
        <div>
          {this.state.challenges.map(challenge => {
            return (
              <DisplayMetaInfo key={challenge.id} {...challenge} userScore={challenge.user_max_score} />
            )
          })}
        </div>
      </main>
    )
  }

  render () {
    return (
      // <Route exact path='/categories/:category' component={CategoryChallengeList} />
      <div>
        <Header />
        <section className='dashboard'>
          <div className='columns'>
            <SidebarNav />
            <Switch>
              <Route exact path='/' component={ActivityFeed} />
              <Route exact path='/leaderboard' component={OverallLeaderboard} />
              <Route exact path='/categories' component={CategoryPage} />
              <Route exact path='/categories/:subcategory' component={SubcategoriesPage} />
              <Route exact path='/challenges/:challengeId' component={ChallengeDetails} />
              <Route exact path='/accounts/password/change' component={Profile} />
              <Route exact path='/accounts/edit' component={Profile} />
              <Route path='*' component={RouteNotFound} />
            </Switch>
            <aside className='right-sidebar'>
              <FollowSuggestions />
              <RanklistBox />
            </aside>
          </div>
        </section>
      </div>
    )
  }
}

export default Dashboard
