import React from 'react'
import Button from '../Button'

const ChatMsgBox = (props) => (
  <div className='chatbox'>
    <form className='chatbox__form' action=''>
      <textarea name='ChatMsgBox' id='msg-box-area' className='chatbox__area' cols='30' rows='10' placeholder='Write message...' />
    </form>
    <Button text='SEND' />
  </div>
)

export default ChatMsgBox
