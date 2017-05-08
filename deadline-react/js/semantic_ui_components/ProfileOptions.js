import React from 'react'
import { Button, Modal, Image } from 'semantic-ui-react'
import OptionsList from './OptionsList'

class ProfileOptions extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      open: false
    }

    this.handleClose = this.handleClose.bind(this)
    this.handleOpen = this.handleOpen.bind(this)
  }

  handleOpen () {
    this.setState({open: true})
  }

  handleClose () {
    this.setState({open: false})
  }

  render () {
    return (
      <div>
        <img src='/assets/img/avatar.jpg' onClick={this.handleOpen} />
        <Modal
          dimmer='blurring'
          open={this.state.open}>
          <Modal.Header>Select a Photo</Modal.Header>
          <Modal.Content image>
            <Image wrapped size='medium' src='/assets/img/avatar.jpg' />
            <Modal.Description className='account-dialog'>
              <OptionsList />
            </Modal.Description>
          </Modal.Content>
          <Modal.Actions>
            <Button secondary content='Cancel' onClick={this.handleClose} />
          </Modal.Actions>
        </Modal>
      </div>
    )
  }
}

export default ProfileOptions
