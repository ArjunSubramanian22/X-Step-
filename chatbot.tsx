import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Send, Bot, User } from 'lucide-react-native';
import { useSensor } from '../../contexts/SensorContext';
import { useHealth } from '../../contexts/HealthContext';
import { useTodo } from '../../contexts/TodoContext';
import { createRorkTool, useRorkAgent } from '@rork/toolkit-sdk';
import { z } from 'zod';
import Colors from '../../constants/colors';



export default function ChatbotScreen() {
  const { isDarkMode, footData, calculateRiskScore } = useSensor();
  const { medicalRecord, healthIndex } = useHealth();
  const { todayTasks, addTask } = useTodo();
  const [input, setInput] = useState<string>('');
  const scrollRef = useRef<ScrollView>(null);
  const colors = isDarkMode ? Colors.dark : Colors.light;
  const insets = useSafeAreaInsets();

  const riskScore = calculateRiskScore();
  const maxPressure = Math.max(
    ...Object.values(footData.left).map(r => r.pressure),
    ...Object.values(footData.right).map(r => r.pressure)
  );
  const completedTasks = todayTasks.filter(t => t.completed).length;
  const totalTasks = todayTasks.length;

  const systemContext = `You are StepMate, a helpful AI assistant for diabetic foot care. Here's the current patient context:

Medical Info:
- HbA1c: ${medicalRecord.hba1c}% (Last checked: ${medicalRecord.lastHba1cDate})
- Neuropathy Status: ${medicalRecord.neuropathyStatus}
- Active foot ulcers: ${medicalRecord.hasFootUlcers ? 'Yes' : 'No'}
- Ulcer History: ${medicalRecord.ulcerHistory.join('; ') || 'None'}
- Medications: ${medicalRecord.medications.join(', ')}
- Footwear: ${medicalRecord.footwearHabits.join(', ')}

Current Foot Data:
- Health Index: ${healthIndex.score.toFixed(0)}/100
- Risk Score: ${riskScore.toFixed(0)}/100
- Max Pressure: ${maxPressure.toFixed(1)} kPa

Daily Tasks:
- Completed: ${completedTasks}/${totalTasks}

Provide personalized, empathetic, and medically-informed guidance. Always remind users to consult healthcare providers for medical decisions.`;

  const { messages, sendMessage } = useRorkAgent({
    tools: {
      addTodoTask: createRorkTool({
        description: 'Add a new task to the user\'s to-do list',
        zodSchema: z.object({
          title: z.string().describe('Short title for the task'),
          description: z.string().describe('Detailed description of the task').optional(),
          category: z.enum(['foot_care', 'nutrition', 'activity', 'health_tracking', 'medication', 'education']).describe('Task category'),
          priority: z.enum(['low', 'medium', 'high']).describe('Task priority'),
        }),
        execute(input) {
          addTask({
            title: input.title,
            description: input.description || '',
            completed: false,
            type: input.category,
            urgency: input.priority,
            generatedBy: 'stepmate',
          });
          return `Task "${input.title}" added to your to-do list!`;
        },
      }),
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const [hasInitialized, setHasInitialized] = useState<boolean>(false);

  useEffect(() => {
    if (!hasInitialized && messages.length === 0) {
      setHasInitialized(true);
      const initMessage = `You are StepMate, a helpful AI assistant for diabetic foot care. ${systemContext}\n\nPlease introduce yourself as StepMate and ask how you can help today. Keep your response friendly and conversational.`;
      sendMessage(initMessage);
    }
  }, [hasInitialized, messages.length, sendMessage]);

  const handleSend = () => {
    if (!input.trim()) return;
    
    const userInput = input.trim();
    setInput('');
    sendMessage(userInput);
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View style={[styles.header, { backgroundColor: colors.surface, paddingTop: Platform.OS === 'web' ? insets.top + 20 : 20 }]}>
        <View style={styles.headerContent}>
          <View style={[styles.botAvatar, { backgroundColor: colors.primary }]}>
            <Bot size={24} color="#FFFFFF" />
          </View>
          <View>
            <Text style={[styles.headerTitle, { color: colors.text }]}>StepMate</Text>
            <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
              Your Health Assistant
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.map((m) => (
          <View key={m.id} style={{ marginVertical: 8 }}>
            <View style={{ flexDirection: 'column', gap: 4 }}>
              {m.parts.map((part, i) => {
                if (part.type === 'text') {
                  return (
                    <View
                      key={`${m.id}-${i}`}
                      style={[
                        styles.messageBubble,
                        m.role === 'user' ? styles.userBubble : styles.assistantBubble,
                      ]}
                    >
                      <View style={styles.messageHeader}>
                        {m.role === 'assistant' ? (
                          <View style={[styles.messageAvatar, { backgroundColor: colors.primary }]}>
                            <Bot size={16} color="#FFFFFF" />
                          </View>
                        ) : (
                          <View style={[styles.messageAvatar, { backgroundColor: colors.textSecondary }]}>
                            <User size={16} color="#FFFFFF" />
                          </View>
                        )}
                        <Text style={[styles.messageRole, { color: colors.textTertiary }]}>
                          {m.role === 'user' ? 'You' : 'StepMate'}
                        </Text>
                      </View>
                      <Text style={[styles.messageText, { color: colors.text }]}>
                        {part.text}
                      </Text>
                      <Text style={[styles.messageTime, { color: colors.textTertiary }]}>
                        {new Date().toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </Text>
                    </View>
                  );
                } else if (part.type === 'tool') {
                  const toolName = part.toolName;
                  switch (part.state) {
                    case 'input-streaming':
                    case 'input-available':
                      return (
                        <View key={`${m.id}-${i}`} style={[styles.toolMessage, { backgroundColor: colors.surface }]}>
                          <Text style={[styles.toolText, { color: colors.textSecondary }]}>
                            ⚙️ Calling {toolName}...
                          </Text>
                        </View>
                      );
                    case 'output-available':
                      return (
                        <View key={`${m.id}-${i}`} style={[styles.toolMessage, { backgroundColor: colors.surface }]}>
                          <Text style={[styles.toolText, { color: colors.primary }]}>
                            ✅ {JSON.stringify(part.output)}
                          </Text>
                        </View>
                      );
                    case 'output-error':
                      return (
                        <View key={`${m.id}-${i}`} style={[styles.toolMessage, { backgroundColor: colors.surface }]}>
                          <Text style={[styles.toolText, { color: '#EF4444' }]}>
                            ❌ Error: {part.errorText}
                          </Text>
                        </View>
                      );
                  }
                }
                return null;
              })}
            </View>
          </View>
        ))}
      </ScrollView>

      <View style={[styles.inputContainer, { backgroundColor: colors.surface, paddingBottom: insets.bottom > 0 ? insets.bottom : 16 }]}>
        <TextInput
          style={[styles.input, { backgroundColor: colors.background, color: colors.text }]}
          placeholder="Ask StepMate anything..."
          placeholderTextColor={colors.textTertiary}
          value={input}
          onChangeText={setInput}
          multiline
          maxLength={500}
        />
        <TouchableOpacity
          style={[styles.sendButton, { backgroundColor: colors.primary }]}
          onPress={handleSend}
          disabled={!input.trim()}
        >
          <Send size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  botAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700' as const,
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 20,
    gap: 16,
  },
  messageBubble: {
    maxWidth: '85%',
    padding: 12,
    borderRadius: 16,
    gap: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: 'rgba(59, 130, 246, 0.15)',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderBottomLeftRadius: 4,
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  messageAvatar: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  messageRole: {
    fontSize: 12,
    fontWeight: '600' as const,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  messageTime: {
    fontSize: 11,
    alignSelf: 'flex-end',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    paddingTop: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  input: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 24,
    fontSize: 15,
    maxHeight: 100,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  toolMessage: {
    padding: 12,
    borderRadius: 8,
    marginVertical: 4,
    alignSelf: 'flex-start',
    maxWidth: '85%',
  },
  toolText: {
    fontSize: 13,
    fontStyle: 'italic' as const,
  },
});
