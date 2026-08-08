import React, { useEffect, useMemo, useRef, useState } from "react";
import {
    AmbientLight,
    BufferGeometry,
    CanvasTexture,
    CircleGeometry,
    Clock,
    Color,
    CylinderGeometry,
    DirectionalLight,
    DoubleSide,
    EdgesGeometry,
    Fog,
    Group,
    Line,
    LineBasicMaterial,
    LineSegments,
    Mesh,
    MeshBasicMaterial,
    MeshStandardMaterial,
    PerspectiveCamera,
    PlaneGeometry,
    PointLight,
    Raycaster,
    RingGeometry,
    Scene,
    SRGBColorSpace,
    Vector2,
    Vector3,
    WebGLRenderer,
} from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { geocodeLocal, isUsCoordinate } from "../geoUtils.js";

const SOURCE_COLORS = {
    sighting: 0x60a5fa,
    hospital: 0x22c55e,
    transportation: 0xfacc15,
    camera: 0xf97316,
    toll: 0xa78bfa,
    cell_provider: 0x38bdf8,
    social_media: 0xf472b6,
    evidence: 0x14b8a6,
    bolo: 0xef4444,
    address: 0x67e8f9,
    school: 0x818cf8,
    work: 0xfbbf24,
    last_seen: 0xef4444,
    other: 0xcbd5e1,
    human_trafficking: 0xf43f5e,
    repeat_offenders: 0xfb7185,
    unidentified_remains: 0xe5e7eb,
    multiple_missing_persons: 0x38bdf8,
    offender_residences: 0xf97316,
    child_exploitation: 0xef4444,
    crime_clusters: 0xfacc15,
    lpr_hits: 0xa78bfa,
    camera_hits: 0x22d3ee,
    gang_territories: 0x8b5cf6,
};

const ANALYSIS_LAYERS = [
    ["human_trafficking", "Human trafficking trends", "#f43f5e"],
    ["repeat_offenders", "Repeat offender locations", "#fb7185"],
    ["unidentified_remains", "Unidentified remains", "#e5e7eb"],
    ["multiple_missing_persons", "Multiple missing persons", "#38bdf8"],
    ["offender_residences", "Known offender residences", "#f97316"],
    ["child_exploitation", "Child exploitation investigations", "#ef4444"],
    ["crime_clusters", "Geographic crime clusters", "#facc15"],
    ["lpr_hits", "License plate reader hits", "#a78bfa"],
    ["camera_hits", "Camera hits", "#22d3ee"],
    ["social_media", "Social media intelligence", "#f472b6"],
    ["gang_territories", "Gang-linked geography", "#8b5cf6"],
];

function hashLocation(value) {
    return [...String(value || "unknown")].reduce(
        (hash, character) => (hash * 31 + character.charCodeAt(0)) % 997,
        17
    );
}

function normalizeCoordinate(value, min, max, fallback) {
    const number = Number(value);
    if (!Number.isFinite(number) || min === max) return fallback;
    return ((number - min) / (max - min) - 0.5) * 28;
}

