import type { Product } from '../types/chat';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const defaultImageUrl =
    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTydlkOWWEOacWIaFKSdUMi8eHDLuRe6-D7rnk4x5EHaggA-KpmcKTkEq4hmr73I_sZ4wE&usqp=CAU';

  return (
    <div className='rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow'>
      <a
        href={product.url}
        target='_blank'
        rel='noopener noreferrer'
        className='block'
      >
        <div className='p-6'>
          <div className='flex gap-4 mb-4'>
            <div className='w-[100px] h-auto flex-shrink-0 overflow-hidden rounded'>
              <img
                src={product.image_url || defaultImageUrl}
                alt={product.name}
                className='h-full w-full object-contain'
              />
            </div>
            <div className='flex-1'>
              <h3 className='text-lg font-semibold mb-2'>{product.name}</h3>
              <p className='text-sm text-muted-foreground'>
                {product.description}
              </p>
            </div>
          </div>
          <div className='flex items-center justify-between'>
            <span className='text-lg font-bold'>{product.price}</span>
            <span className='inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2'>
              Buy Now
            </span>
          </div>
        </div>
      </a>
    </div>
  );
}
