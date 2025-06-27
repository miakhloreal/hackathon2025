import type { Product } from '../types/chat';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  return (
    <div className='rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow'>
      <a
        href={product.url}
        target='_blank'
        rel='noopener noreferrer'
        className='block p-6'
      >
        <h3 className='text-lg font-semibold mb-2'>{product.name}</h3>
        <p className='text-sm text-muted-foreground mb-4'>
          {product.description}
        </p>
        {product.ingredients && product.ingredients.length > 0 && (
          <div className='mb-4'>
            <h4 className='text-sm font-semibold mb-2'>Key Ingredients:</h4>
            <ul className='text-sm text-muted-foreground list-disc list-inside'>
              {product.ingredients.map((ingredient, idx) => (
                <li key={idx}>{ingredient}</li>
              ))}
            </ul>
          </div>
        )}
        <div className='flex items-center justify-between'>
          <span className='text-lg font-bold'>{product.price}</span>
          <span className='inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2'>
            Buy Now
          </span>
        </div>
      </a>
    </div>
  );
}