function createMapTexture() {
    const canvas = document.createElement("canvas");
    canvas.width = 1600;
    canvas.height = 1200;
    const context = canvas.getContext("2d");

    const background = context.createLinearGradient(0, 0, 1600, 1200);
    background.addColorStop(0, "#07111f");
    background.addColorStop(0.5, "#0f172a");
    background.addColorStop(1, "#111827");
    context.fillStyle = background;
    context.fillRect(0, 0, canvas.width, canvas.height);

    context.fillStyle = "rgba(14, 116, 144, 0.26)";
    context.beginPath();
    context.moveTo(0, 825);
    context.bezierCurveTo(280, 720, 420, 910, 650, 800);
    context.bezierCurveTo(880, 690, 1020, 745, 1260, 642);
    context.bezierCurveTo(1425, 570, 1525, 605, 1600, 560);
    context.lineTo(1600, 1200);
    context.lineTo(0, 1200);
    context.closePath();
    context.fill();

    context.strokeStyle = "rgba(148, 163, 184, 0.14)";
    context.lineWidth = 2;
    for (let x = -220; x < 1800; x += 130) {
        context.beginPath();
        context.moveTo(x, 0);
        context.lineTo(x + 340, 1200);
        context.stroke();
    }
    for (let y = 120; y < 1160; y += 112) {
        context.beginPath();
        context.moveTo(0, y);
        context.lineTo(1600, y - 95);
        context.stroke();
    }

    const roads = [
        [[60, 780], [300, 650], [520, 604], [820, 480], [1130, 410], [1550, 250]],
        [[120, 320], [380, 350], [620, 455], [830, 590], [1080, 720], [1510, 850]],
        [[210, 1040], [415, 820], [610, 610], [790, 455], [930, 290], [1050, 90]],
        [[450, 90], [500, 260], [610, 410], [770, 530], [900, 700], [980, 1060]],
        [[70, 585], [290, 560], [500, 575], [710, 650], [990, 675], [1490, 640]],
    ];

    roads.forEach((road, index) => {
        context.strokeStyle = index === 0 ? "rgba(219, 234, 254, 0.46)" : "rgba(147, 197, 253, 0.25)";
        context.lineWidth = index === 0 ? 10 : 6;
        context.lineCap = "round";
        context.lineJoin = "round";
        context.beginPath();
        road.forEach(([x, y], pointIndex) => {
            if (pointIndex === 0) {
                context.moveTo(x, y);
            } else {
                context.lineTo(x, y);
            }
        });
        context.stroke();
    });

    const labels = [
        ["Downtown", 740, 520],
        ["Transit Hub", 420, 620],
        ["Hospital District", 1030, 590],
        ["North Corridor", 930, 260],
        ["River Search Area", 245, 920],
        ["Camera Zone", 1190, 430],
    ];

    context.font = "700 34px Arial";
    context.textAlign = "center";
    labels.forEach(([label, x, y]) => {
        context.fillStyle = "rgba(2, 6, 23, 0.74)";
        context.fillRect(x - 160, y - 36, 320, 56);
        context.strokeStyle = "rgba(96, 165, 250, 0.24)";
        context.strokeRect(x - 160, y - 36, 320, 56);
        context.fillStyle = "rgba(226, 232, 240, 0.82)";
        context.fillText(label, x, y);
    });

    const texture = new CanvasTexture(canvas);
    texture.colorSpace = SRGBColorSpace;
    texture.anisotropy = 8;
    return texture;
}

