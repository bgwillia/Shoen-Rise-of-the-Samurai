"""Smooth shoulder mounting weights in Blender world metres."""
import math


def strap_weights(point):
    # Front/back ends stay on the reinforcing bib. The continuous arch follows
    # its clavicle without inheriting noisy neck/upper-arm/twist transitions.
    along = max(0.0, min(1.0, (point.y + .153) / .298))
    shoulder = .8 * math.sin(math.pi * along) ** 2
    side = 'l' if point.x > 0 else 'r'
    return {'spine_05': 1.0 - shoulder, 'clavicle_' + side: shoulder}
