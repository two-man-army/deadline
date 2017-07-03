import React from 'react'
import Activity from './Activity'

class ActivityFeed extends React.Component {
  render () {
    return (
      <section className='activity-feed main'>
        <h2 className='activity-feed-header'>Activity Feed</h2>
        <ul>
          <Activity
            className='username'
            name='Ben Foster'
            path='assets/img/sidebar/profile.png'
            msg='Became Rookie in Dynamic Programming' />
          <Activity
            className='username'
            name='Linn Davis'
            path='assets/img/sidebar/profile.png'
            msg='Complited Basic Number challenge and earned 20 points' />
          <Activity
            className='username'
            name='Rick Hase'
            path='assets/img/sidebar/profile.png'
            msg='Earned the title Python Developer' />
          <Activity
            className='username'
            name='Rick Hase'
            path='assets/img/sidebar/profile.png'
            msg='Earned the title Python Developer' />
          <Activity
            className='username'
            name='Rick Hase'
            path='assets/img/sidebar/profile.png'
            msg='Earned the title Python Developer' />
          <Activity
            className='username'
            name='Rick Hase'
            path='assets/img/sidebar/profile.png'
            msg='Earned the title Python Developer' />
          <Activity
            className='username'
            name='Rick Hase'
            path='assets/img/sidebar/profile.png'
            msg='Earned the title Python Developer' />
        </ul>
      </section>
    )
  }
}

export default ActivityFeed
