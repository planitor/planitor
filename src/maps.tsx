import {
  getEntityAddresses,
  getNearbyCaseAddresses,
  MapEntityResponse,
} from "./api/types";

export let mapkit = globalThis["mapkit"];

// Render map only when it is in the viewport
document.addEventListener("lazybeforeunveil", function (e) {
  let el = e.target;
  if (el instanceof HTMLElement && el.classList.contains("map")) {
    var address = new mapkit.Coordinate(
      parseFloat(el.dataset.lat),
      parseFloat(el.dataset.lon)
    );
    var region = new mapkit.CoordinateRegion(
      address,
      new mapkit.CoordinateSpan(0.03, 0.04)
    );
    var map = new mapkit.Map(el);

    var addressAnnotation = new mapkit.MarkerAnnotation(address, {
      color: "#f4a56d",
      title: el.dataset.address,
    });
    map.showItems([addressAnnotation]);

    map.region = region;
  }
});

function getRegion(coordinateSets) {
  var north = coordinateSets[0].lat,
    south = north,
    west = coordinateSets[0].lon,
    east = west;

  if (coordinateSets.length === 1) {
    return new mapkit.CoordinateRegion(
      new mapkit.Coordinate(north, west),
      new mapkit.CoordinateSpan(0.01, 0.01)
    );
  }

  // Shift direction variables to the outermost parts of pins to create a boundary region
  for (var coordinates of coordinateSets) {
    const { lat, lon } = coordinates;
    if (lat > north) north = lat;
    if (lat < south) south = lat;
    if (lon < west) west = lon;
    if (lon > east) east = lon;
  }

  const latDiff = Math.abs(north - south) * 0.1;
  const lonDiff = Math.abs(east - west) * 0.1;
  return new mapkit.BoundingRegion(
    north + latDiff,
    east + lonDiff,
    south - latDiff,
    west - lonDiff
  ).toCoordinateRegion();
}

function getMarkersForAddresses(addresses: MapEntityResponse["addresses"]) {
  var pins = [];
  for (var address of addresses) {
    const { lat, lon, label, status } = address;
    const labelColor = status ? status[2] : null;
    pins.push(
      new mapkit.MarkerAnnotation(new mapkit.Coordinate(lat, lon), {
        title: label,
        color:
          { green: "#0c7556", yellow: "#755600", red: "#A33417" }[labelColor] ||
          "#0D2475",
      })
    );
  }
  return pins;
}

export async function getEntityMapOptions(kennitala: string) {
  const { addresses } = await getEntityAddresses(kennitala);
  if (addresses.length === 0) return null;
  const pins = getMarkersForAddresses(addresses);
  const region = getRegion(addresses);
  return { annotations: pins, region: region };
}

export async function getNearbyMapOptions({
  hnitnum,
  radius,
  days,
}: {
  hnitnum: string;
  radius: string;
  days: string;
}) {
  const { address, addresses, plan } = await getNearbyCaseAddresses(
    parseInt(hnitnum, 10),
    {
      days: parseInt(days, 10),
      radius: parseInt(radius, 10),
    }
  );
  if (addresses.length === 0) return null;
  const pins = getMarkersForAddresses(addresses);
  const region = getRegion(addresses);
  pins.push(
    new mapkit.MarkerAnnotation(
      new mapkit.Coordinate(address.lat, address.lon),
      {
        title: address.label,
        color: "#2A1F6F",
      }
    )
  );
  const overlays = [];
  if (plan !== null) {
    const polygonOverlay = new mapkit.PolygonOverlay(
      (plan.polygon as any).map(([x, y]) => {
        return new mapkit.Coordinate(x, y);
      }),
      {
        style: new mapkit.Style({
          strokeOpacity: 0.2,
          lineWidth: 2,
          lineJoin: "round",
        }),
      }
    );
    overlays.push(polygonOverlay);
  }
  return { annotations: pins, region: region, overlays: overlays };
}
