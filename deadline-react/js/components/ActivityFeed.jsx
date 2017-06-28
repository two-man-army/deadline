import React from 'react'
import PropTypes from 'prop-types'
import Activity from 'Activity'

class ActivityFeed extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    return (
      <section className='activity-feed'>
        <h2>Activity Feed</h2>
        <Activity />
        <Activity />
        <Activity />
      </section>
    )
  }
}

export default ActivityFeed
