import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors, layout, spacing, typography, shadows, radius } from '../../constants/theme';
import { Card } from './Card';
import { Button } from './Button';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface ChatMessage {
  id: string;
  user_id: string;
  package_id: string;
  agent_id: string;
  message: string;
  sender_type: 'user' | 'agent';
  timestamp: string;
  is_read: boolean;
}

interface Package {
  id: string;
  title: string;
  agent_id: string;
  price: number;
  destination: string;
  duration: string;
}

interface ChatModalProps {
  visible: boolean;
  onClose: () => void;
  package: Package | null;
  agentName: string;
}

export const ChatModal: React.FC<ChatModalProps> = ({
  visible,
  onClose,
  package: selectedPackage,
  agentName,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (visible && selectedPackage) {
      loadMessages();
    }
  }, [visible, selectedPackage]);

  const loadMessages = async () => {
    if (!selectedPackage) return;
    
    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/chat/${selectedPackage.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const chatMessages = await response.json();
        setMessages(chatMessages);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedPackage) return;

    setSending(true);
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          package_id: selectedPackage.id,
          message: newMessage.trim(),
        }),
      });

      if (response.ok) {
        setNewMessage('');
        loadMessages(); // Reload messages to show the new one
      } else {
        Alert.alert('Error', 'Failed to send message. Please try again.');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.sender_type === 'user';
    
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.agentMessageContainer,
        ]}
      >
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.userMessageBubble : styles.agentMessageBubble,
          ]}
        >
          <Text style={[
            styles.messageText,
            isUser ? styles.userMessageText : styles.agentMessageText,
          ]}>
            {message.message}
          </Text>
        </View>
        <Text style={[
          styles.messageTime,
          isUser ? styles.userMessageTime : styles.agentMessageTime,
        ]}>
          {formatTime(message.timestamp)}
        </Text>
      </View>
    );
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerInfo}>
            <Text style={styles.agentName}>{agentName}</Text>
            {selectedPackage && (
              <Text style={styles.packageTitle}>{selectedPackage.title}</Text>
            )}
          </View>
        </View>

        {/* Package Info */}
        {selectedPackage && (
          <Card style={styles.packageCard}>
            <Text style={styles.packageName}>{selectedPackage.title}</Text>
            <Text style={styles.packageDetails}>
              {selectedPackage.destination} • {selectedPackage.duration} • ₹{selectedPackage.price}
            </Text>
          </Card>
        )}

        {/* Messages */}
        <ScrollView style={styles.messagesContainer} showsVerticalScrollIndicator={false}>
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={styles.loadingText}>Loading messages...</Text>
            </View>
          ) : messages.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No messages yet.</Text>
              <Text style={styles.emptySubtext}>Start a conversation about this package!</Text>
            </View>
          ) : (
            messages.map((message, index) => renderMessage(message, index))
          )}
        </ScrollView>

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.messageInput}
            placeholder="Type your message..."
            placeholderTextColor={colors.textSecondary}
            value={newMessage}
            onChangeText={setNewMessage}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[styles.sendButton, (!newMessage.trim() || sending) && styles.sendButtonDisabled]}
            onPress={sendMessage}
            disabled={!newMessage.trim() || sending}
          >
            <Text style={[styles.sendButtonText, (!newMessage.trim() || sending) && styles.sendButtonTextDisabled]}>
              {sending ? '...' : 'Send'}
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.primaryLight,
    ...shadows.small,
  },
  closeButton: {
    padding: spacing.xs,
    marginRight: spacing.sm,
  },
  closeButtonText: {
    fontSize: 24,
    color: colors.primary,
    fontWeight: 'bold',
  },
  headerInfo: {
    flex: 1,
  },
  agentName: {
    ...typography.h4,
    color: colors.primary,
  },
  packageTitle: {
    ...typography.body2,
    color: colors.textSecondary,
    marginTop: spacing.xs / 2,
  },
  packageCard: {
    margin: spacing.md,
    marginBottom: spacing.sm,
  },
  packageName: {
    ...typography.body1,
    fontWeight: 'bold',
    marginBottom: spacing.xs,
  },
  packageDetails: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: spacing.md,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  loadingText: {
    ...typography.body2,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  emptyText: {
    ...typography.h4,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  emptySubtext: {
    ...typography.body2,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  messageContainer: {
    marginVertical: spacing.xs,
  },
  userMessageContainer: {
    alignItems: 'flex-end',
  },
  agentMessageContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.lg,
  },
  userMessageBubble: {
    backgroundColor: colors.primary,
  },
  agentMessageBubble: {
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.primaryLight,
  },
  messageText: {
    ...typography.body1,
  },
  userMessageText: {
    color: colors.textLight,
  },
  agentMessageText: {
    color: colors.text,
  },
  messageTime: {
    ...typography.caption,
    marginTop: spacing.xs / 2,
    marginHorizontal: spacing.sm,
  },
  userMessageTime: {
    color: colors.textSecondary,
    textAlign: 'right',
  },
  agentMessageTime: {
    color: colors.textSecondary,
    textAlign: 'left',
  },
  inputContainer: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.primaryLight,
    alignItems: 'flex-end',
  },
  messageInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.primaryLight,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginRight: spacing.sm,
    maxHeight: 100,
    ...typography.body1,
    backgroundColor: colors.background,
  },
  sendButton: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md + 4,
    paddingVertical: spacing.sm + 2,
    justifyContent: 'center',
    minHeight: 44,
  },
  sendButtonDisabled: {
    backgroundColor: colors.textSecondary,
    opacity: 0.6,
  },
  sendButtonText: {
    ...typography.button,
    color: colors.textLight,
  },
  sendButtonTextDisabled: {
    color: colors.textLight,
  },
});