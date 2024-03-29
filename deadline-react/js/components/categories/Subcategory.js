import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import CategoryHeader from './CategoryHeader'
import SubcategoryOverlay from './SubcategoryOverlay'

const Subcategory = ({
  url,
  name,
  proficiency,
  solvedChallenges,
  challengeCount,
  percentageCompleted,
  expToNextProficiency,
  nextProficiency,
  onClick
  }) => (
    <li data-subcategory-name={name} className='subcategory' onClick={onClick}>
      <Link to={{pathname: url}}>
        <section>
          <CategoryHeader name={name} />
          <div className='category-info'>
            <div className='proficiency'>
              {proficiency}
            </div>
            <div className='completed-challenges'>
              <div className='challenges-progress'>
                {solvedChallenges}/{challengeCount}
              </div>
              <div className='status-text'>Completed</div>
            </div>
          </div>
          <SubcategoryOverlay
            percentageCompleted={percentageCompleted}
            expToNextProficiency={expToNextProficiency}
            nextProficiency={nextProficiency} />
        </section>
      </Link>
    </li>
)

Subcategory.propTypes = {
  url: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  proficiency: PropTypes.string.isRequired,
  solvedChallenges: PropTypes.number.isRequired,
  challengeCount: PropTypes.number.isRequired,
  percentageCompleted: PropTypes.string.isRequired,
  expToNextProficiency: PropTypes.number.isRequired,
  nextProficiency: PropTypes.string.isRquired,
  onClick: PropTypes.func.isRquired
}

export default Subcategory
