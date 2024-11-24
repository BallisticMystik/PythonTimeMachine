/* global THREE */
document.addEventListener('DOMContentLoaded', () => {
    if (typeof THREE === 'undefined') {
        console.error('THREE is not defined. Make sure three.js is loaded properly.');
        return;
    }
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('canvas-container').appendChild(renderer.domElement);
  
    // Create road geometry
    const roadGeometry = new THREE.PlaneGeometry(20, 80000, 20, 8000);
    const roadMaterial = new THREE.MeshBasicMaterial({ 
      color: 0x00ff00, 
      wireframe: true,
      transparent: true,
      opacity: 0.5
    });
    const road = new THREE.Mesh(roadGeometry, roadMaterial);
    road.rotation.x = -Math.PI / 2;
    road.position.z = -40000;
    scene.add(road);
  
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);
  
    // Add point light
    const pointLight = new THREE.PointLight(0xff00ff, 1, 100);
    pointLight.position.set(0, 10, 50);
    scene.add(pointLight);
  
    // Create stars
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.1 });
    
    const starsVertices = [];
    for (let i = 0; i < 20000; i++) {
      const x = (Math.random() - 0.5) * 2000;
      const y = Math.random() * 1000;
      const z = (Math.random() - 0.5) * 2000;
      starsVertices.push(x, y, z);
    }
    
    starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starsVertices, 3));
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);
  
    camera.position.z = 5;
    camera.position.y = 2;
  
    const roadSpeed = 400;
    const starsSpeed = 0.2;
  
    function animate() {
      requestAnimationFrame(animate);
      road.position.z += roadSpeed;
      if (road.position.z > 40000) {
        road.position.z = -40000;
      }
      
      // Animate stars
      const starsPositions = stars.geometry.attributes.position.array;
      for (let i = 0; i < starsPositions.length; i += 3) {
        starsPositions[i + 2] += starsSpeed;
        if (starsPositions[i + 2] > 1000) {
          starsPositions[i + 2] = -1000;
        }
      }
      stars.geometry.attributes.position.needsUpdate = true;
      
      renderer.render(scene, camera);
    }
  
    animate();
  
    // Handle window resize
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  });