function buildMapPoints(sightings, records, mappedLocations = []) {
    const hasCoordinates = (latitude, longitude) =>
        latitude !== null && latitude !== undefined && latitude !== "" &&
        longitude !== null && longitude !== undefined && longitude !== "" &&
        Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude));
    const coordinateEntries = [
        ...sightings
            .filter((sighting) =>
                hasCoordinates(sighting.latitude, sighting.longitude) &&
                isUsCoordinate(sighting.latitude, sighting.longitude)
            )
            .map((sighting, index) => ({
                id: `sighting-${sighting.sighting_id ?? index}`,
                type: "sighting",
                title: sighting.location || `Sighting ${index + 1}`,
                detail: sighting.description || "Reported sighting",
                caseId: sighting.case_id,
                confidence: Number(sighting.confidence_score ?? 0.35),
                analysisLayer: sighting.analysis_layer || "crime_clusters",
                latitude: Number(sighting.latitude),
                longitude: Number(sighting.longitude),
            })),
        ...mappedLocations
            .filter((location) =>
                hasCoordinates(location.latitude, location.longitude) &&
                isUsCoordinate(location.latitude, location.longitude)
            )
            .map((location, index) => ({
                id: location.id || `mapped-${index}`,
                type: location.type || "address",
                title: location.title || location.label || "Mapped case location",
                detail: location.detail || location.address || "Case geography",
                caseId: location.caseId || location.case_id,
                confidence: Number(location.confidence ?? 0.62),
                analysisLayer: location.analysisLayer || location.analysis_layer || "multiple_missing_persons",
                latitude: Number(location.latitude),
                longitude: Number(location.longitude),
            })),
        ...records
            .map((record, index) => {
                const geocoded =
                    hasCoordinates(record.latitude, record.longitude)
                        ? {
                            latitude: Number(record.latitude),
                            longitude: Number(record.longitude),
                        }
                        : geocodeLocal(record.location);

                if (!geocoded || !isUsCoordinate(geocoded.latitude, geocoded.longitude)) return null;

                return {
                    id: `record-${record.id ?? index}`,
                    type: record.record_type || "other",
                    title: record.location || record.record_type || "External record",
                    detail: record.notes || "Partner-provided intelligence",
                    caseId: record.case_id,
                    confidence: record.geocode_score
                        ? Math.max(0.35, Math.min(Number(record.geocode_score) / 100, 0.95))
                        : 0.55,
                    analysisLayer: record.analysis_layer || "crime_clusters",
                    latitude: geocoded.latitude,
                    longitude: geocoded.longitude,
                };
            })
            .filter(Boolean),
    ];

    const latitudes = coordinateEntries.map((entry) => Number(entry.latitude));
    const longitudes = coordinateEntries.map((entry) => Number(entry.longitude));
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);
    const bounds = {
        minLat: minLat === maxLat ? minLat - 0.02 : minLat,
        maxLat: minLat === maxLat ? maxLat + 0.02 : maxLat,
        minLng: minLng === maxLng ? minLng - 0.02 : minLng,
        maxLng: minLng === maxLng ? maxLng + 0.02 : maxLng,
    };

    const coordinatePoints = coordinateEntries.map((entry, index) => ({
        ...entry,
        x: normalizeCoordinate(entry.longitude, bounds.minLng, bounds.maxLng, -12 + index * 3),
        z: normalizeCoordinate(entry.latitude, bounds.minLat, bounds.maxLat, -6 + index * 2),
    }));

    const recordPoints = records.slice(0, 24).map((record, index) => {
        const seed = hashLocation(`${record.location}-${record.record_type}-${index}`);
        return {
            id: `record-${record.id ?? index}`,
            type: record.record_type || "other",
            title: record.location || record.record_type || "External record",
            detail: record.notes || "Partner-provided intelligence",
            caseId: record.case_id,
            confidence: 0.48 + (seed % 45) / 100,
            analysisLayer: record.analysis_layer || "crime_clusters",
            x: ((seed % 29) - 14) + (index % 3) * 0.4,
            z: (((seed * 7) % 25) - 12) + (index % 2) * 0.6,
        };
    });

    const coordinatePointIds = new Set(coordinatePoints.map((point) => point.id));

    return [
        ...coordinatePoints,
        ...recordPoints.filter((point) => !coordinatePointIds.has(point.id)),
    ];
}

