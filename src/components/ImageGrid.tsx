interface ImageItem {
  id: string;
  imageUrl?: string;
  similarity?: number;
}

interface ImageGridProps {
  items?: ImageItem[];
  isLoading?: boolean;
}

export const ImageGrid = ({ items = [], isLoading }: ImageGridProps) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[...Array(12)].map((_, i) => (
          <div key={i} className="aspect-square bg-muted rounded-lg animate-pulse"></div>
        ))}
      </div>
    );
  }

  if (!items.length) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {items.map((item) => (
        <div key={item.id} className="group relative aspect-square overflow-hidden rounded-lg bg-muted">
          {item.imageUrl ? (
            <img 
              src={item.imageUrl} 
              alt=""
              className="w-full h-full object-cover transition-transform group-hover:scale-105"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNDAwIDQwMCIgZmlsbD0iI2YzZjRmNiI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNlZWVlZWUiLz48cGF0aCBkPSJNMTUwLDEwMEgyNTBWMjUwSDE1MFYxMDBaTTEwMCwxNTBIMTUwVjI1MEgxMDBWMTUwWk0yMDAsMTUwSDI1MFYyNTBIMjAwVjE1MFpNNTAsMjAwSDEwMFYyNTBINTBWMjAwWk0yMDAsMjAwSDI1MFYyNTBIMjAwVjIwMFpNMjUwLDEwMEgzMDBWMTUwSDI1MFYxMDBaTTMwMCwxNTBIMzUwVjIwMEgzMDBWMTUwWk0yMDAsMTAwVjE1MEgyNTBWMTUwVjEwMEgyMDBaTTE1MCwxNTBIMjAwVjIwMEgxNTBWMTUwWk0xMDAsMjAwaDUwVjI1MEgxMDBWMjAwWk0yMDAsMjAwaDUwVjI1MEgyMDBWMjAwWiIgZmlsbD0iI2QxZDNkNyIvPjwvc3ZnPg==';
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-muted">
              <div className="text-muted-foreground/50">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
