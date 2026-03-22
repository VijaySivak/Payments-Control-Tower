"use client";
import type { ReactNode } from "react";

// Mercator projection utility
export function mercatorProject(lat: number, lng: number, width: number, height: number): [number, number] {
  const x = ((lng + 180) / 360) * width;
  const latRad = (lat * Math.PI) / 180;
  const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
  const y = height / 2 - (width * mercN) / (2 * Math.PI);
  return [x, y];
}

// World map SVG path data (simplified world outline for Mercator flat map)
// Using a compact representation of major land masses
export const WORLD_MAP_VIEWBOX = "0 0 1000 500";
export const WORLD_MAP_WIDTH = 1000;
export const WORLD_MAP_HEIGHT = 500;

interface WorldMapBaseProps {
  children?: ReactNode;
  className?: string;
  onBackgroundClick?: () => void;
}

export function WorldMapBase({ children, className, onBackgroundClick }: WorldMapBaseProps) {
  return (
    <svg
      viewBox={WORLD_MAP_VIEWBOX}
      width="100%"
      style={{ display: "block", background: "transparent" }}
      className={className}
      onClick={onBackgroundClick}
    >
      {/* Ocean background */}
      <rect width="1000" height="500" fill="#0c1629" rx="0" />

      {/* Grid lines */}
      {[-60, -30, 0, 30, 60].map((lat) => {
        const [, y] = mercatorProject(lat, 0, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT);
        return (
          <line
            key={`lat-${lat}`}
            x1={0}
            y1={y}
            x2={1000}
            y2={y}
            stroke="rgba(255,255,255,0.04)"
            strokeWidth={0.5}
          />
        );
      })}
      {[-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150].map((lng) => {
        const [x] = mercatorProject(0, lng, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT);
        return (
          <line
            key={`lng-${lng}`}
            x1={x}
            y1={0}
            x2={x}
            y2={500}
            stroke="rgba(255,255,255,0.04)"
            strokeWidth={0.5}
          />
        );
      })}

      {/* Simplified continent shapes */}
      <WorldContinents />

      {children}
    </svg>
  );
}

function WorldContinents() {
  return (
    <g opacity={0.85}>
      {/* North America */}
      <path
        d="M 95 82 L 150 70 L 195 72 L 215 85 L 222 100 L 215 120 L 200 140 L 185 165 L 175 200 L 160 225 L 155 245 L 145 260 L 135 255 L 120 240 L 110 220 L 100 195 L 90 170 L 82 145 L 78 120 L 80 100 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Greenland */}
      <path
        d="M 195 40 L 225 35 L 250 42 L 255 60 L 240 72 L 215 75 L 195 65 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Central America */}
      <path
        d="M 155 245 L 165 250 L 172 265 L 168 275 L 158 268 L 150 255 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* South America */}
      <path
        d="M 168 275 L 195 268 L 220 275 L 240 295 L 250 325 L 255 360 L 248 395 L 235 415 L 220 425 L 205 420 L 190 400 L 178 370 L 168 335 L 162 305 L 160 280 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Europe */}
      <path
        d="M 448 65 L 480 60 L 510 65 L 530 75 L 535 90 L 520 100 L 505 110 L 490 108 L 478 118 L 465 115 L 455 105 L 445 92 L 442 78 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Scandinavia */}
      <path
        d="M 475 42 L 495 38 L 510 48 L 515 62 L 505 68 L 490 65 L 478 55 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Africa */}
      <path
        d="M 458 140 L 490 135 L 518 138 L 535 155 L 540 180 L 538 210 L 530 240 L 520 270 L 510 300 L 500 325 L 490 345 L 478 355 L 465 348 L 452 325 L 442 295 L 435 265 L 432 235 L 435 205 L 438 175 L 445 155 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Russia / Asia (north) */}
      <path
        d="M 535 55 L 600 48 L 680 42 L 740 45 L 780 52 L 810 60 L 820 78 L 800 90 L 770 95 L 730 92 L 690 95 L 650 98 L 610 100 L 575 98 L 548 92 L 538 78 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Middle East / South Asia */}
      <path
        d="M 535 140 L 570 135 L 610 138 L 640 145 L 660 160 L 670 180 L 658 200 L 640 212 L 618 218 L 595 215 L 572 205 L 552 190 L 538 170 L 533 155 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* India */}
      <path
        d="M 622 185 L 645 182 L 665 195 L 670 218 L 660 240 L 645 258 L 630 262 L 618 248 L 612 225 L 612 205 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Southeast Asia */}
      <path
        d="M 700 185 L 730 182 L 758 188 L 770 205 L 762 222 L 742 232 L 720 228 L 705 215 L 698 200 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* China / East Asia */}
      <path
        d="M 670 95 L 720 92 L 760 95 L 790 105 L 808 120 L 810 140 L 800 158 L 778 168 L 750 172 L 720 170 L 695 162 L 675 148 L 665 130 L 662 112 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Japan */}
      <path
        d="M 820 108 L 832 105 L 840 115 L 835 128 L 822 130 L 814 120 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Indonesia / Philippines */}
      <path
        d="M 720 248 L 750 242 L 775 248 L 788 262 L 780 275 L 758 278 L 735 272 L 718 260 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* Australia */}
      <path
        d="M 745 305 L 795 298 L 840 302 L 870 315 L 882 335 L 880 360 L 865 378 L 840 388 L 812 390 L 782 382 L 758 362 L 742 338 L 738 318 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* New Zealand */}
      <path
        d="M 898 360 L 908 355 L 915 368 L 910 380 L 900 378 L 895 368 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
      {/* British Isles */}
      <path
        d="M 445 72 L 455 68 L 462 75 L 458 85 L 448 86 L 443 79 Z"
        fill="#162440"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth={0.8}
      />
    </g>
  );
}
