import { Chat } from './components/Chat';

export default function App() {
  return (
    <main className='min-h-screen bg-background font-sans antialiased'>
      <div className='relative flex min-h-screen flex-col'>
        <div className='flex-1'>
          <Chat />
        </div>
      </div>
    </main>
  );
}
