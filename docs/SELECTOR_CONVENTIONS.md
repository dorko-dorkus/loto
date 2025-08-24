# SVG Selector Conventions

To ensure PID overlays work reliably, drawings should follow these rules when
adding selector attributes to SVG elements:

- **Use `id` for unique equipment.** Every taggable item should have a stable
  `id` value so it can be referenced as `#id`.
- **Group related items with classes.** Elements that represent a logical set
  may share a class name and be referenced as `.class`.
- **Nested groups are allowed.** `id` and `class` attributes may appear on any
  element, including elements inside transformed `<g>` groups.
- **ViewBox friendly.** All drawings should include a `viewBox` attribute on
  the root `<svg>` so coordinates can be transformed consistently.

Keeping to these conventions helps the overlay and validation tooling locate
the correct graphics within complex diagrams.
