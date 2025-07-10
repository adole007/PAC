// Test script to verify frontend-backend communication
// Run this in the browser console on the frontend page

async function testBackendConnection() {
    const BASE_URL = 'http://localhost:8000/api';
    
    console.log('🔄 Testing backend connection...');
    
    // Test 1: Health check
    try {
        const healthResponse = await fetch('http://localhost:8000/health');
        if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            console.log('✅ Health check passed:', healthData);
        } else {
            console.log('❌ Health check failed:', healthResponse.status);
            return;
        }
    } catch (error) {
        console.log('❌ Health check error:', error);
        return;
    }
    
    // Test 2: Login
    let token;
    try {
        const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'clinician',
                password: 'admin123'
            })
        });
        
        if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            token = loginData.access_token;
            console.log('✅ Login successful, token:', token.substring(0, 20) + '...');
        } else {
            console.log('❌ Login failed:', loginResponse.status);
            return;
        }
    } catch (error) {
        console.log('❌ Login error:', error);
        return;
    }
    
    // Test 3: Get patients
    try {
        const patientsResponse = await fetch(`${BASE_URL}/patients`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (patientsResponse.ok) {
            const patients = await patientsResponse.json();
            console.log('✅ Patients fetched:', patients.length, 'patients');
            
            if (patients.length > 0) {
                const firstPatient = patients[0];
                console.log('First patient:', firstPatient.id, firstPatient.first_name, firstPatient.last_name);
                
                // Test 4: Get patient images
                try {
                    const imagesResponse = await fetch(`${BASE_URL}/patients/${firstPatient.id}/images`, {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (imagesResponse.ok) {
                        const images = await imagesResponse.json();
                        console.log('✅ Patient images fetched:', images.length, 'images');
                        
                        if (images.length > 0) {
                            const firstImage = images[0];
                            console.log('First image:', firstImage.id, firstImage.modality, firstImage.original_filename);
                            
                            // Test 5: Get image data
                            try {
                                const imageDataResponse = await fetch(`${BASE_URL}/images/${firstImage.id}/data`, {
                                    headers: {
                                        'Authorization': `Bearer ${token}`
                                    }
                                });
                                
                                if (imageDataResponse.ok) {
                                    const blob = await imageDataResponse.blob();
                                    console.log('✅ Image data fetched:', blob.size, 'bytes, type:', blob.type);
                                    
                                    // Test 6: Create and display image
                                    const url = URL.createObjectURL(blob);
                                    const img = document.createElement('img');
                                    img.src = url;
                                    img.style.maxWidth = '300px';
                                    img.style.border = '2px solid green';
                                    img.onload = () => {
                                        console.log('✅ Image displayed successfully');
                                        URL.revokeObjectURL(url);
                                    };
                                    img.onerror = () => {
                                        console.log('❌ Image display failed');
                                        URL.revokeObjectURL(url);
                                    };
                                    document.body.appendChild(img);
                                    
                                } else {
                                    console.log('❌ Image data fetch failed:', imageDataResponse.status);
                                }
                            } catch (error) {
                                console.log('❌ Image data fetch error:', error);
                            }
                        } else {
                            console.log('⚠️  No images found for patient');
                        }
                    } else {
                        console.log('❌ Patient images fetch failed:', imagesResponse.status);
                    }
                } catch (error) {
                    console.log('❌ Patient images fetch error:', error);
                }
            } else {
                console.log('⚠️  No patients found');
            }
        } else {
            console.log('❌ Patients fetch failed:', patientsResponse.status);
        }
    } catch (error) {
        console.log('❌ Patients fetch error:', error);
    }
    
    console.log('🔄 Backend connection test completed');
}

// Call the test function
testBackendConnection();
