import { h } from "preact";
import { api } from "./api";

export let mapkit = window["mapkit"];

// Render map only when it is in the viewport
document.addEventListener("lazybeforeunveil", function (e) {
  let el = e.target;
  if (el.classList.contains("map")) {
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

export async function getEntityMapOptions(kennitala) {
  const addresses = await api.getEntityAddresses(kennitala).then((response) => {
    return response.data.addresses;
  });
  if (addresses.length === 0) return null;

  var north = addresses[0].lat,
    south = north,
    west = addresses[0].lon,
    east = west,
    pins = [];

  // Shift direction variables to the outermost parts of pins to create a boundary region
  for (var address of addresses) {
    const { lat, lon, label, status } = address;
    const labelColor = status ? status[2] : null;
    pins.push(
      new mapkit.MarkerAnnotation(new mapkit.Coordinate(lat, lon), {
        title: label,
        color:
          { green: "#48BB78", yellow: "#F6E05E", red: "#E53E3E" }[labelColor] ||
          "#718096",
      })
    );
    if (lat > north) north = lat;
    if (lat < south) south = lat;
    if (lon < west) west = lon;
    if (lon > east) east = lon;
  }

  if (addresses.length === 1) {
    return {
      annotations: pins,
      region: new mapkit.CoordinateRegion(
        new mapkit.Coordinate(north, west),
        new mapkit.CoordinateSpan(0.01, 0.01)
      ),
    };
  } else {
    const latDiff = Math.abs(north - south) * 0.1;
    const lonDiff = Math.abs(east - west) * 0.1;
    const region = new mapkit.BoundingRegion(
      north + latDiff,
      east + lonDiff,
      south - latDiff,
      west - lonDiff
    ).toCoordinateRegion();
    return {
      annotations: pins,
      region: region,
    };
  }
}
