import React from 'react'
import PropTypes from 'prop-types'
import TimeAgo from 'react-timeago'

const Activity = ({name, lvl, description}) => (
  <section className='activity'>
    <div className='activity-content>
      <h3>{name}</h3>
      <img src="" alt="">
      <p className='level'>Lvl: {lvl}</p>
      <p className='description'>{description}</p>
    </div>
    <div className="activity-timeago">
      <TimeAgo date={submission.created_at} />
    </div>
  </section>
)

export default Activity
