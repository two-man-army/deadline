import React from 'react'
import { Icon } from 'semantic-ui-react'

const RouteNotFound = () => (
  <div className='page-not-found'>
    <Icon name='warning sign' size='huge' />
    <h3>404 page not found</h3>
    <p>We are sorry but the page you are looking for does not exist!</p>
  </div>
)

export default RouteNotFound
