import React from 'react'
import ChatHeader from './ChatHeader'
import ChatFriendMsg from './ChatFriendMsg'
import ChatMyMsg from './ChatMyMsg'

const ChatWindow = () => (
  <section className='chat-window'>
    <ChatHeader heading='Freind Name' />
    <ChatFriendMsg date='12/05/1993' path='assets/img/pikachu.svg' msg='Lorem ipsum dolor sit amet, consectetur adipiscing elit.' />
    <ChatMyMsg msg='Lorem ipsum dolor sit amet, consectetur adipiscing elit.' />
    <ChatFriendMsg date='12/05/1993' path='assets/img/pikachu.svg' msg='Lorem ipsum dolor sit amet, consectetur adipiscing elit.' />
    <ChatMyMsg msg='Lorem ipsum dolor sit amet, consectetur adipiscing elit.' />
    <ChatMyMsg msg='Lorem ipsum dolor sit amet, consectetur adipiscing elit. consectetur adipiscing elit. consectetur adipiscing elit. consectetur adipiscing elit. consectetur adipiscing elit.' />
    <ChatFriendMsg date='12/05/1993' path='assets/img/pikachu.svg' msg='Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elitLorem ipsum dolor sit amet, consectetur adipiscing elitLorem ipsum dolor sit amet, consectetur adipiscing elitLorem ipsum dolor sit amet, consectetur adipiscing elitLorem ipsum dolor sit amet, consectetur adipiscing elit' />
  </section>
)

export default ChatWindow
