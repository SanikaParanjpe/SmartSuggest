import React, { useEffect, useState } from 'react';
import hashtagIcon from './hashtag.svg';
import {
  ChakraProvider,
  Box,
  Textarea,
  Flex,
  Heading,
  Button,
  VStack,
  Text,
  Select,
  Table,
  Thead,
  Tbody,
  Tfoot,
  Tr,
  Th,
  Td,
  TableContainer,
  Tag,
  TagLabel,
  DarkMode,
  Wrap,
  Spacer,
  Divider,
  useToast,
} from '@chakra-ui/react';
import cities from './cities.json';
import Sentiment from 'sentiment';
import theme from './theme';
const sentiment = new Sentiment();

function App() {
  const [selectedCity, setSelectedCity] = useState();
  const [text, setText] = useState();
  const [result, setResult] = useState();
  const [suggestedTwitterHashtags, setSuggestedTwitterHashtags] = useState([]);
  const [suggestedNewsHashtags, setSuggestedNewsHashtags] = useState([]);
  const toast = useToast()
  const [sentimentData, setSentimentData] = useState([]);

  useEffect(() => {
    getInitialData();
  }, []);
  
  async function getInitialData() {
    const response = await fetch('/api/sentiment', {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const json = await response.json();
    console.log(json);
    setSentimentData(json)
  }

  async function analyzeSentimentAndPost() {
    // get sentiment
    if (!text) {
      toast({
        title: `Please write some text`,
        status: 'error',
        isClosable: true,
      });
      return;
    }
    var output = sentiment.analyze(text);
    console.log(output);
    setResult(output);

    // update sentiment
    if (!selectedCity) {
      toast({
        title: `Please select a city from the dropdown`,
        status: 'error',
        isClosable: true,
      });
      return;
    }
    const response = await fetch('/api/update_sentiment', {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tweet: text,
        sentiment: output.score,
        city: selectedCity,
      })
    });
    const json = await response.json();
    console.log(json);
    setSentimentData(json)
  }

  function calculateSentimentItem(sentiment) {
    const { positive, neutral, negative } = sentiment;
    const total = positive + neutral + negative;
    const sentimentScore = (positive - negative) / total;
    
    var sentimentLabel = 'Neutral😐';
    var sentimentColor = 'white';
    if (sentimentScore > 0) {
      sentimentLabel = 'Positive🙃';
      sentimentColor = '#41644A';
    }
    else if (sentimentScore < 0) {
      sentimentLabel = 'Negative😔';
      sentimentColor = '#CE5959';
    }

    return <Td color={sentimentColor}>{sentimentLabel}</Td>
  }

  async function getHashtagSuggestions() {
    if (!text) {
      toast({
        title: `Please write some text`,
        status: 'error',
        isClosable: true,
      });
      return;
    }
    const response = await fetch('/api/suggest_hashtags', {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        tweet: text
      })
    });
    const json = await response.json();

    setSuggestedTwitterHashtags(json.twitter_hashtags)
    setSuggestedNewsHashtags(json.news_hashtags)
    console.log(json);
  }

  function toggleHashtag(hashtag) {
    if (text.includes(hashtag)) {
      setText(text.replace(hashtag, ''));
    }
    else {
      setText(text + ' ' + hashtag);
    }
  }

  function HashtagsRow({hashtags, dataFrom}) {
    if (hashtags.length == 0) return;
    return (
      <Flex gap={'10px'}>
        <Text fontSize='md'>{dataFrom} data: </Text>
        <Wrap>
          {
            hashtags.map((hashtag, i) => <HashtagPill key={hashtag+i} text={hashtag} />)
          }
        </Wrap>
      </Flex>
    );
  }
  
  function HashtagPill({text}) {
    return (
      <Tag onClick={() => toggleHashtag('#' + text)} cursor={'pointer'} size={"md"} key={text} variant='subtle'>
        <img height={"15px"} width={"15px"} src={hashtagIcon} />
        <TagLabel ml={"5px"}>{text}</TagLabel>
      </Tag>
    );
  }

  function copyTweet() {
    navigator.clipboard.writeText(text);
  }

  return (
    <ChakraProvider theme={theme}>
      <DarkMode>
      <Box textAlign="center" fontSize="xl" bgColor={"#0d1015"} paddingY={'5%'}>
        <Flex direction={'column'} justifyContent={'center'} paddingX={'25%'} height="100%" gap={"16px"}>
          <Flex>
            <Heading as='h4' size='md'>SmartSuggest</Heading>
          </Flex>
          <Select placeholder='Select city' onChange={(e) => setSelectedCity(e.target.value)}>
            {
              cities.map((city, i) => <option key={city + i} value={city}>{city}</option>)
            }
          </Select>
            <Textarea value={text} onChange={(e) => setText(e.target.value)} placeholder='Start typing your tweet...' bgColor={"#151c24"} minHeight={"200px"} border={"none"}/>
          <Flex gap={'15px'}>
            <Button onClick={analyzeSentimentAndPost} colorScheme='blue'>Post Sentiment</Button>
            <Button onClick={getHashtagSuggestions} colorScheme='blue'>Suggest Hashtags</Button>
            <Button onClick={copyTweet} colorScheme='blue' variant='outline'>Copy to clipboard</Button>
          </Flex>
          {
            suggestedNewsHashtags != "" &&
              <VStack alignItems={'flex-start'}>
                  <Heading as='h4' size='md' mb={'10px'}>Suggestions from</Heading>
                  <HashtagsRow dataFrom={"Twitter"} hashtags={suggestedTwitterHashtags} />
                  <Spacer height={'10px'} />
                  <Divider />
                  <Spacer height={'10px'} />
                  <HashtagsRow dataFrom={"News"} hashtags={suggestedNewsHashtags} />
              </VStack>
          }
          {
            result && <VStack alignItems={'flex-start'}>
              <Heading as='h4' size='md'>Results</Heading>
              <Text fontSize='md'>Score: {result.score}</Text>
              <Text fontSize='md'>Positive: {result.positive.join(", ")}</Text>
              <Text fontSize='md'>Negative: {result.negative.join(", ")}</Text>
            </VStack>
          }
          <Flex>
            <Heading as='h4' size='md'>Sentiment Data City Wise</Heading>
          </Flex>
          <TableContainer>
            <Table variant='simple'>
              <Thead>
                <Tr>
                  <Th>City</Th>
                  <Th>Sentiment</Th>
                </Tr>
              </Thead>
              <Tbody>
                {
                  sentimentData.map((item) => <Tr key={item._id}>
                  <Td>{item._id}</Td>
                  {calculateSentimentItem(item.sentiment)}
                </Tr>)
                }
              </Tbody>
              <Tfoot>
                <Tr>
                  <Th>City</Th>
                  <Th>Sentiment</Th>
                </Tr>
              </Tfoot>
            </Table>
          </TableContainer>
        </Flex>
      </Box>
      </DarkMode>
    </ChakraProvider>
  );
}

export default App;
