import * as THREE from 'three';
import config from '../../assets/data/game.json';
import { FixedStep } from '../core/step';
import { createGame } from '../gameplay/game';
import { bindInput } from '../gameplay/input';
import { bindHud } from '../ui/hud';

/** One owner for loop, input, resize observer, meshes and GPU allocations. */
export function startCollect(host: HTMLElement): () => void {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.domElement.style.width = '100%'; renderer.domElement.style.height = '100%';
  host.append(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#182c36');
  const camera = new THREE.OrthographicCamera(0, config.width, 0, config.height, 0.1, 1000);
  camera.position.z = 600;
  scene.add(new THREE.AmbientLight(0xffffff, 2));
  const light = new THREE.DirectionalLight(0xffffff, 3);
  light.position.set(100, 80, 300); scene.add(light);
  const playerGeometry = new THREE.SphereGeometry(config.radius, 24, 16);
  const playerMaterial = new THREE.MeshStandardMaterial({ color: '#8ee2d2', roughness: 0.45 });
  const pickupGeometry = new THREE.OctahedronGeometry(config.pickupRadius);
  const pickupMaterial = new THREE.MeshStandardMaterial({ color: '#f8ca6a', roughness: 0.45 });
  const player = new THREE.Mesh(playerGeometry, playerMaterial);
  scene.add(player);
  const pickups = config.pickups.map(point => {
    const mesh = new THREE.Mesh(pickupGeometry, pickupMaterial);
    mesh.position.set(point.x, point.y, 0); scene.add(mesh); return mesh;
  });
  const grid = new THREE.GridHelper(config.width, 20, 0x27434e, 0x27434e);
  grid.rotation.x = Math.PI / 2; grid.position.set(config.width / 2, config.height / 2, -20);
  scene.add(grid);
  const simulation = createGame(config);
  const clock = new FixedStep(config.tick);
  const controls = bindInput(renderer.domElement, config);
  const hud = bindHud(config.pickups.length, () => {
    simulation.reset(); clock.reset(); controls.clear(); renderState();
  });
  function renderState(): void {
    const state = simulation.state;
    player.position.set(state.x, state.y, 0);
    for (let i = 0; i < pickups.length; i++) pickups[i].visible = !state.collected[i];
    hud.render(state);
    renderer.render(scene, camera);
  }
  function resize(): void {
    renderer.setSize(host.clientWidth, host.clientHeight, false);
    renderState();
  }
  const observer = new ResizeObserver(resize); observer.observe(host); resize();
  let previous: number | null = null;
  const simulate = (dt: number): void => {
    const direction = controls.sample(simulation.state, dt);
    simulation.step(direction.x, direction.y, dt);
  };
  renderer.setAnimationLoop(time => {
    if (previous !== null) clock.advance((time - previous) / 1000, simulate);
    previous = time; renderState();
  });
  let disposed = false;
  return () => {
    if (disposed) return;
    disposed = true;
    renderer.setAnimationLoop(null); observer.disconnect(); controls.dispose(); hud.dispose();
    scene.clear();
    playerGeometry.dispose(); playerMaterial.dispose(); pickupGeometry.dispose(); pickupMaterial.dispose();
    grid.geometry.dispose();
    if (Array.isArray(grid.material)) grid.material.forEach(material => material.dispose());
    else grid.material.dispose();
    renderer.dispose(); renderer.domElement.remove();
  };
}
