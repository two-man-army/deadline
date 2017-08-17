import React from 'react'
import PropTypes from 'prop-types'

const SubcategoryOverlay = ({
  percentageCompleted,
  expToNextProficiency,
  nextProficiency
}) => (
  <div className='category-overlay'>
    <div className='align-center next-proficiency-exp'>
      {expToNextProficiency} exp
      <p className='next-proficiency-title'>to {nextProficiency}</p>
    </div>
    <div className='align-center'>
      <div className='challenges-progress'>
        {percentageCompleted}%
      </div>
      <div className='status-text'>Completed</div>
    </div>
  </div>
)

SubcategoryOverlay.propTypes = {
  percentageCompleted: PropTypes.string.isRequired,
  expToNextProficiency: PropTypes.number.isRequired,
  nextProficiency: PropTypes.string.isRquired
}

export default SubcategoryOverlay
