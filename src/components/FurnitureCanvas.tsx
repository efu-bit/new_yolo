import { useRef, useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';


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

interface FurnitureCanvasProps {
    imageSrc: string;
    onFurnitureSelect: (furniture: FurnitureMask) => void;
    selectedFurniture?: FurnitureMask;
    masks: FurnitureMask[];
    isProcessing?: boolean;
}

export const FurnitureCanvas = ({
    imageSrc,
    onFurnitureSelect,
    selectedFurniture,
    masks,
    isProcessing = false,
}: FurnitureCanvasProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [originalImageDimensions, setOriginalImageDimensions] = useState({ width: 0, height: 0 });

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const img = new Image();
        img.onload = () => {
            const aspectRatio = img.width / img.height;
            const canvasWidth = 600;
            const canvasHeight = canvasWidth / aspectRatio;

            canvas.width = canvasWidth;
            canvas.height = canvasHeight;

            setOriginalImageDimensions({ width: img.width, height: img.height });

            ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);
            setImageLoaded(true);
        };

        img.src = imageSrc;
    }, [imageSrc]);

    useEffect(() => {
        if (!imageLoaded) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            // Draw all masks in their original shapes with color
            if (masks.length > 0) {
                masks.forEach((mask, idx) => {
                    if (!mask.mask) return;

                    // Assign a unique color per mask
                    const colors = [
                        [255, 99, 132],
                        [54, 162, 235],
                        [255, 206, 86],
                        [75, 192, 192],
                        [153, 102, 255],
                        [255, 159, 64],
                    ];
                    const [r, g, b] = colors[idx % colors.length];
                    ctx.save();
                    ctx.globalAlpha = 0.45; // semi-transparent

                    const maskArr = mask.mask;
                    const maskHeight = maskArr.length;
                    const maskWidth = maskArr[0].length;
                    const scaleX = canvas.width / maskWidth;
                    const scaleY = canvas.height / maskHeight;

                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                    for (let y = 0; y < maskHeight; y++) {
                        for (let x = 0; x < maskWidth; x++) {
                            if (maskArr[y][x]) {
                                ctx.fillRect(
                                    x * scaleX,
                                    y * scaleY,
                                    scaleX,
                                    scaleY
                                );
                            }
                        }
                    }
                    ctx.restore();
                });
            }
        };

        img.src = imageSrc;
    }, [imageSrc, selectedFurniture, imageLoaded, masks]);

    const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!imageLoaded || masks.length === 0) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const canvasX = (e.clientX - rect.left) * (canvas.width / rect.width);
        const canvasY = (e.clientY - rect.top) * (canvas.height / rect.height);

        // Check if clicked on a mask
        for (const mask of masks) {
            if (!mask.mask) continue;
            const maskArr = mask.mask;
            const maskHeight = maskArr.length;
            const maskWidth = maskArr[0].length;
            const scaleX = canvas.width / maskWidth;
            const scaleY = canvas.height / maskHeight;
            const mx = Math.floor(canvasX / scaleX);
            const my = Math.floor(canvasY / scaleY);
            if (
                mx >= 0 &&
                my >= 0 &&
                mx < maskWidth &&
                my < maskHeight &&
                maskArr[my][mx]
            ) {
                onFurnitureSelect(mask);
                break;
            }
        }
    };

    return (
        <Card className="overflow-hidden shadow-medium">
            <div className="p-4 border-b bg-gradient-subtle">
                <canvas
                    ref={canvasRef}
                    style={{ width: "100%", height: "auto", cursor: "pointer" }}
                    onClick={handleCanvasClick}
                />
            </div>
        </Card>
    );
};