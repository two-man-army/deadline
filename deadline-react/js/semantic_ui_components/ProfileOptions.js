import React from 'react'
import { Button, Modal, Image, Header } from 'semantic-ui-react'
import OptionsList from './OptionsList'

const ProfileOptions = () => (
  <Modal
    dimmer='blurring'
    trigger={<img src='/assets/img/avatar.jpg' />}>
    <Modal.Header>Select a Photo</Modal.Header>
    <Modal.Content image>
      <Image wrapped size='medium' src='/assets/img/avatar.jpg' />
      <Modal.Description>
        <Header>Draft. Additional styles and logic should be applied. Probably material ui List will be more handy</Header>
        <OptionsList />
      </Modal.Description>
    </Modal.Content>
    <Modal.Actions>
      <Button positive icon='checkmark' labelPosition='right' content='Cancel/Go?' />
    </Modal.Actions>
  </Modal>
)

export default ProfileOptions
