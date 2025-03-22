import { ChakraProvider, Box, Heading } from '@chakra-ui/react';
import Chat from './components/Chat';

function App() {
  return (
    <ChakraProvider>
      <Box minH="100vh" bg="gray.50">
        <Box bg="white" boxShadow="sm" py={4}>
          <Heading size="lg" textAlign="center" color="blue.600">
            Adobe Analytics Documentation Assistant
          </Heading>
        </Box>
        <Chat />
      </Box>
    </ChakraProvider>
  );
}

export default App;
