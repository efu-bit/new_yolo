import { useState } from 'react';
import { ImageUpload } from '@/components/ImageUpload';
import { FurnitureCanvas } from '@/components/FurnitureCanvas';
import { SearchResults } from '@/components/SearchResults';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Sparkles, Search, Info, CheckCircle2, Crop } from 'lucide-react';

interface FurnitureMask {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
  label?: string;
  mask?: number[][];
}

interface BackendMask {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  score: number;
  mask: number[][];
}


interface SearchResult {
  id: string;
  name: string;
  price?: string;
  brand?: string;
  rating?: number;
  imageUrl?: string;
  similarity: number;
  inStock?: boolean;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Index = () => {
  const [uploadedImage, setUploadedImage] = useState<string>();
  const [uploadedFile, setUploadedFile] = useState<File>();
  const [masks, setMasks] = useState<FurnitureMask[]>([]);
  const [selectedFurniture, setSelectedFurniture] = useState<FurnitureMask>();
  const [isSegmenting, setIsSegmenting] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [croppedImage, setCroppedImage] = useState<string>();
  const { toast } = useToast();

  const handleImageUpload = async (file: File) => {
    const url = URL.createObjectURL(file);
    setUploadedImage(url);
    setUploadedFile(file);
    setSelectedFurniture(undefined);
    setMasks([]);
    setResults([]);
    setCroppedImage(undefined);

    toast({
      title: 'Image uploaded successfully',
      description: 'AI is analyzing your image for furniture...'
    });

    // Call backend for segmentation
    try {
      setIsSegmenting(true);
      const form = new FormData();
      form.append('image', file);
      const resp = await fetch(`${BACKEND_URL}/segment`, { method: 'POST', body: form });
      if (!resp.ok) throw new Error(await resp.text());
      const data: BackendMask[] = await resp.json();
      const mapped: FurnitureMask[] = data.map((m) => ({
        id: m.id,
        x: m.x,
        y: m.y,
        width: m.width,
        height: m.height,
        confidence: m.score ?? 0,
        label: undefined,
        mask: m.mask
      }));
      setMasks(mapped);
      toast({ title: 'Detection complete', description: `${mapped.length} items found` });
    } catch (e: any) {
      toast({ title: 'Segmentation failed', description: String(e), variant: 'destructive' });
    } finally {
      setIsSegmenting(false);
    }
  };

  const handleClearImage = () => {
    if (uploadedImage) {
      URL.revokeObjectURL(uploadedImage);
    }
    if (croppedImage) {
      URL.revokeObjectURL(croppedImage);
    }
    setUploadedImage(undefined);
    setUploadedFile(undefined);
    setSelectedFurniture(undefined);
    setMasks([]);
    setResults([]);
    setCroppedImage(undefined);
  };

  const handleFurnitureSelect = async (furniture: FurnitureMask) => {
    setSelectedFurniture(furniture);
    setIsSearching(true);

    toast({
      title: 'Furniture selected',
      description: 'Cropping and searching for similar items...'
    });

    if (!uploadedFile) return;

    try {
      // 1) Crop the image using bounding box coordinates
      const cropForm = new FormData();
      cropForm.append('image', uploadedFile);
      cropForm.append('x', String(furniture.x));
      cropForm.append('y', String(furniture.y));
      cropForm.append('width', String(furniture.width));
      cropForm.append('height', String(furniture.height));
      
      const cropResp = await fetch(`${BACKEND_URL}/crop_bbox`, { method: 'POST', body: cropForm });
      if (!cropResp.ok) throw new Error(await cropResp.text());
      const cropData = await cropResp.json();
      
      // Convert base64 to blob URL for display
      const base64Response = await fetch(`data:image/png;base64,${cropData.cropped_image}`);
      const blob = await base64Response.blob();
      const croppedUrl = URL.createObjectURL(blob);
      setCroppedImage(croppedUrl);
      
      // 2) Get embedding for the cropped image using SigLIP2
      const croppedFile = new File([blob], 'cropped.png', { type: 'image/png' });
      const embedForm = new FormData();
      embedForm.append('image', croppedFile);
      
      const embedResp = await fetch(`${BACKEND_URL}/embed_siglip`, { method: 'POST', body: embedForm });
      if (!embedResp.ok) throw new Error(await embedResp.text());
      const embedding: number[] = await embedResp.json();

      // 3) Search in DB
      const searchResp = await fetch(`${BACKEND_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ embedding, top_k: 12 })
      });
      if (!searchResp.ok) throw new Error(await searchResp.text());
      const items: SearchResult[] = await searchResp.json();
      setResults(items);
      toast({ title: 'Search complete', description: `Found ${items.length} matching products` });
    } catch (e: any) {
      toast({ title: 'Search failed', description: String(e), variant: 'destructive' });
    } finally {
      setIsSearching(false);
    }
  };


  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50 shadow-soft">
        <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                  FurniFind AI
                </h1>
                <p className="text-sm text-muted-foreground">Find furniture with computer vision</p>
              </div>
            
            <div className="flex items-center space-x-3">
              <Badge variant="secondary" className="flex items-center space-x-1">
                <Sparkles className="h-3 w-3" />
                <span>Powered by SAM2</span>
              </Badge>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Hero Section */}
          {!uploadedImage && (
            <div className="text-center space-y-6 py-12">
              <div className="space-y-4">
                <h2 className="text-4xl font-bold">
                  Discover furniture with
                  <span className="bg-gradient-primary bg-clip-text text-transparent"> AI vision</span>
                </h2>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                  Upload any room photo and our AI will detect furniture pieces, 
                  then find similar items from top retailers instantly.
                </p>
              </div>
              
              <div className="flex justify-center space-x-6 text-sm text-muted-foreground">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">1</span>
                  </div>
                  <span>Upload image</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">2</span>
                  </div>
                  <span>AI detects furniture</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">3</span>
                  </div>
                  <span>Click to auto-crop and search</span>
                </div>
              </div>
            </div>
          )}

          {/* Upload Section */}
          <div className="max-w-2xl mx-auto">
            <ImageUpload
              onImageUpload={handleImageUpload}
              uploadedImage={uploadedImage}
              onClearImage={handleClearImage}
            />
          </div>

          {/* Canvas and Results */}
          {uploadedImage && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Canvas Section */}
              <div className="space-y-4">
                <FurnitureCanvas
                  imageSrc={uploadedImage}
                  masks={masks}
                  isProcessing={isSegmenting}
                  onFurnitureSelect={handleFurnitureSelect}
                  selectedFurniture={selectedFurniture}
                />
                
                {/* Selected Furniture Info */}
                {selectedFurniture && (
                  <div className="bg-card rounded-lg p-4 shadow-soft border border-border">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                          <h4 className="font-semibold text-card-foreground">Selected item</h4>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Confidence: {Math.round((selectedFurniture.confidence ?? 0) * 100)}%
                        </p>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Info className="h-3 w-3" />
                          <span>AI detected this furniture piece</span>
                        </div>
                      </div>
                      <Button 
                        size="sm" 
                        className="flex items-center space-x-1"
                        disabled={isSearching}
                      >
                        <Search className="h-4 w-4" />
                        <span>{isSearching ? 'Searching...' : 'Search Similar'}</span>
                      </Button>
                    </div>
                  </div>
                )}

                {/* Cropped Image Display */}
                {croppedImage && (
                  <div className="bg-card rounded-lg p-4 shadow-soft border border-border">
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <Crop className="h-4 w-4 text-green-500" />
                        <h4 className="font-semibold text-card-foreground">Auto-cropped Selection</h4>
                      </div>
                      <img 
                        src={croppedImage} 
                        alt="Cropped furniture" 
                        className="w-full h-auto rounded-lg border border-border"
                      />
                      <p className="text-xs text-muted-foreground">
                        This is the area automatically cropped around your selected furniture
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Results Section */}
              <div>
                <SearchResults
                  query={selectedFurniture?.label || 'Selected furniture'}
                  results={results}
                  isLoading={isSearching}
                />
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-background/50 backdrop-blur-sm mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-muted-foreground">
            <p>Built with React, SAM2, and MongoDB • Computer Vision for Interior Design</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;