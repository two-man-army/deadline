import React from 'react'
import ChatButton from './ChatButton'

const ChatMsgBox = (props) => (
  <div className='chatbox'>
    <form className='chatbox__form' action=''>
      <textarea name='ChatMsgBox' id='msg-box-area' className='chatbox__area' cols='30' rows='10' placeholder='Write message...' />
    </form>
    <ChatButton />
  </div>
)

export default ChatMsgBox
