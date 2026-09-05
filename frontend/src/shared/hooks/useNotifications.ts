import { useState, useEffect } from 'react';

export interface Notification {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  message: string;
  status: 'pending' | 'read' | 'failed';
  created_at: string;
  metadata?: Record<string, any>;
}

export interface AlertNotification extends Notification {
  alert_id: string;
  severity: string;
}

export interface ReminderNotification extends Notification {
  reminder_id: string;
  reminder_type: string;
}

export const useNotifications = (userId: string, token: string | null) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!token) return;

    const fetchNotifications = async () => {
      try {
        const response = await fetch('/api/v1/notifications?status=pending', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();
        setNotifications(data);
        setUnreadCount(data.filter((n: Notification) => n.status !== 'read').length);
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [token, userId]);

  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications(prev =>
        prev.map(n => (n.id === notificationId ? { ...n, status: 'read' as const } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  return { notifications, unreadCount, markAsRead };
};
