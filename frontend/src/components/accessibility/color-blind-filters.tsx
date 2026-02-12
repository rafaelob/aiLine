/**
 * SVG filter definitions for color blindness simulation.
 * Hidden SVG element with feColorMatrix filters based on
 * Brettel, Viénot & Mollon (1997) color vision deficiency matrices.
 *
 * Applied via CSS: filter: url(#cb-protanopia)
 */

export function ColorBlindFilters() {
  return (
    <svg
      aria-hidden="true"
      className="absolute h-0 w-0 overflow-hidden"
      style={{ position: 'absolute', width: 0, height: 0 }}
    >
      <defs>
        {/* Protanopia — reduced red sensitivity (Brettel et al. 1997) */}
        <filter id="cb-protanopia">
          <feColorMatrix
            type="matrix"
            values="
              0.567, 0.433, 0.000, 0, 0
              0.558, 0.442, 0.000, 0, 0
              0.000, 0.242, 0.758, 0, 0
              0,     0,     0,     1, 0
            "
          />
        </filter>

        {/* Deuteranopia — reduced green sensitivity (Brettel et al. 1997) */}
        <filter id="cb-deuteranopia">
          <feColorMatrix
            type="matrix"
            values="
              0.625, 0.375, 0.000, 0, 0
              0.700, 0.300, 0.000, 0, 0
              0.000, 0.300, 0.700, 0, 0
              0,     0,     0,     1, 0
            "
          />
        </filter>

        {/* Tritanopia — reduced blue sensitivity (Brettel et al. 1997) */}
        <filter id="cb-tritanopia">
          <feColorMatrix
            type="matrix"
            values="
              0.950, 0.050, 0.000, 0, 0
              0.000, 0.433, 0.567, 0, 0
              0.000, 0.475, 0.525, 0, 0
              0,     0,     0,     1, 0
            "
          />
        </filter>
      </defs>
    </svg>
  )
}
