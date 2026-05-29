import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_id = user.id
        self.group_name = f"notifications_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # On connect: send unread notifications snapshot
        unread = await self._get_unread()
        await self.send(text_data=json.dumps({
            'type': 'snapshot',
            'unread_count': len(unread),
            'notifications': [self._serialize(n) for n in unread],
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except Exception:
            return

        msg_type = payload.get('type')
        if msg_type == 'mark_all_read':
            await self._mark_all_read()
            unread = await self._get_unread()
            await self.send(text_data=json.dumps({
                'type': 'snapshot',
                'unread_count': len(unread),
                'notifications': [self._serialize(n) for n in unread],
            }))
        elif msg_type == 'mark_read':
            notification_id = payload.get('notification_id')
            if notification_id is not None:
                await self._mark_read(notification_id)
                unread = await self._get_unread()
                await self.send(text_data=json.dumps({
                    'type': 'snapshot',
                    'unread_count': len(unread),
                    'notifications': [self._serialize(n) for n in unread],
                }))

    async def notify(self, event):
        """Handler for events sent to the user group."""
        notification = event.get('notification')
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification,
            'unread_count': event.get('unread_count', 0),
        }))

    @database_sync_to_async
    def _get_unread(self):
        return list(Notification.objects.filter(recipient_id=self.user_id, is_read=False).order_by('-created_at')[:20])

    @database_sync_to_async
    def _mark_all_read(self):
        Notification.objects.filter(recipient_id=self.user_id, is_read=False).update(is_read=True)

    @database_sync_to_async
    def _mark_read(self, notification_id):
        Notification.objects.filter(recipient_id=self.user_id, id=notification_id).update(is_read=True)

    def _serialize(self, n: Notification):
        return {
            'id': n.id,
            'recipient': n.recipient_id,
            'sender': n.sender_id,
            'message': n.message,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'notification_type': n.notification_type,
            'project_id': getattr(n.project, 'id', None) if n.project_id else None,
            'task_id': getattr(n.task, 'id', None) if n.task_id else None,
        }

