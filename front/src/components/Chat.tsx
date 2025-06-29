import { useState, useRef, useEffect } from 'react';
import type { ChatMessage, ChatResponse } from '../types/chat';
import { ProductCard } from './ProductCard';

function TypingIndicator() {
  return (
    <div className='flex justify-start'>
      <div className='bg-muted rounded-lg p-4 max-w-[80%]'>
        <div className='flex items-center space-x-2'>
          <div
            className='w-2 h-2 bg-primary rounded-full animate-bounce'
            style={{ animationDelay: '0ms' }}
          ></div>
          <div
            className='w-2 h-2 bg-primary rounded-full animate-bounce'
            style={{ animationDelay: '150ms' }}
          ></div>
          <div
            className='w-2 h-2 bg-primary rounded-full animate-bounce'
            style={{ animationDelay: '300ms' }}
          ></div>
        </div>
      </div>
    </div>
  );
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "👋 Hi! I'm kNOwLI, your personal beauty advisor. I'm here to help you discover the perfect L'Oréal products for your needs. Whether you're looking for skincare, haircare, or makeup recommendations, I'll guide you to the best solutions. What can I help you with today?",
    },
  ]);
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

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
        }),
      });

      const data: ChatResponse = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.text,
        },
      ]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, there was an error processing your request.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        role: 'assistant',
        content:
          "👋 Hi! I'm kNOwLI, your personal beauty advisor. I'm here to help you discover the perfect L'Oréal products for your needs. Whether you're looking for skincare, haircare, or makeup recommendations, I'll guide you to the best solutions. What can I help you with today?",
      },
    ]);
  };

  const extractProducts = (text: string) => {
    try {
      // Find everything between the first { and its matching }
      const jsonRegex = /\{(?:[^{}]|(?:\{[^{}]*\}))*\}/;
      const jsonMatch = text.match(jsonRegex);
      if (jsonMatch) {
        const productData = JSON.parse(jsonMatch[0]);
        // Only include the essential information in the product card
        return [
          {
            name: productData.name,
            description: productData.description,
            price: productData.price || '€18.99',
            url: productData.url || '#',
            image_url: productData.image_url || '',
            ingredients: productData.ingredients || [],
            advantages: productData.advantages || [],
            suitability: productData.suitability || [],
            questions: productData.questions || [],
          },
        ];
      }
    } catch (e) {
      console.error('Error parsing product JSON:', e);
    }
    return null;
  };

  const formatResponseText = (text: string) => {
    // Remove everything up to the first section header
    const cleanedText = text.replace(/^[\s\S]*?(## [👩🏼‍🔬🌟✨💫])/, '$1').trim();

    // Split the content into sections
    const sections = cleanedText.split(/(?=## [👩🏼‍🔬🌟✨💫])/);

    return sections.map((section, index) => {
      if (!section.trim()) return null;

      // Split section into title and content
      const [title, ...content] = section.split('\n');

      // Format the content: split by bullet points and filter empty lines
      const bulletPoints = content
        .join('\n')
        .split('•')
        .filter((point) => point.trim())
        .map((point) => point.trim());

      return (
        <div key={index} className='mb-6'>
          <h3 className='text-lg font-semibold mb-4'>{title.trim()}</h3>
          <ul className='space-y-4'>
            {bulletPoints.map((point, idx) => (
              <li key={idx} className='flex items-start'>
                <span className='mr-2'>•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      );
    });
  };

  return (
    <div className='flex flex-col h-screen max-w-3xl mx-auto p-4'>
      <div className='flex justify-between items-center mb-4'>
        <h1 className='text-2xl font-bold'>kNOwLI Advisor</h1>
        <button
          onClick={handleReset}
          className='inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-secondary text-secondary-foreground hover:bg-secondary/80 h-10 px-4 py-2'
        >
          Reset Chat
        </button>
      </div>

      <div className='flex-1 overflow-y-auto mb-4 space-y-4'>
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {message.role === 'assistant' && (
                <>
                  {extractProducts(message.content)?.map((product, idx) => (
                    <div key={idx} className='mb-4'>
                      <ProductCard product={product} />
                    </div>
                  ))}
                  <div className='mt-4'>
                    {formatResponseText(message.content)}
                  </div>
                </>
              )}
              {message.role === 'user' && message.content}
            </div>
          </div>
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className='flex gap-2'>
        <input
          type='text'
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder='Tell me about your beauty needs...'
          className='flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'
          disabled={isLoading}
        />
        <button
          type='submit'
          disabled={isLoading}
          className='inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2'
        >
          Send
        </button>
      </form>
    </div>
  );
}
