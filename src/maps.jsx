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

export async function buildEntityMap(map, kennitala) {
  return await api.getEntityAddresses(kennitala).then((response) => {
    const addresses = response.data.addresses;
    var north = 0.0,
      south = 0.0,
      west = 0.0,
      east = 0.0,
      pins = [];

    // Shift direction variables to the outermost parts of pins to create a boundary region
    for (var address of addresses) {
      const { lat, lon, label } = address;
      if (lat > north || north === 0.0) north = lat;
      if (lat < south || south === 0.0) south = lat;
      if (lon > west || west === 0.0) west = lon;
      if (lon < east || east === 0.0) east = lon;
      const coordinate = new mapkit.Coordinate(lat, lon);
      pins.push(new mapkit.MarkerAnnotation(coordinate, { title: label }));
    }

    // Set as coordinate region of map
    map.region = new mapkit.BoundingRegion(
      north,
      east,
      south,
      west
    ).toCoordinateRegion();
    map.showItems(pins);
  });
}