function IntelligenceMap3D({ sightings, records, mappedLocations = [] }) {
    const mountRef = useRef(null);
    const markerRefs = useRef([]);
    const raycasterRef = useRef(new Raycaster());
    const pointerRef = useRef(new Vector2());
    const [selectedPoint, setSelectedPoint] = useState(null);
    const [activeLayers, setActiveLayers] = useState(() => new Set(ANALYSIS_LAYERS.map(([id]) => id)));

    const points = useMemo(
        () => buildMapPoints(sightings, records, mappedLocations),
        [sightings, records, mappedLocations]
    );
    const visiblePoints = useMemo(
        () => points.filter((point) => activeLayers.has(point.analysisLayer)),
        [points, activeLayers]
    );
    const layerCounts = useMemo(() => points.reduce((counts, point) => ({
        ...counts,
        [point.analysisLayer]: (counts[point.analysisLayer] || 0) + 1,
    }), {}), [points]);
    const clusterCount = useMemo(() => {
        const occupiedCells = new Map();
        visiblePoints.forEach((point) => {
            const key = `${point.analysisLayer}:${Math.round(point.x / 4)}:${Math.round(point.z / 4)}`;
            occupiedCells.set(key, (occupiedCells.get(key) || 0) + 1);
        });
        return [...occupiedCells.values()].filter((count) => count > 1).length;
    }, [visiblePoints]);

    const toggleLayer = (layerId) => {
        setActiveLayers((current) => {
            const next = new Set(current);
            if (next.has(layerId)) next.delete(layerId);
            else next.add(layerId);
            return next;
        });
    };

    useEffect(() => {
        const mount = mountRef.current;
        if (!mount) return undefined;

        const scene = new Scene();
        scene.background = new Color(0x020617);
        scene.fog = new Fog(0x020617, 22, 72);

        const camera = new PerspectiveCamera(48, 1, 0.1, 160);
        camera.position.set(0, 22, 34);

        const renderer = new WebGLRenderer({
            antialias: true,
            alpha: false,
        });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.outputColorSpace = SRGBColorSpace;
        renderer.domElement.className = "intelligence-3d-canvas";
        mount.appendChild(renderer.domElement);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.maxPolarAngle = Math.PI * 0.48;
        controls.minDistance = 16;
        controls.maxDistance = 58;
        controls.target.set(0, 0, 0);

        scene.add(new AmbientLight(0x8fb4ff, 0.42));

        const keyLight = new DirectionalLight(0xeff6ff, 2.4);
        keyLight.position.set(-10, 22, 18);
        scene.add(keyLight);

        const blueLight = new PointLight(0x2563eb, 42, 58);
        blueLight.position.set(12, 11, -14);
        scene.add(blueLight);

        const groundGeometry = new PlaneGeometry(40, 34, 1, 1);
        const groundMaterial = new MeshStandardMaterial({
            color: 0xffffff,
            map: createMapTexture(),
            roughness: 0.9,
            metalness: 0.14,
        });
        const ground = new Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.03;
        scene.add(ground);

        const border = new LineSegments(
            new EdgesGeometry(groundGeometry),
            new LineBasicMaterial({
                color: 0x60a5fa,
                transparent: true,
                opacity: 0.36,
            })
        );
        border.rotation.x = -Math.PI / 2;
        border.position.y = 0.01;
        scene.add(border);

        const routeMaterial = new LineBasicMaterial({
            color: 0x93c5fd,
            transparent: true,
            opacity: 0.46,
        });
        const routePoints = visiblePoints
            .slice(0, 10)
            .map((point) => new Vector3(point.x, 0.18, point.z));
        if (routePoints.length > 1) {
            const route = new Line(
                new BufferGeometry().setFromPoints(routePoints),
                routeMaterial
            );
            scene.add(route);
        }

        const markerGroup = new Group();
        markerRefs.current = [];

        const clusterCells = new Map();
        visiblePoints.forEach((point) => {
            const key = `${point.analysisLayer}:${Math.round(point.x / 4)}:${Math.round(point.z / 4)}`;
            const cell = clusterCells.get(key) || [];
            cell.push(point);
            clusterCells.set(key, cell);
        });
        clusterCells.forEach((cluster) => {
            if (cluster.length < 2) return;
            const color = SOURCE_COLORS[cluster[0].analysisLayer] ?? SOURCE_COLORS.other;
            const centerX = cluster.reduce((sum, point) => sum + point.x, 0) / cluster.length;
            const centerZ = cluster.reduce((sum, point) => sum + point.z, 0) / cluster.length;
            const clusterDisc = new Mesh(
                new CircleGeometry(Math.min(4.2, 1.4 + cluster.length * 0.42), 48),
                new MeshBasicMaterial({
                    color,
                    transparent: true,
                    opacity: 0.13,
                    side: DoubleSide,
                    depthWrite: false,
                })
            );
            clusterDisc.rotation.x = -Math.PI / 2;
            clusterDisc.position.set(centerX, 0.05, centerZ);
            markerGroup.add(clusterDisc);
        });

        visiblePoints.forEach((point, index) => {
            const color = SOURCE_COLORS[point.analysisLayer] ?? SOURCE_COLORS[point.type] ?? SOURCE_COLORS.other;
            const height = 0.8 + Math.max(point.confidence, 0.25) * 4.2;

            const tower = new Mesh(
                new CylinderGeometry(0.18, 0.28, height, 24),
                new MeshStandardMaterial({
                    color,
                    emissive: color,
                    emissiveIntensity: 0.38,
                    roughness: 0.42,
                    metalness: 0.3,
                })
            );
            tower.position.set(point.x, height / 2, point.z);
            tower.userData = { point };
            markerGroup.add(tower);
            markerRefs.current.push(tower);

            const pulse = new Mesh(
                new RingGeometry(0.6, 0.72, 48),
                new MeshBasicMaterial({
                    color,
                    transparent: true,
                    opacity: 0.45,
                    side: DoubleSide,
                })
            );
            pulse.rotation.x = -Math.PI / 2;
            pulse.position.set(point.x, 0.08, point.z);
            pulse.userData = { speed: 0.9 + (index % 5) * 0.12 };
            markerGroup.add(pulse);
        });

        scene.add(markerGroup);

        const resize = () => {
            const { clientWidth, clientHeight } = mount;
            const width = Math.max(clientWidth, 320);
            const height = Math.max(clientHeight, 420);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height, false);
        };

        const onPointerDown = (event) => {
            const bounds = renderer.domElement.getBoundingClientRect();
            pointerRef.current.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
            pointerRef.current.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
            raycasterRef.current.setFromCamera(pointerRef.current, camera);

            const [hit] = raycasterRef.current.intersectObjects(markerRefs.current);
            setSelectedPoint(hit?.object?.userData?.point ?? null);
        };

        const resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(mount);
        renderer.domElement.addEventListener("pointerdown", onPointerDown);
        resize();

        let frameId = 0;
        const clock = new Clock();

        const animate = () => {
            const elapsed = clock.getElapsedTime();
            markerGroup.children.forEach((child) => {
                if (child.geometry?.type === "RingGeometry") {
                    const scale = 1 + (Math.sin(elapsed * child.userData.speed) + 1) * 0.24;
                    child.scale.setScalar(scale);
                    child.material.opacity = 0.22 + Math.sin(elapsed * child.userData.speed) * 0.12;
                }
            });
            controls.update();
            renderer.render(scene, camera);
            frameId = window.requestAnimationFrame(animate);
        };

        animate();

        return () => {
            window.cancelAnimationFrame(frameId);
            resizeObserver.disconnect();
            renderer.domElement.removeEventListener("pointerdown", onPointerDown);
            controls.dispose();
            mount.removeChild(renderer.domElement);

            scene.traverse((object) => {
                object.geometry?.dispose?.();
                if (Array.isArray(object.material)) {
                    object.material.forEach((material) => material.dispose());
                } else {
                    object.material?.dispose?.();
                }
            });
            renderer.dispose();
        };
    }, [visiblePoints]);

    const summary = selectedPoint && activeLayers.has(selectedPoint.analysisLayer)
        ? selectedPoint
        : visiblePoints[0];

    return (
        <div className="intelligence-analysis-workspace">
            <aside className="intelligence-layer-panel">
                <div className="intelligence-layer-summary">
                    <span>Pattern engine</span>
                    <strong>{clusterCount}</strong>
                    <small>multi-point clusters visible</small>
                </div>
                {ANALYSIS_LAYERS.map(([id, label, color]) => (
                    <button
                        key={id}
                        type="button"
                        className={activeLayers.has(id) ? "active" : ""}
                        onClick={() => toggleLayer(id)}
                    >
                        <i style={{ backgroundColor: color }}></i>
                        <span>{label}</span>
                        <strong>{layerCounts[id] || 0}</strong>
                    </button>
                ))}
            </aside>
            <div className="intelligence-3d-shell">
                <div ref={mountRef} className="intelligence-3d-stage" />
            <div className="intelligence-3d-overlay">
                <div>
                    <span>Selected Intelligence Signal</span>
                    <strong>{summary ? summary.title : "No mapped data"}</strong>
                    {summary && (
                        <p>
                            {summary.detail}
                            {summary.caseId ? ` | Case ${summary.caseId}` : ""}
                        </p>
                    )}
                </div>
            </div>
            </div>
        </div>
    );
}

export default IntelligenceMap3D;
