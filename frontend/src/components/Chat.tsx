import React, { useState, useRef, useEffect, FormEvent, ChangeEvent, ReactNode } from 'react';
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
  Code,
  UnorderedList,
  OrderedList,
  ListItem,
  Heading,
} from '@chakra-ui/react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface Message {
  type: 'user' | 'assistant' | 'error';
  content: string;
  sources?: string[];
  role?: 'user' | 'assistant';
}

interface MarkdownComponentProps {
  children: ReactNode;
}

interface CodeProps extends MarkdownComponentProps {
  node?: any;
  inline?: boolean;
  className?: string;
}

const Chat = () => {
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

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      type: 'user',
      content: input.trim(),
      role: 'user',
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Convert messages to conversation history format
      const conversationHistory = messages.map(msg => ({
        role: msg.role || (msg.type === 'user' ? 'user' : 'assistant'),
        content: msg.content,
        sources: msg.sources,
      }));

      const response = await axios.post('http://localhost:8001/ask', {
        question: input.trim(),
        conversation_history: conversationHistory,
      });

      const assistantMessage: Message = {
        type: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        role: 'assistant',
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

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const MessageContent = ({ content }: { content: string }) => {
    return (
      <Box className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw, rehypeHighlight]}
          components={{
            p: ({ children }: MarkdownComponentProps) => <Text mb={4}>{children}</Text>,
            h1: ({ children }: MarkdownComponentProps) => <Heading as="h1" size="xl" mb={4}>{children}</Heading>,
            h2: ({ children }: MarkdownComponentProps) => <Heading as="h2" size="lg" mb={3}>{children}</Heading>,
            h3: ({ children }: MarkdownComponentProps) => <Heading as="h3" size="md" mb={3}>{children}</Heading>,
            h4: ({ children }: MarkdownComponentProps) => <Heading as="h4" size="sm" mb={3}>{children}</Heading>,
            ul: ({ children }: MarkdownComponentProps) => <UnorderedList mb={4}>{children}</UnorderedList>,
            ol: ({ children }: MarkdownComponentProps) => <OrderedList mb={4}>{children}</OrderedList>,
            li: ({ children }: MarkdownComponentProps) => <ListItem mb={2}>{children}</ListItem>,
            code: ({ node, inline, className, children, ...props }: CodeProps) => {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <Code
                  className={className}
                  p={4}
                  borderRadius="md"
                  display="block"
                  whiteSpace="pre"
                  overflowX="auto"
                  {...props}
                >
                  {children}
                </Code>
              ) : (
                <Code className={className} {...props}>
                  {children}
                </Code>
              );
            },
            a: ({ href, children }: { href?: string; children: ReactNode }) => (
              <Link href={href} color="blue.500" isExternal>
                {children}
              </Link>
            ),
            blockquote: ({ children }: MarkdownComponentProps) => (
              <Box
                as="blockquote"
                pl={4}
                borderLeft="4px"
                borderColor="gray.200"
                color="gray.600"
                mb={4}
              >
                {children}
              </Box>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </Box>
    );
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
              <MessageContent content={message.content} />
              {message.sources && message.sources.length > 0 && (
                <Box mt={4}>
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
            onChange={handleInputChange}
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