import { ImageGrid } from './ImageGrid';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export interface SearchResult {
  id: string;
  name: string;
  price?: string;
  brand?: string;
  rating?: number;
  imageUrl?: string;
  similarity: number;
  inStock?: boolean;
}

interface SearchResultsProps {
  query?: string;
  results?: SearchResult[];
  isLoading?: boolean;
}

export const SearchResults = ({ query, results = [], isLoading }: SearchResultsProps) => {
  // Helper: convert any gs:// URL to our proxy BACKEND_URL/images/<path>
  const toProxyUrl = (url?: string) => {
    if (!url) return undefined;
    if (url.startsWith('gs://')) {
      // Strip `gs://<bucket>/` and prefix with BACKEND_URL/images/
      const path = url.replace(/^gs:\/\/[^/]+\//, '');
      return `${BACKEND_URL}/images/${path}`;
    }
    return url;
  };

  // Map the results to the format expected by ImageGrid
  const imageItems = results.map(result => ({
    id: result.id,
    // Prefer original_url from backend, but route via proxy for browser compatibility
    imageUrl: toProxyUrl((result as any).original_url || result.imageUrl),
    similarity: result.similarity
  }));

  return (
    <div className="space-y-4">
      {query && (
        <h2 className="text-xl font-semibold">
          Similar to "{query}"
        </h2>
      )}
      <ImageGrid 
        items={imageItems} 
        isLoading={isLoading} 
      />
    </div>
  );
};