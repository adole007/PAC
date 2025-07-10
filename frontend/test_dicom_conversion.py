import os
import sys
import pydicom
import numpy as np
from PIL import Image
import base64
import io

def process_dicom_file(file_path):
    """Test the DICOM processing function with the provided file"""
    print(f"Testing DICOM file: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        print(f"✅ File read successfully: {len(file_content):,} bytes")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Process DICOM file (same logic as backend)
    try:
        # Read DICOM file with force=True to handle files without proper headers
        ds = pydicom.dcmread(io.BytesIO(file_content), force=True)
        print(f"✅ DICOM file parsed successfully")
        
        # Print basic DICOM info
        print(f"📋 Patient Name: {getattr(ds, 'PatientName', 'N/A')}")
        print(f"📋 Study Description: {getattr(ds, 'StudyDescription', 'N/A')}")
        print(f"📋 Modality: {getattr(ds, 'Modality', 'N/A')}")
        print(f"📋 Image Type: {getattr(ds, 'ImageType', 'N/A')}")
        
        # Extract metadata
        metadata = {}
        for elem in ds:
            if elem.tag.group != 0x7fe0:  # Skip pixel data
                try:
                    metadata[str(elem.tag)] = str(elem.value)
                except:
                    pass
        
        print(f"📋 Extracted {len(metadata)} metadata elements")
        
        # Extract image data
        if hasattr(ds, 'pixel_array'):
            try:
                pixel_array = ds.pixel_array
                print(f"✅ Pixel array extracted successfully")
                print(f"📊 Original pixel array shape: {pixel_array.shape}")
                print(f"📊 Original pixel array dtype: {pixel_array.dtype}")
                print(f"📊 Original pixel array range: {pixel_array.min()} to {pixel_array.max()}")
                
                # Handle different pixel array types
                if len(pixel_array.shape) == 3:
                    print(f"⚠️  Multi-dimensional array detected")
                    # Multi-frame or color image - take first frame or convert to grayscale
                    if pixel_array.shape[2] == 3:  # RGB
                        pixel_array = np.mean(pixel_array, axis=2)  # Convert to grayscale
                        print(f"🔄 Converted RGB to grayscale")
                    else:
                        pixel_array = pixel_array[:, :, 0]  # Take first frame
                        print(f"🔄 Extracted first frame")
                
                # Apply windowing if available
                window_center = getattr(ds, 'WindowCenter', None)
                window_width = getattr(ds, 'WindowWidth', None)
                
                if window_center and window_width:
                    # Convert to appropriate type
                    if isinstance(window_center, (list, tuple)):
                        window_center = float(window_center[0])
                    else:
                        window_center = float(window_center)
                        
                    if isinstance(window_width, (list, tuple)):
                        window_width = float(window_width[0])
                    else:
                        window_width = float(window_width)
                    
                    # Apply windowing
                    img_min = window_center - window_width / 2
                    img_max = window_center + window_width / 2
                    pixel_array = np.clip(pixel_array, img_min, img_max)
                    print(f"🔄 Applied windowing: center={window_center}, width={window_width}")
                
                # Normalize to 0-255 range with safe division
                pixel_min = pixel_array.min()
                pixel_max = pixel_array.max()
                
                if pixel_max == pixel_min:
                    # Handle case where all pixels have the same value
                    print(f"⚠️  All pixels have the same value, creating uniform image")
                    pixel_array = np.full_like(pixel_array, 128, dtype=np.uint8)
                else:
                    # Safe normalization
                    pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
                
                print(f"🔄 Normalized pixel array range: {pixel_array.min()} to {pixel_array.max()}")
                
                # Convert to PIL Image
                if pixel_array.dtype != np.uint8:
                    pixel_array = pixel_array.astype(np.uint8)
                    
                # Get original dimensions from DICOM
                original_height, original_width = pixel_array.shape
                print(f"📐 Original DICOM dimensions: {original_width}x{original_height}")
                
                # Create PIL Image with original dimensions preserved
                image = Image.fromarray(pixel_array, mode='L')  # Grayscale mode
                print(f"✅ PIL Image created: {image.size}, mode: {image.mode}")
                
                # Verify the image maintains original dimensions
                if image.size != (original_width, original_height):
                    print(f"⚠️  Image size mismatch: PIL={image.size}, DICOM=({original_width}x{original_height})")
                    # Resize to match original DICOM dimensions if needed
                    image = image.resize((original_width, original_height), Image.Resampling.LANCZOS)
                    print(f"🔄 Resized image to match original dimensions: {image.size}")
                else:
                    print(f"✅ Image dimensions preserved correctly: {image.size}")
                
                # Create thumbnail
                thumbnail = image.copy()
                thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
                print(f"✅ Thumbnail created: {thumbnail.size}")
                
                # Convert to base64
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                
                thumb_buffer = io.BytesIO()
                thumbnail.save(thumb_buffer, format='PNG')
                thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                
                print(f"✅ Successfully converted to PNG format")
                print(f"📊 Final image dimensions: {image.size} (preserved from DICOM)")
                print(f"📊 Main image PNG size: {len(img_buffer.getvalue()):,} bytes")
                print(f"📊 Thumbnail PNG size: {len(thumb_buffer.getvalue()):,} bytes")
                print(f"📊 Base64 image data length: {len(img_base64):,} characters")
                print(f"📊 Base64 thumbnail data length: {len(thumb_base64):,} characters")
                
                # Test if we can decode the base64 back to image
                try:
                    test_img_bytes = base64.b64decode(img_base64)
                    test_img = Image.open(io.BytesIO(test_img_bytes))
                    print(f"✅ Base64 to image conversion test passed: {test_img.size}, mode: {test_img.mode}")
                except Exception as e:
                    print(f"❌ Base64 to image conversion test failed: {e}")
                
                # Save test images to disk for verification
                try:
                    output_dir = "test_output"
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Save main image
                    main_path = os.path.join(output_dir, "converted_main.png")
                    image.save(main_path)
                    print(f"💾 Main image saved to: {main_path}")
                    
                    # Save thumbnail
                    thumb_path = os.path.join(output_dir, "converted_thumbnail.png")
                    thumbnail.save(thumb_path)
                    print(f"💾 Thumbnail saved to: {thumb_path}")
                    
                except Exception as e:
                    print(f"⚠️  Could not save test images: {e}")
                
                result = {
                    'metadata': metadata,
                    'image_data': img_base64,
                    'thumbnail_data': thumb_base64,
                    'window_center': float(window_center) if window_center else None,
                    'window_width': float(window_width) if window_width else None,
                    'success': True
                }
                
                print(f"✅ DICOM processing completed successfully!")
                return result
                
            except Exception as img_error:
                print(f"❌ Error processing DICOM pixel array: {str(img_error)}")
                import traceback
                traceback.print_exc()
                return {
                    'metadata': metadata,
                    'image_data': None,
                    'thumbnail_data': None,
                    'window_center': None,
                    'window_width': None,
                    'success': False,
                    'error': str(img_error)
                }
        else:
            print(f"❌ No pixel array found in DICOM file")
            return {
                'metadata': metadata,
                'image_data': None,
                'thumbnail_data': None,
                'window_center': None,
                'window_width': None,
                'success': False,
                'error': 'No pixel array found'
            }
        
    except Exception as e:
        print(f"❌ Error processing DICOM file: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("=== DICOM to PNG Conversion Test ===")
    
    # Test file path
    dicom_file = r"C:\Users\Tony\Music\Altea_t2_stir_sag_DR_88115187.dcm"
    
    result = process_dicom_file(dicom_file)
    
    print("\n=== Test Results ===")
    if result and result.get('success'):
        print("✅ DICOM file successfully processed and converted to PNG!")
        print("✅ The backend should be able to handle this file correctly")
        
        if result.get('image_data'):
            print("✅ Main image data available for database storage")
        if result.get('thumbnail_data'):
            print("✅ Thumbnail data available for database storage")
            
    else:
        print("❌ DICOM processing failed!")
        if result and result.get('error'):
            print(f"❌ Error: {result['error']}")
        print("❌ This file may cause issues in the PAC system")

if __name__ == "__main__":
    main()
