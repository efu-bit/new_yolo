import { useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, X, Camera } from 'lucide-react';

interface ImageUploadProps {
  onImageUpload: (file: File) => void;
  uploadedImage?: string;
  onClearImage: () => void;
}

export const ImageUpload = ({ onImageUpload, uploadedImage, onClearImage }: ImageUploadProps) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));
    
    if (imageFile) {
      onImageUpload(imageFile);
    }
  }, [onImageUpload]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onImageUpload(file);
    }
  }, [onImageUpload]);

  if (uploadedImage) {
    return (
      <Card className="relative overflow-hidden shadow-medium border border-border">
        <img 
          src={uploadedImage} 
          alt="Uploaded furniture" 
          className="w-full h-64 object-cover"
        />
        <Button
          onClick={onClearImage}
          size="icon"
          variant="destructive"
          className="absolute top-2 right-2 h-8 w-8 shadow-medium"
          aria-label="Remove uploaded image"
        >
          <X className="h-4 w-4" />
        </Button>
      </Card>
    );
  }

  return (
    <Card
      className={`
        relative overflow-hidden border-2 border-dashed transition-all duration-200 cursor-pointer
        ${isDragOver 
          ? 'border-primary bg-primary/5 shadow-glow' 
          : 'border-border hover:border-primary/50 hover:bg-primary/5'
        }
      `}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
        <input
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="absolute inset-0 opacity-0 cursor-pointer"
        aria-label="Upload furniture image"
      />
      
      <div className="flex flex-col items-center justify-center p-12 text-center space-y-4">
        <div className={`
          p-4 rounded-full transition-all duration-200
          ${isDragOver ? 'bg-primary text-primary-foreground shadow-glow' : 'bg-secondary'}
        `}>
          {isDragOver ? <Camera className="h-8 w-8" /> : <Upload className="h-8 w-8" />}
        </div>
        
        <div className="space-y-2">
          <h3 className="text-lg font-semibold">
            {isDragOver ? 'Drop your image here' : 'Upload furniture image'}
          </h3>
          <p className="text-muted-foreground text-sm">
            Drag & drop an image or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            JPG, PNG, or WebP (max 10MB)
          </p>
        </div>

        <Button variant="outline" className="mt-4">
          <Upload className="h-4 w-4 mr-2" />
          Choose File
        </Button>
      </div>
    </Card>
  );
};