const fs = require('fs');

async function generate() {
  const query = `
    [out:json];
    (
      node["amenity"~"^(library|cafe)$"](18.7906,98.9448,18.8152,98.9635);
      way["amenity"~"^(library|cafe)$"](18.7906,98.9448,18.8152,98.9635);
      relation["amenity"~"^(library|cafe)$"](18.7906,98.9448,18.8152,98.9635);
    )->.places;
    way(around.places:15)["building"];
    out geom;
    .places out geom;
  `;
  
  const rs = await fetch("https://overpass-api.de/api/interpreter", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: "data=" + encodeURIComponent(query)
  });
  
  if (!rs.ok) {
     console.error("Error:", await rs.text());
     process.exit(1);
  }
  
  const data = await rs.json();
  const buildings = data.elements.filter(e => e.tags && e.tags.building);
  const places = data.elements.filter(e => e.tags && e.tags.amenity);
  
  const matchPlaceToPolygon = (p) => {
    let pLat = p.lat || p.center?.lat;
    let pLon = p.lon || p.center?.lon;
    if (!pLat || !pLon) {
      if (p.geometry && p.geometry.length > 0) {
        pLat = p.geometry[0].lat;
        pLon = p.geometry[0].lon;
      } else {
        return null;
      }
    }
    
    if (p.type === "way" || p.type === "relation") return p;
    
    let best = null;
    let minD = 999999;
    for (const b of buildings) {
      if (!b.geometry) continue;
      let bLat = 0, bLon = 0;
      b.geometry.forEach(g => { bLat += g.lat; bLon += g.lon; });
      bLat /= b.geometry.length;
      bLon /= b.geometry.length;
      const d = Math.hypot(pLat - bLat, pLon - bLon);
      if (d < minD && d < 0.0005) { 
        minD = d;
        best = b;
      }
    }
    if (best) return best;
    
    // Synthetic square fallback for points without buildings
    const size = 0.0001;
    return {
      type: "synthetic_polygon",
      id: p.id,
      tags: p.tags,
      geometry: [
        {lat: pLat - size, lon: pLon - size},
        {lat: pLat + size, lon: pLon - size},
        {lat: pLat + size, lon: pLon + size},
        {lat: pLat - size, lon: pLon + size},
        {lat: pLat - size, lon: pLon - size}
      ]
    };
  };
  
  const features = places.map(p => {
    const matched = matchPlaceToPolygon(p);
    if (!matched) return null;
    
    const amenity = p.tags.amenity;
    const name = p.tags.name || amenity;
    
    let coords = [];
    if (matched.type === "way" && matched.geometry) {
       coords = matched.geometry.map(g => [g.lon, g.lat]);
    } else if (matched.type === "relation" && matched.members) {
       const outer = matched.members.find(m => m.role === "outer" && m.geometry);
       if (outer) coords = outer.geometry.map(g => [g.lon, g.lat]);
    } else if (matched.type === "synthetic_polygon") {
       coords = matched.geometry.map(g => [g.lon, g.lat]);
    }
    
    if (coords.length >= 4) {
      return { 
        type: "Feature", 
        properties: { id: p.id, name, amenity, type: "polygon" }, 
        geometry: { type: "Polygon", coordinates: [coords] } 
      };
    }
    return null;
  }).filter(Boolean);

  const collection = { type: "FeatureCollection", features };
  fs.writeFileSync('app/web/places.json', JSON.stringify(collection, null, 2));
  console.log(`Generated app/web/places.json with ${features.length} features.`);
}

generate();
