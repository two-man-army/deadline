import React from 'react'
import PropTypes from 'prop-types'

class SideBarNav extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    return (
      <aside className='side-nav'>
        <nav>
          <NavItem />
          <NavProfile />
        </nav>
      </aside>
    )
  }
}

export default SideBarNav
