import React from 'react'
import { List } from 'semantic-ui-react'

const OptionsList = () => (
  <List link>
    <List.Item as='a'>Edit Profile</List.Item>
    <List.Item as='a'>Change Password</List.Item>
    <List.Item as='a'>Log Out</List.Item>
    <List.Item as='a'>Cancel</List.Item>
  </List>
)

export default OptionsList
