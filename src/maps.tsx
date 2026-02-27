import L from "leaflet";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";
import {
  getEntityAddresses,
  getNearbyCaseAddresses,
  MapEntityResponse,
} from "./api/types";

// Fix default marker icon paths broken by bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl });

const TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

function createTileLayer() {
  return L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION });
}

function getMarkerColor(status: MapEntityResponse["addresses"][0]["status"]) {
  const labelColor = status ? status[2] : null;
  return (
    { green: "#0c7556", yellow: "#755600", red: "#A33417" }[labelColor] ||
    "#0D2475"
  );
}

function createCircleMarker(
  lat: number,
  lon: number,
  title: string,
  color: string
) {
  return L.circleMarker([lat, lon], {
    radius: 8,
    fillColor: color,
    color: color,
    weight: 2,
    opacity: 1,
    fillOpacity: 0.7,
  }).bindPopup(title);
}

// Render map only when it is in the viewport
document.addEventListener("lazybeforeunveil", function (e) {
  let el = e.target;
  if (el instanceof HTMLElement && el.classList.contains("map")) {
    const lat = parseFloat(el.dataset.lat);
    const lon = parseFloat(el.dataset.lon);
    const address = el.dataset.address || "";

    const map = L.map(el).setView([lat, lon], 14);
    createTileLayer().addTo(map);

    const marker = L.marker([lat, lon]).addTo(map);
    if (address) marker.bindPopup(address);
  }
});

function getMarkersForAddresses(addresses: MapEntityResponse["addresses"]) {
  return addresses.map(({ lat, lon, label, status }) =>
    createCircleMarker(lat, lon, label, getMarkerColor(status))
  );
}

interface FrontpagePin {
  lat: number;
  lon: number;
  label: string;
  status_color: string | null;
  headline: string;
  url: string;
}

function getFrontpageMarkerColor(color: string | null): string {
  return (
    { green: "#0c7556", yellow: "#755600", red: "#A33417" }[color] || "#0D2475"
  );
}

export function renderFrontpageMap(el: HTMLElement) {
  const scriptEl = el.querySelector<HTMLScriptElement>(
    'script[type="application/json"]'
  );
  if (!scriptEl) return;

  const pins: FrontpagePin[] = JSON.parse(scriptEl.textContent || "[]");
  if (pins.length === 0) return;

  const map = L.map(el).setView([64.14, -21.88], 13);
  createTileLayer().addTo(map);

  const markers = pins.map((pin) => {
    const color = getFrontpageMarkerColor(pin.status_color);
    const popupHtml = `<a href="${pin.url}" class="text-sm font-bold">${pin.label}</a>${pin.headline ? `<br><span class="text-xs">${pin.headline}</span>` : ""}`;
    return createCircleMarker(pin.lat, pin.lon, popupHtml, color);
  });

  const group = L.featureGroup(markers).addTo(map);
  map.fitBounds(group.getBounds().pad(0.1));
}

export function renderEntityMap(el: HTMLElement, kennitala: string) {
  return getEntityAddresses(kennitala).then(({ addresses }) => {
    if (addresses.length === 0) return;
    const map = L.map(el);
    createTileLayer().addTo(map);
    const markers = getMarkersForAddresses(addresses);
    const group = L.featureGroup(markers).addTo(map);
    map.fitBounds(group.getBounds().pad(0.1));
  });
}

export function renderNearbyMap(
  el: HTMLElement,
  opts: { hnitnum: string; radius: string; days: string }
) {
  return getNearbyCaseAddresses(parseInt(opts.hnitnum, 10), {
    days: parseInt(opts.days, 10),
    radius: parseInt(opts.radius, 10),
  }).then(({ address, addresses, plan }) => {
    if (addresses.length === 0) return;
    const map = L.map(el);
    createTileLayer().addTo(map);

    const markers = getMarkersForAddresses(addresses);

    // Add the main address marker
    markers.push(
      createCircleMarker(address.lat, address.lon, address.label, "#2A1F6F")
    );

    const group = L.featureGroup(markers).addTo(map);

    // Add plan polygon overlay if present
    if (plan !== null) {
      const polygon = L.polygon(
        (plan.polygon as [number, number][]).map(([x, y]) => [x, y]),
        {
          color: "#333",
          weight: 2,
          opacity: 0.2,
          fillOpacity: 0.05,
          lineJoin: "round",
        }
      ).addTo(map);
      group.addLayer(polygon);
    }

    map.fitBounds(group.getBounds().pad(0.1));
  });
}
