import React from 'react'
import RanklistBoxRow from './RanklistBoxRow'
import { getOverallLeaderboard } from '../../requests.js'

class RanklistBox extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      users: []
    }

    this.loadUsers = this.loadUsers.bind(this)
    this.loadUsers()
  }

  // TODO: Load only say 10 users
  loadUsers () {
    getOverallLeaderboard().then(users => {
      this.setState({users})
    })
  }

  render () {
    return (
      <section className='ranklist'>
        <div className='ranklist-box-header'>
          <h4>Ranklist</h4>
          <div>
            <span className='users-to-follow'>The Users You Follow</span>
            <span className='all-users'>All Users</span>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>USER</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {this.state.users.map((user, idx) => (
              <RanklistBoxRow name={user.name} position={user.position} score={user.score} key={idx} />
            ))}
          </tbody>
        </table>
      </section>
    )
  }
}

export default RanklistBox
