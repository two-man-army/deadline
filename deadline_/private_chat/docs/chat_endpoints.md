Initiating a chat/conversation is simple.

# Initiating a chat and sending a message

## Connecting
First, you need to connect to the right URL, which would be something like
 
ws://localhost:5002/chat/your_id/your_opponent_id

So, if we were Mark with ID 1 and we wanted to connect to Sam with ID 2, the url would be

ws://localhost:5002/chat/1/2


## Authenticating
At this point, the server cannot trust that you are user with ID 1, as you have not proved it in any way.
To prove this and have your websocket marked as valid, you need to send a special message of type
'fetch-token'. This message must contain the following

```json
{
    "type": "fetch-token",
    "user_id": 1,
    "auth_token": "YOUR_AUTH_TOKEN_HERE",
    "opponent_id": 2
}
```
This will return 
```json
{
"type": "conversation-token",
"conversation_token": "YOUR_TOKEN"
}
```
You should save this token, as you will always need to send it while sending a message, confirming to the server you are who you claim to be.
Note: This token will expire from time to time and you will need to fetch another one.

Sending a message is done in the following way:
```json
{
    "type": "new-message",
    "message": "Hello Sam",
    "user_id": 1,
    "opponent_id": 2,
    "conversation_token": "YOUR_TOKEN"
}
```

When you send a message (or receive one for that matter) you will always receive it back from the server, confirming it was sent:
```json
{
    "type": "received-message",
    "created": "Some date here",
    "sender_name": "Mark",
    "message": "Hello Sam",
    "id": 123
}
```

# Other Types of Messages

### Online check
When you authenticate and when your opponent comes online/goes offline you will receive a message indicating that, in the form of
```json
{"type": "online-check", "is_online": false}
```


### Typing
When your client starts typing, you need to send a message indicating that to the other user
```json
{
    "type": "is-typing",
    "conversation_token": "YOUR_TOKEN",
    "user_id": 1,
    "opponent_id": 2
}
```
Vice versa, when your opponent starts typing you will receive the following message:
```
{"type": "opponent-typing"}
```

### Errors
You can receive multiple kind of errors, regarding on the problem that has arisen with your request.
The most common one would be that of an expired conversation_token, prompting you to fetch a new one
```json
{
    "type": "error",
    "error_type": "EXPIRED_CONVERSATION_TOKEN",
    "message": "Invalid conversation_token. Fetch a new one!"
}
```