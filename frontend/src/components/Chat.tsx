import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Flex,
  Link,
  Spinner,
} from '@chakra-ui/react';
import axios from 'axios';

interface Message {
  type: 'user' | 'assistant' | 'error';
  content: string;
  sources?: string[];
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      type: 'user',
      content: input.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8001/ask', {
        question: input.trim(),
      });

      const assistantMessage: Message = {
        type: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        type: 'error',
        content: 'Failed to get response from the server. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      maxW="800px"
      mx="auto"
      h="100vh"
      display="flex"
      flexDirection="column"
      p={4}
    >
      <VStack flex={1} overflowY="auto" gap={4} mb={4}>
        {messages.map((message, index) => (
          <Flex
            key={index}
            w="100%"
            justify={message.type === 'user' ? 'flex-end' : 'flex-start'}
          >
            <Box
              maxW="80%"
              bg={
                message.type === 'user'
                  ? 'blue.500'
                  : message.type === 'error'
                  ? 'red.100'
                  : 'gray.100'
              }
              color={
                message.type === 'user'
                  ? 'white'
                  : message.type === 'error'
                  ? 'red.700'
                  : 'black'
              }
              p={4}
              borderRadius="lg"
              boxShadow="sm"
            >
              <Text>{message.content}</Text>
              {message.sources && message.sources.length > 0 && (
                <Box mt={2}>
                  <Text fontSize="sm" color="gray.500">
                    Sources:
                  </Text>
                  {message.sources.map((source, idx) => (
                    <Link
                      key={idx}
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      color="blue.500"
                      fontSize="sm"
                      display="block"
                      mt={1}
                    >
                      {source}
                    </Link>
                  ))}
                </Box>
              )}
            </Box>
          </Flex>
        ))}
        {isLoading && (
          <Flex w="100%" justify="flex-start">
            <Box bg="gray.100" p={4} borderRadius="lg">
              <Spinner size="sm" />
            </Box>
          </Flex>
        )}
        <div ref={messagesEndRef} />
      </VStack>

      <form onSubmit={handleSubmit}>
        <HStack>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about Adobe Analytics..."
            size="lg"
            disabled={isLoading}
          />
          <Button
            type="submit"
            colorScheme="blue"
            size="lg"
            isLoading={isLoading}
            disabled={!input.trim() || isLoading}
          >
            Send
          </Button>
        </HStack>
      </form>
    </Box>
  );
};

export default Chat; 