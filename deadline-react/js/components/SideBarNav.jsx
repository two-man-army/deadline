import React from 'react'
import PropTypes from 'prop-types'

class SideBarNav extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    return (
      <nav className='side-nav'>
        <NavItem />
        <NavProfile />
      </nav>
    )
  }
}

export default SideBarNav
