// Web Worker for image processing
// This moves heavy image processing operations off the main thread

// Bilateral filter implementation
function applyBilateralFilter(imageData, spatialSigma, colorSigma) {
  const data = imageData.data;
  const width = imageData.width;
  const height = imageData.height;
  const output = new Uint8ClampedArray(data.length);
  
  // Copy alpha channel as-is
  for (let i = 3; i < data.length; i += 4) {
    output[i] = data[i];
  }
  
  const kernelRadius = Math.ceil(spatialSigma * 3);
  
  for (let y = kernelRadius; y < height - kernelRadius; y++) {
    for (let x = kernelRadius; x < width - kernelRadius; x++) {
      const centerIdx = (y * width + x) * 4;
      const centerR = data[centerIdx];
      const centerG = data[centerIdx + 1];
      const centerB = data[centerIdx + 2];
      
      let sumR = 0, sumG = 0, sumB = 0;
      let weightSum = 0;
      
      for (let dy = -kernelRadius; dy <= kernelRadius; dy++) {
        for (let dx = -kernelRadius; dx <= kernelRadius; dx++) {
          const ny = y + dy;
          const nx = x + dx;
          const nIdx = (ny * width + nx) * 4;
          
          // Spatial weight (Gaussian based on distance)
          const spatialDist = dx * dx + dy * dy;
          const spatialWeight = Math.exp(-spatialDist / (2 * spatialSigma * spatialSigma));
          
          // Color weight (Gaussian based on color difference)
          const colorDist = Math.pow(data[nIdx] - centerR, 2) + 
                           Math.pow(data[nIdx + 1] - centerG, 2) + 
                           Math.pow(data[nIdx + 2] - centerB, 2);
          const colorWeight = Math.exp(-colorDist / (2 * colorSigma * colorSigma));
          
          const weight = spatialWeight * colorWeight;
          
          sumR += data[nIdx] * weight;
          sumG += data[nIdx + 1] * weight;
          sumB += data[nIdx + 2] * weight;
          weightSum += weight;
        }
      }
      
      output[centerIdx] = Math.round(sumR / weightSum);
      output[centerIdx + 1] = Math.round(sumG / weightSum);
      output[centerIdx + 2] = Math.round(sumB / weightSum);
    }
  }
  
  // Copy back to original
  for (let i = 0; i < data.length; i++) {
    data[i] = output[i];
  }
  
  return imageData;
}

// Optimized noise reduction
function applyNoiseReduction(imageData, threshold) {
  if (threshold === 0) return imageData;
  
  const spatialSigma = threshold * 3 + 1;
  const colorSigma = threshold * 50 + 10;
  
  // Apply bilateral filtering
  applyBilateralFilter(imageData, spatialSigma, colorSigma);
  
  return imageData;
}

// Optimized bone removal with reduced complexity
function applyAdvancedBoneRemoval(imageData, intensity) {
  if (intensity === 0) return imageData;
  
  const data = imageData.data;
  const width = imageData.width;
  const height = imageData.height;
  
  // Convert to grayscale for processing
  const grayscale = new Array(width * height);
  for (let i = 0; i < data.length; i += 4) {
    const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    grayscale[i / 4] = gray;
  }
  
  // Use simplified adaptive thresholding for better performance
  const windowSize = 9; // Reduced from 15
  const halfWindow = Math.floor(windowSize / 2);
  
  for (let y = halfWindow; y < height - halfWindow; y += 2) { // Skip every other row for performance
    for (let x = halfWindow; x < width - halfWindow; x += 2) { // Skip every other column
      const centerIdx = y * width + x;
      const pixelIdx = centerIdx * 4;
      
      // Calculate local mean (simplified)
      let sum = 0;
      let count = 0;
      
      for (let dy = -halfWindow; dy <= halfWindow; dy += 2) {
        for (let dx = -halfWindow; dx <= halfWindow; dx += 2) {
          const ny = y + dy;
          const nx = x + dx;
          const nIdx = ny * width + nx;
          sum += grayscale[nIdx];
          count++;
        }
      }
      
      const mean = sum / count;
      const currentGray = grayscale[centerIdx];
      
      // Simplified bone detection
      const threshold = mean + 30; // Fixed threshold for performance
      
      if (currentGray > threshold) {
        const boneStrength = (currentGray - threshold) / (255 - threshold);
        const suppressionFactor = 1 - (intensity * boneStrength * 0.8);
        
        // Apply suppression to current pixel and neighbors
        for (let dy = 0; dy < 2; dy++) {
          for (let dx = 0; dx < 2; dx++) {
            const ny = y + dy;
            const nx = x + dx;
            if (ny < height && nx < width) {
              const nIdx = (ny * width + nx) * 4;
              data[nIdx] *= Math.max(0.1, suppressionFactor);
              data[nIdx + 1] *= Math.max(0.1, suppressionFactor);
              data[nIdx + 2] *= Math.max(0.1, suppressionFactor);
            }
          }
        }
      }
    }
  }
  
  return imageData;
}

// Optimized flesh removal
function applyAdvancedFleshRemoval(imageData, intensity) {
  if (intensity === 0) return imageData;
  
  const data = imageData.data;
  const width = imageData.width;
  const height = imageData.height;
  
  // Simplified flesh removal using global threshold
  const globalThreshold = 80 + (intensity * 50); // Adaptive global threshold
  
  for (let i = 0; i < data.length; i += 4) {
    const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    
    if (gray < globalThreshold) {
      // Soft tissue suppression
      const suppressionFactor = 1 - (intensity * 0.7);
      data[i] *= suppressionFactor;
      data[i + 1] *= suppressionFactor;
      data[i + 2] *= suppressionFactor;
    }
  }
  
  return imageData;
}

// Message handler for the worker
self.onmessage = function(e) {
  const { type, imageData, params, processingId } = e.data;
  
  console.log('Worker received message:', { type, params, processingId, imageSize: `${imageData.width}x${imageData.height}` });
  
  try {
    // Reconstruct ImageData object
    const data = new Uint8ClampedArray(imageData.data);
    const reconstructedImageData = {
      data: data,
      width: imageData.width,
      height: imageData.height
    };
    
    let result;
    
    switch (type) {
      case 'noiseReduction':
        console.log('Applying noise reduction...');
        result = applyNoiseReduction(reconstructedImageData, params.threshold);
        break;
      case 'boneRemoval':
        console.log('Applying bone removal...');
        result = applyAdvancedBoneRemoval(reconstructedImageData, params.intensity);
        break;
      case 'fleshRemoval':
        console.log('Applying flesh removal...');
        result = applyAdvancedFleshRemoval(reconstructedImageData, params.intensity);
        break;
      default:
        throw new Error(`Unknown processing type: ${type}`);
    }
    
    console.log('Worker processing completed for:', type);
    
    // Send result back to main thread
    self.postMessage({
      type: 'processingComplete',
      processingId,
      result: {
        data: result.data,
        width: result.width,
        height: result.height
      }
    });
    
  } catch (error) {
    console.error('Worker processing error:', error);
    self.postMessage({
      type: 'processingError',
      processingId,
      error: error.message
    });
  }
};
