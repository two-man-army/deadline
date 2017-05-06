/** A Select component with icons and seach functionality */
import React from 'react'
import PropTypes from 'prop-types'
import { Dropdown } from 'semantic-ui-react'

// options = [ { key: 'af', value: 'af', flag: 'af', text: 'Afghanistan',  image: { avatar: true, src: '/assets/images/avatar/small/jenny.jpg' } }, ...  ]

const SelectionSearch = ({options, placeholder, onChange}) => (
  <Dropdown placeholder={placeholder} fluid search selection options={options} onChange={onChange} />
)

SelectionSearch.propTypes = {
  options: PropTypes.func,
  placeholder: PropTypes.string,
  onChange: PropTypes.func
}

export default SelectionSearch
