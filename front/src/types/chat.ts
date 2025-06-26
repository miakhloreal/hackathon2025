export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Product {
  name: string;
  price: string;
  url: string;
  description: string;
}

export interface ChatResponse {
  text: string;
  products: Product[] | null;
}
