import json
from django.contrib.auth import get_user_model
import asyncio
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self,event):
        #Allow us to have websocket connected to consumer
        print("Connected",event)
        
        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']
        #print(other_user,me)
        thread_obj = await self.get_thread(me, other_user)
        self.thread_obj = thread_obj
        chat_room = "thread_{}".format(thread_obj.id)
        self.chat_room = chat_room
        await self.channel_layer.group_add(
                chat_room,
                self.channel_name
            )
        
        await self.send({
                "type": "websocket.accept"
            })
        #await asyncio.sleep(10)
        """
        await self.send({
                "type": "websocket.close"
            })
        await self.send({
                "type": "websocket.send",
                "text": "Hello world"
            })
        """
        
    async def websocket_receive(self,event):
        #When message is received from websocket
        print("Received",event)
        front_text = event.get('text',None)
        if front_text is not None:
            loaded_dict_data = json.loads(front_text)
            msg = loaded_dict_data.get('message')
            user = self.scope['user']
            username = 'default'
            if user.is_authenticated:
                username = user.username
                
            myResponse = {
                    'message': msg,
                    'username': username
                }
            await self.create_chat_message(msg)
            # Broadcast the message event to be sent
            await self.channel_layer.group_send(
                self.chat_room,
                {
                    "type":"chat_message",
                    "text": json.dumps(myResponse)
                }   
            )
        #Received {'type': 'websocket.receive', 'text': '{"message":"another"}'}
        
        
    async def chat_message(self,event):
        # Send the actual message
        print('message',event)
        await self.send({
                "type": "websocket.send",
                "text": event['text']
            })
        
    async def websocket_disconnect(self,event):
        #When the socket connects
        print("Disconnected", event)
        
    @database_sync_to_async
    def get_thread(self, user, other_username):
        return Thread.objects.get_or_new(user, other_username)[0]
    
    @database_sync_to_async
    def create_chat_message(self, msg):
        thread_obj = self.thread_obj
        me = self.scope['user']
        return ChatMessage.objects.create(thread=thread_obj, user=me, message=me)