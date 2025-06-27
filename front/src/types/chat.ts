export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Product {
  name: string;
  price: string;
  url: string;
  image_url: string;
  description: string;
  ingredients: string[];
  advantages: string[];
  suitability: string[];
  questions: string[];
}

export interface ChatResponse {
  text: string;
  products: Product[] | null;
}
